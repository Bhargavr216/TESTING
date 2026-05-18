import asyncio
import re
from datetime import datetime
from pathlib import Path

from playwright.async_api import async_playwright, Page

from src.profile import load_profile
from src.tracker import ApplicationTracker
from src.utils import (
    human_delay,
    log_step,
    log_success,
    log_error,
    log_warning,
    log_info,
)


class NaukriScanner:
    NAUKRI_BASE = "https://www.naukri.com"

    def __init__(self, profile_path: str = "config/profile.yaml"):
        self.profile = load_profile(profile_path)
        self.tracker = ApplicationTracker()
        self.scan_history_path = Path("data/scan-history.tsv")

    async def scan(
        self,
        keywords: list[str] | None = None,
        location: str = "",
        experience_min: int = 0,
        experience_max: int = 20,
        max_pages: int = 3,
        fresh_only: bool = True,
    ) -> list[dict]:
        if not keywords:
            keywords = self.profile.get("target_roles", {}).get("primary", [])

        if not location:
            cities = self.profile.get("location", {}).get("preferred_cities", [])
            location = cities[0] if cities else ""

        all_jobs: list[dict] = []
        seen_urls: set[str] = set()

        async with async_playwright() as p:
            try:
                browser = await p.chromium.launch(
                    channel="chrome",
                    headless=False,
                    args=["--no-sandbox", "--disable-dev-shm-usage", "--window-size=1366,768"],
                )
            except Exception:
                log_warning("System Chrome not found, falling back to Playwright Chromium (may be blocked)")
                browser = await p.chromium.launch(
                    headless=True,
                    args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
                )
            context = await browser.new_context(
                viewport={"width": 1366, "height": 768},
                locale="en-IN",
                timezone_id="Asia/Kolkata",
                permissions=["geolocation"],
                geolocation={"latitude": 12.9716, "longitude": 77.5946},
            )
            await context.grant_permissions(["geolocation"], origin="https://www.naukri.com")
            page = await context.new_page()

            for keyword in keywords:
                log_step(f"Scanning: '{keyword}' in '{location}'")
                jobs = await self._scan_keyword(
                    page, keyword, location, experience_min, experience_max, max_pages, fresh_only
                )
                for job in jobs:
                    url = job.get("url", "")
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        all_jobs.append(job)

                await human_delay(2, 5)

            await browser.close()

        all_jobs = self._deduplicate(all_jobs)
        self._save_scan_history(all_jobs)

        log_success(f"Scan complete: {len(all_jobs)} unique jobs found")
        return all_jobs

    async def _scan_keyword(
        self,
        page: Page,
        keyword: str,
        location: str,
        exp_min: int,
        exp_max: int,
        max_pages: int,
        fresh_only: bool,
    ) -> list[dict]:
        jobs = []

        search_slug = keyword.replace(" ", "-")
        loc_slug = location.replace(" ", "-") if location else ""
        base_url = f"{self.NAUKRI_BASE}/{search_slug}-jobs"
        if loc_slug:
            base_url += f"-in-{loc_slug}"

        for page_num in range(1, max_pages + 1):
            url = base_url if page_num == 1 else f"{base_url}-{page_num}"

            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=20000)
                await human_delay(2, 4)

                if exp_min > 0 or exp_max < 20:
                    await self._apply_experience_filter(page, exp_min, exp_max)

                if fresh_only:
                    await self._apply_fresh_filter(page)

                page_jobs = await self._extract_jobs(page)
                if not page_jobs:
                    break

                jobs.extend(page_jobs)
                log_info(f"  Page {page_num}: {len(page_jobs)} jobs")

            except Exception as e:
                log_warning(f"Error scanning page {page_num}: {e}")
                break

            await human_delay(1, 3)

        return jobs

    async def _apply_experience_filter(self, page: Page, exp_min: int, exp_max: int):
        try:
            filter_section = page.locator('[class*="filter"], [class*="filterBox"]').first
            if not await filter_section.is_visible(timeout=2000):
                return

            exp_links = await page.query_selector_all('a[href*="experience"]')
            for link in exp_links:
                text = (await link.inner_text()).strip().lower()
                if f"{exp_min}-{exp_max}" in text or f"{exp_min} to {exp_max}" in text:
                    await link.click()
                    await human_delay(1, 2)
                    break
        except Exception:
            pass

    async def _apply_fresh_filter(self, page: Page):
        try:
            fresh_links = await page.query_selector_all('a:has-text("Last 24 hours"), a:has-text("Last 3 days"), a:has-text("Last 7 days")')
            if fresh_links:
                await fresh_links[0].click()
                await human_delay(1, 2)
        except Exception:
            pass

    async def _extract_jobs(self, page: Page) -> list[dict]:
        jobs = []

        try:
            await page.wait_for_selector(
                'div.srp-jobtuple-wrapper, [data-job-id]',
                timeout=10000,
            )
        except Exception:
            return jobs

        cards = await page.query_selector_all('div.srp-jobtuple-wrapper')

        for card in cards:
            try:
                job = await self._parse_card(card)
                if job:
                    jobs.append(job)
            except Exception:
                continue

        return jobs

    async def _parse_card(self, card) -> dict | None:
        title_el = await card.query_selector('a.title')
        if not title_el:
            return None

        title = (await title_el.inner_text()).strip()
        job_url = await title_el.get_attribute("href")
        if job_url and not job_url.startswith("http"):
            job_url = self.NAUKRI_BASE + job_url

        company_el = await card.query_selector('a.comp-name')
        company = (await company_el.inner_text()).strip() if company_el else "Unknown"

        location_el = await card.query_selector('span.locWdth')
        location = (await location_el.inner_text()).strip() if location_el else ""

        salary_el = await card.query_selector('span.sal, .salary')
        salary = (await salary_el.inner_text()).strip() if salary_el else "Not Disclosed"

        experience_el = await card.query_selector('span.expwdth')
        experience = (await experience_el.inner_text()).strip() if experience_el else ""

        posted_el = await card.query_selector('.job-post-day')
        posted = (await posted_el.inner_text()).strip() if posted_el else ""

        tags = []
        tag_els = await card.query_selector_all('ul.tags-gt li.tag-li, ul.tags li')
        for tag_el in tag_els[:6]:
            tag_text = (await tag_el.inner_text()).strip()
            if tag_text:
                tags.append(tag_text)

        description_el = await card.query_selector('.job-desc')
        description = (await description_el.inner_text()).strip() if description_el else ""

        job_id = await card.get_attribute("data-job-id") or ""
        if not job_id and job_url:
            id_match = re.search(r"(\d{8,})", job_url)
            if id_match:
                job_id = id_match.group(1)

        return {
            "id": job_id,
            "title": title,
            "url": job_url or "",
            "company": company,
            "location": location,
            "salary": salary,
            "experience": experience,
            "tags": tags,
            "description": description,
            "posted": posted,
            "found_date": datetime.now().strftime("%Y-%m-%d"),
        }

    def _deduplicate(self, jobs: list[dict]) -> list[dict]:
        seen = set()
        unique = []

        history_urls = set()
        if self.scan_history_path.exists():
            for line in self.scan_history_path.read_text().split("\n"):
                parts = line.split("\t")
                if len(parts) >= 1 and parts[0].startswith("http"):
                    history_urls.add(parts[0])

        applied_ids = self.tracker.get_all_applied_ids()

        for job in jobs:
            url = job.get("url", "")
            job_id = job.get("id", "")

            if url in seen:
                continue
            if url in history_urls:
                continue
            if job_id and job_id in applied_ids:
                continue

            seen.add(url)
            unique.append(job)

        return unique

    def _save_scan_history(self, jobs: list[dict]):
        self.scan_history_path.parent.mkdir(parents=True, exist_ok=True)

        if not self.scan_history_path.exists():
            header = "url\tfirst_seen\tkeyword\ttitle\tcompany\tlocation\tstatus\n"
            self.scan_history_path.write_text(header)

        date = datetime.now().strftime("%Y-%m-%d")
        lines = []
        for job in jobs:
            url = job.get("url", "N/A")
            title = job.get("title", "N/A")
            company = job.get("company", "N/A")
            location = job.get("location", "N/A")
            lines.append(f"{url}\t{date}\tscan\t{title}\t{company}\t{location}\tadded\n")

        with open(self.scan_history_path, "a") as f:
            f.writelines(lines)
