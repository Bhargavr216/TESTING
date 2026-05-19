import asyncio
import os
import random
import re
from datetime import datetime
from pathlib import Path

from playwright.async_api import async_playwright, Page, Browser, BrowserContext, Frame

from src.profile import load_profile, resolve_storage_state_path
from src.tracker import ApplicationTracker
from src.utils import (
    human_delay,
    random_mouse_move,
    extract_salary_lakhs,
    log_step,
    log_success,
    log_error,
    log_warning,
    log_info,
)


class NaukriBot:
    NAUKRI_BASE = "https://www.naukri.com"
    HOME_URL = NAUKRI_BASE  # same entry point as naukri-auto-update apply_naukri_jobs
    LOGIN_URL = "https://www.naukri.com/nlogin/login"
    SEARCH_URL = "https://www.naukri.com/jobapi/v3/search"
    JOBS_URL = "https://www.naukri.com/mnjuser/homepage"

    def __init__(self, profile_path: str = "config/profile.yaml", headless: bool = False):
        self.profile = load_profile(profile_path)
        self.headless = headless
        self.browser: Browser | None = None
        self.context: BrowserContext | None = None
        self.page: Page | None = None
        self.tracker = ApplicationTracker()
        self.session_applied = 0
        self.session_date = datetime.now().strftime("%Y-%m-%d")
        self.max_per_day = self.profile.get("search_preferences", {}).get(
            "max_applications_per_day", 30
        )
        self.apply_delay = self.profile.get("search_preferences", {}).get(
            "apply_delay_seconds", 15
        )

    async def start(self):
        log_step("Launching browser...")
        self._playwright = await async_playwright().start()
        try:
            self.browser = await self._playwright.chromium.launch(
                channel="chrome",
                headless=self.headless,
                args=[
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--window-size=1366,768",
                ],
            )
        except Exception:
            log_warning("System Chrome not found, falling back to Playwright Chromium (may be blocked by Naukri)")
            self.browser = await self._playwright.chromium.launch(
                headless=self.headless,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                ],
            )
        auth_path = resolve_storage_state_path(self.profile)
        context_kwargs = {
            "viewport": {"width": 1366, "height": 768},
            "locale": "en-IN",
            "timezone_id": "Asia/Kolkata",
            "permissions": ["geolocation"],
            "geolocation": {"latitude": 12.9716, "longitude": 77.5946}, # Default to Bangalore
        }
        try:
            if auth_path.exists():
                context_kwargs["storage_state"] = str(auth_path)
                log_info(f"Using storage state: {auth_path}")
        except Exception as e:
            log_warning(f"Invalid storage state path: {e}")

        self.context = await self.browser.new_context(**context_kwargs)
        # Grant geolocation permission to avoid prompts
        await self.context.grant_permissions(["geolocation"], origin="https://www.naukri.com")
        self.page = await self.context.new_page()
        log_success("Browser launched")

    async def close(self) -> None:
        if self.context:
            try:
                await self.context.close()
            except Exception as e:
                log_warning(f"Error closing browser context: {e}")
        if hasattr(self, "_playwright") and self._playwright:
            try:
                await self._playwright.stop()
            except Exception as e:
                log_warning(f"Error stopping Playwright: {e}")

    async def update_profile(self) -> bool:
        """Update Naukri profile by uploading a local resume file from config/profile.yaml."""
        log_step("Updating Naukri profile resume from local file...")

        resume_path = str(self.profile.get("resume_path", "") or "").strip()
        if not resume_path:
            log_error("'resume_path' is not set in config/profile.yaml")
            return False

        candidate_path = Path(resume_path).expanduser()
        if not candidate_path.exists():
            candidate_path = (Path(__file__).resolve().parent.parent / resume_path).expanduser()

        if not candidate_path.exists():
            log_error(f"Local resume file not found: {resume_path}")
            return False

        try:
            await self.page.goto(f"{self.NAUKRI_BASE}/mnjuser/profile", wait_until="domcontentloaded")
            await human_delay(4, 6)

            log_info(f"Using resume file: {candidate_path}")

            file_inputs = await self.page.locator("input[type='file']").all()
            file_uploaded = False
            for input_el in file_inputs:
                try:
                    name_attr = (await input_el.get_attribute("name") or "").lower()
                    id_attr = (await input_el.get_attribute("id") or "").lower()
                    if "resume" in name_attr or "resume" in id_attr or await input_el.is_visible():
                        await input_el.set_input_files(str(candidate_path))
                        await human_delay(3, 5)
                        log_info("Resume file set via file input")
                        file_uploaded = True
                        break
                except Exception:
                    continue

            if not file_uploaded:
                trigger_selectors = [
                    "text=Update resume",
                    "text=Upload resume",
                    "text=Browse resume",
                    "[class*='resumeUpload']",
                    "[class*='resume-upload']",
                    "label[for*='resume']",
                    "input[value='Update resume']",
                ]
                for sel in trigger_selectors:
                    try:
                        el = self.page.locator(sel).first
                        if await el.is_visible(timeout=3000):
                            async with self.page.expect_file_chooser(timeout=5000) as fc_info:
                                await el.click()
                                fc = await fc_info.value
                                await fc.set_files(str(candidate_path))
                            await human_delay(3, 5)
                            log_info("Resume uploaded via file chooser")
                            break
                    except Exception:
                        continue

            for save_sel in [
                "button:has-text('Save')",
                "button:has-text('Upload')",
                "button:has-text('Confirm')",
                "button:has-text('Done')",
            ]:
                try:
                    btn = self.page.locator(save_sel).first
                    if await btn.is_visible(timeout=3000):
                        await btn.click()
                        await human_delay(2, 3)
                        log_success("Profile resume uploaded successfully")
                        return True
                except Exception:
                    continue

            log_warning("Could not find resume save button after upload. Resume file may be uploaded but not confirmed.")
            return True
        except Exception as e:
            log_error(f"Error updating profile resume: {e}")
            return False

    async def handle_early_access(self) -> bool:
        """Check for 'Early access roles' on homepage, click View All, and Share Interest."""
        log_step("Checking for Early Access roles...")
        max_retries = 3
        retry_delay = 2

        for attempt in range(max_retries):
            try:
                await self.page.goto(self.HOME_URL, wait_until="domcontentloaded")
                await human_delay(3, 5)

                # Look for Early access section using the ID from provided HTML
                early_section = self.page.locator('#s2j-ear-component, .s2j-preJobs-container').first
                if await early_section.is_visible(timeout=5000):
                    log_info("Early access section found")
                    break
                else:
                    if attempt < max_retries - 1:
                        log_info(f"Early access section not found (attempt {attempt + 1}/{max_retries}), retrying in {retry_delay}s...")
                        await human_delay(retry_delay, retry_delay + 1)
                        continue
                    else:
                        log_info("Early access section not found after all retries - skipping")
                        return False
            except Exception as e:
                if attempt < max_retries - 1:
                    log_warning(f"Error checking early access (attempt {attempt + 1}/{max_retries}): {e}, retrying...")
                    await human_delay(retry_delay, retry_delay + 1)
                    continue
                else:
                    log_error(f"Error handling early access after all retries: {e}")
                    return False

        try:
            # Use the specific class for View all
            view_all = early_section.locator('a.spc__view-all, a:has-text("View all")').first
            if await view_all.is_visible(timeout=3000):
                await view_all.click()
                await human_delay(3, 5)
                log_info("Clicked 'View all' for early access roles")

                async def open_early_access_page() -> bool:
                    try:
                        await self.page.goto(self.HOME_URL, wait_until="domcontentloaded")
                        await human_delay(3, 5)
                        early_section = self.page.locator('#s2j-ear-component, .s2j-preJobs-container').first
                        if await early_section.is_visible(timeout=5000):
                            next_view_all = early_section.locator('a.spc__view-all, a:has-text("View all")').first
                            if await next_view_all.is_visible(timeout=3000):
                                await next_view_all.click()
                                await human_delay(3, 5)
                                return True
                        return False
                    except Exception:
                        return False

                def share_selectors():
                    return (
                        '.tlc__tuple button.unshared, .tlc__tuple button:has-text("Share interest"), '
                        '.cust-job-tuple button.unshared, .cust-job-tuple button:has-text("Share interest")'
                    )

                clicked_any = False
                for retry in range(50):
                    share_buttons = await self.page.query_selector_all(share_selectors())
                    if not share_buttons:
                        break

                    clicked_this_round = False
                    for btn in share_buttons:
                        try:
                            if not await btn.is_visible():
                                continue
                            await btn.scroll_into_view_if_needed()
                            await human_delay(0.5, 1.0)
                            try:
                                await btn.click(force=True, timeout=5000)
                            except Exception:
                                await self.page.evaluate("(el) => el.click()", btn)

                            log_success("  Shared interest for one early access role")
                            clicked_any = True
                            clicked_this_round = True
                            await human_delay(1, 2)

                            try:
                                await self.page.wait_for_load_state("domcontentloaded", timeout=3000)
                            except Exception:
                                pass

                            try:
                                if not await self.page.locator('.tlc__tuple, .cust-job-tuple').first.is_visible(timeout=3000):
                                    log_info("Page moved after Share Interest click; returning to early access page")
                                    if not await open_early_access_page():
                                        return clicked_any
                            except Exception:
                                log_info("Page moved after Share Interest click; returning to early access page")
                                if not await open_early_access_page():
                                    return clicked_any
                            break
                        except Exception as e:
                            log_warning(f"  Error clicking Share Interest button: {e}")
                            continue

                    if not clicked_this_round:
                        break

                if clicked_any:
                    return True
                log_info("No available Share Interest buttons found on the page")
            else:
                log_warning("Could not find 'View all' link in Early Access section")
        except Exception as e:
            log_error(f"Error handling early access: {e}")
            return False

        return False

    async def get_application_statuses_from_profile(self) -> list[dict]:
        """Fetch application statuses from Naukri profile applied jobs section."""
        log_step("Fetching application statuses from Naukri profile...")
        try:
            await self.page.goto("https://www.naukri.com/mnjuser/applied-jobs", wait_until="domcontentloaded")
            await human_delay(3, 5)

            applications = []

            # Look for applied jobs table/list
            job_rows = await self.page.query_selector_all('.applied-job, .job-tuple, [data-job-id]')

            if not job_rows:
                # Try alternative selectors
                job_rows = await self.page.query_selector_all('.jobTuple, .job-tuple, .appliedJobsTuple')

            for row in job_rows[:50]:  # Limit to first 50 applications
                try:
                    app_data = {}

                    # Extract job title
                    title_el = await row.query_selector('.job-title, .title, h3, h2')
                    app_data['title'] = (await title_el.inner_text()).strip() if title_el else "Unknown"

                    # Extract company
                    company_el = await row.query_selector('.company-name, .company, .cmp-name')
                    app_data['company'] = (await company_el.inner_text()).strip() if company_el else "Unknown"

                    # Extract application date
                    date_el = await row.query_selector('.applied-date, .date, .applied-on')
                    app_data['applied_date'] = (await date_el.inner_text()).strip() if date_el else "Unknown"

                    # Extract status
                    status_el = await row.query_selector('.status, .application-status, .app-status')
                    status_text = (await status_el.inner_text()).strip() if status_el else "Unknown"

                    # Normalize status
                    status_lower = status_text.lower()
                    if 'shortlisted' in status_lower or 'selected' in status_lower:
                        app_data['status'] = 'shortlisted'
                    elif 'rejected' in status_lower:
                        app_data['status'] = 'rejected'
                    elif 'viewed' in status_lower or 'seen' in status_lower:
                        app_data['status'] = 'viewed'
                    elif 'applied' in status_lower:
                        app_data['status'] = 'applied'
                    else:
                        app_data['status'] = status_text

                    # Extract job URL if available
                    link_el = await row.query_selector('a')
                    if link_el:
                        href = await link_el.get_attribute('href')
                        if href and 'job' in href:
                            app_data['url'] = f"https://www.naukri.com{href}" if href.startswith('/') else href

                    applications.append(app_data)

                except Exception as e:
                    log_warning(f"Error extracting data from application row: {e}")
                    continue

            log_success(f"Fetched {len(applications)} applications from profile")
            return applications

        except Exception as e:
            log_error(f"Error fetching application statuses: {e}")
            return []
        if self.browser:
            await self.browser.close()
        if hasattr(self, "_playwright"):
            await self._playwright.stop()
        log_info("Browser closed")

    def _get_frames(self) -> list[Frame]:
        if not self.page:
            return []
        try:
            frames = list(self.page.frames)
            return frames if frames else [self.page.main_frame]
        except Exception:
            try:
                return [self.page.main_frame]
            except Exception:
                return []

    async def _detect_logged_in(self) -> bool:
        """True only when the page shows an authenticated session.

        Do not rely on URL alone: we always open ``/mnjuser/homepage``, so
        ``mnjuser`` / ``homepage`` appear even when Naukri shows a login wall.
        """
        url = (self.page.url or "").lower()
        if "nlogin/login" in url:
            return False

        try:
            u = self.page.locator("#usernameField").first
            p = self.page.locator('#passwordField, input[type="password"]').first
            if await u.is_visible() and await p.is_visible():
                return False
        except Exception:
            pass

        try:
            if await self.page.locator('a[href*="logout"]').count() > 0:
                return True
        except Exception:
            pass

        try:
            if await self.page.get_by_role("link", name=re.compile(r"logout", re.I)).count() > 0:
                return True
        except Exception:
            pass

        try:
            my = self.page.get_by_text("My Naukri", exact=True)
            if await my.count() > 0 and await my.first.is_visible():
                return True
        except Exception:
            pass

        # naukri-auto-update apply_naukri_jobs.open_recommended_jobs — logged-in home
        try:
            if await self.page.locator("section:has-text('Recommended Jobs')").count() > 0:
                return True
        except Exception:
            pass

        try:
            if await self.page.locator(
                'a[href*="/mnjuser/profile"], a[href*="/mnjuser/resume"]'
            ).count() > 0:
                return True
        except Exception:
            pass

        return False

    async def _credential_login_succeeded(self) -> bool:
        """After submitting credentials, Naukri may omit Logout in DOM until menus load; match reference project."""
        if await self._detect_logged_in():
            return True
        url = (self.page.url or "").lower()
        if "nlogin" in url or "/nlogin/" in url:
            return False
        if await self._is_login_page():
            return False
        if "mnjuser" in url or "mynaukri" in url:
            log_info("Session looks valid (jobseeker area, no login form)")
            return True
        return False

    async def _is_login_page(self) -> bool:
        """Same idea as naukri-auto-update apply_naukri_jobs.is_login_page (URL + login form)."""
        url = (self.page.url or "").lower()
        if "nlogin" in url:
            return True
        if "login" in url and "naukri.com" in url:
            return True
        try:
            u = self.page.locator("input#usernameField, input[name='username']").first
            p = self.page.locator("input#passwordField").first
            if await u.is_visible() and await p.is_visible():
                return True
        except Exception:
            pass
        return False

    async def _save_storage_state(self) -> None:
        if not self.context:
            return
        path = resolve_storage_state_path(self.profile)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            await self.context.storage_state(path=str(path))
            log_success(f"Saved session to {path}")
        except Exception as e:
            log_warning(f"Could not save session: {e}")

    async def login(self) -> bool:
        log_step("Logging into Naukri...")

        email = os.environ.get("NAUKRI_EMAIL") or self.profile.get(
            "naukri_credentials", {}
        ).get("email", "")
        password = os.environ.get("NAUKRI_PASSWORD") or self.profile.get(
            "naukri_credentials", {}
        ).get("password", "")

        if not email or not password:
            log_error("Naukri credentials not found. Set NAUKRI_EMAIL and NAUKRI_PASSWORD env vars or fill config/profile.yaml")
            return False

        # naukri-auto-update: open home first, then decide if saved session is still valid
        try:
            await self.page.goto(self.HOME_URL, wait_until="domcontentloaded")
            await human_delay(2, 3)
            try:
                await self.page.wait_for_load_state("networkidle", timeout=15000)
            except Exception:
                pass

            if not await self._is_login_page():
                if await self._detect_logged_in():
                    log_success("Already logged in (session detected)")
                    return True
            else:
                log_info("Saved session missing or expired — signing in with credentials")
        except Exception as e:
            log_warning(f"Home page / session check: {e}")

        try:
            await self.page.goto(self.LOGIN_URL, wait_until="domcontentloaded")
            await human_delay(1, 2)

            email_input = self.page.locator("#usernameField").first
            await email_input.wait_for(state="visible", timeout=30000)
            await email_input.fill(email)

            password_input = self.page.locator('#passwordField, input[type="password"]').first
            await password_input.wait_for(state="visible", timeout=10000)
            await password_input.fill(password)

            # naukri-auto-update uses button[type='submit'] (not .blue-btn)
            submit = self.page.locator("button[type='submit']").first
            await submit.wait_for(state="visible", timeout=10000)
            await submit.click()

            await self.page.wait_for_timeout(7000)
            try:
                await self.page.wait_for_load_state("networkidle", timeout=15000)
            except Exception:
                pass
            await human_delay(1, 2)

            if await self._credential_login_succeeded():
                log_success("Login successful!")
                await self._save_storage_state()
                return True

            await self.page.goto(self.HOME_URL, wait_until="domcontentloaded")
            await human_delay(2, 3)
            try:
                await self.page.wait_for_load_state("networkidle", timeout=15000)
            except Exception:
                pass
            if await self._credential_login_succeeded():
                log_success("Login successful!")
                await self._save_storage_state()
                return True

            await self.page.goto(self.JOBS_URL, wait_until="domcontentloaded")
            await human_delay(2, 3)
            try:
                await self.page.wait_for_load_state("networkidle", timeout=15000)
            except Exception:
                pass
            if await self._credential_login_succeeded():
                log_success("Login successful!")
                await self._save_storage_state()
                return True

            log_error("Login may have failed. Current URL: " + self.page.url)
            return False

        except Exception as e:
            log_error(f"Login error: {e}")
            return False

    async def search_jobs(
        self,
        keyword: str,
        location: str = "",
        experience: str = "",
        fresh_only: bool = False,
        sort_by_date: bool = True,
        max_pages: int = 1,
        max_results: int = 0,
    ) -> list[dict]:
        max_pages = max(1, int(max_pages or 1))
        max_pages = min(max_pages, 25)
        max_results = max(0, int(max_results or 0))

        log_step(
            f"Searching jobs: keyword='{keyword}', location='{location}', pages={max_pages}"
        )

        search_slug = re.sub(r"[^a-z0-9]+", "-", keyword.lower()).strip("-")
        search_url = f"{self.NAUKRI_BASE}/{search_slug}-jobs"
        if location:
            loc_slug = re.sub(r"[^a-z0-9]+", "-", location.lower()).strip("-")
            search_url += f"-in-{loc_slug}"

        await self.page.goto(search_url, wait_until="domcontentloaded")
        await human_delay(2, 4)

        if sort_by_date:
            try:
                # Use specific selectors from user provided HTML
                sort_btn = self.page.locator('#filter-sort, button.styles_sort-droop-label__TxC3K').first
                if await sort_btn.is_visible(timeout=5000):
                    await sort_btn.click()
                    await human_delay(1, 2)
                    
                    # Select "Date" option using specific data-id or title
                    date_option = self.page.locator('li[title="Date"], a[data-id="filter-sort-f"]').first
                    if await date_option.is_visible(timeout=3000):
                        await date_option.click()
                        await human_delay(2, 4)
                        log_info("Sorted results by Date (Newest first)")
                    else:
                        log_warning("Could not find 'Date' option in sort menu")
                else:
                    # Fallback to general dropdown if specific one not found
                    sort_dropdown = self.page.locator('.sort-container, .sort-drop-down, #sort-display, .sort-by-container').first
                    if await sort_dropdown.is_visible(timeout=2000):
                        await sort_dropdown.click()
                        await human_delay(1, 2)
                        date_option = self.page.locator('li:has-text("Date"), span:has-text("Date"), a:has-text("Date")').first
                        if await date_option.is_visible(timeout=2000):
                            await date_option.click()
                            await human_delay(2, 4)
                            log_info("Sorted results by Date (Newest first) via fallback")
            except Exception as e:
                log_warning(f"Could not sort by date: {e}")

        if fresh_only:
            try:
                # Try to click on "Last 3 days" or similar filter if visible
                # Naukri often has these filters in the sidebar
                fresh_links = await self.page.query_selector_all('a:has-text("Last 3 days"), a:has-text("Last 7 days")')
                if fresh_links:
                    await fresh_links[0].click()
                    await human_delay(1, 2)
                    log_info("Applied freshness filter (Last 3/7 days)")
            except Exception:
                pass

        if experience:
            try:
                exp_selectors = [
                    'select[name*="exp"], .exp-dropdown select',
                    'select[name="experience"], #experience'
                ]
                for sel in exp_selectors:
                    try:
                        exp_select = self.page.locator(sel).first
                        await exp_select.select_option(experience)
                        log_info(f"Applied experience filter: {experience}")
                        break
                    except Exception:
                        continue
            except Exception:
                log_warning(f"Could not apply experience filter: {experience}")

        jobs: list[dict] = []
        seen_urls: set[str] = set()

        async def _goto_next_page() -> bool:
            next_selectors = [
                'a[title="Next"]',
                'a[aria-label="Next"]',
                'a:has-text("Next")',
                'a.pagination-next',
                'a[class*="pagination"]:has-text("Next")',
            ]
            for selector in next_selectors:
                try:
                    next_btn = self.page.locator(selector).first
                    if not await next_btn.is_visible(timeout=1500):
                        continue

                    try:
                        aria_disabled = await next_btn.get_attribute("aria-disabled")
                        if aria_disabled and aria_disabled.lower() == "true":
                            return False
                    except Exception:
                        pass

                    old_url = self.page.url
                    await next_btn.click()
                    try:
                        await self.page.wait_for_load_state("domcontentloaded", timeout=15000)
                    except Exception:
                        pass
                    await human_delay(2, 3)

                    # Some paginations update content without a URL change; if click didn't throw,
                    # treat it as a best-effort navigation.
                    _ = old_url
                    return True
                except Exception:
                    continue
            return False

        for page_num in range(1, max_pages + 1):
            new_jobs = await self._extract_job_listings(seen_urls=seen_urls, max_results=max_results)
            jobs.extend(new_jobs)
            if page_num > 1 and not new_jobs:
                break

            if max_results and len(seen_urls) >= max_results:
                break
            if page_num >= max_pages:
                break

            moved = await _goto_next_page()
            if not moved:
                break

        log_success(f"Found {len(jobs)} unique jobs for '{keyword}'")
        return jobs

    async def _extract_job_listings(self, seen_urls: set[str] | None = None, max_results: int = 0) -> list[dict]:
        jobs: list[dict] = []
        max_results = max(0, int(max_results or 0))
        try:
            await self.page.wait_for_selector(
                'div.srp-jobtuple-wrapper, [data-job-id]',
                timeout=15000,
            )
        except Exception:
            log_warning("No job listings found on page")
            return jobs

        # Some result pages load cards lazily while scrolling.
        try:
            last_count = -1
            for _ in range(8):
                cards_now = await self.page.query_selector_all("div.srp-jobtuple-wrapper")
                if len(cards_now) == last_count:
                    break
                last_count = len(cards_now)
                await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await human_delay(1, 2)
        except Exception:
            pass

        job_cards = await self.page.query_selector_all(
            'div.srp-jobtuple-wrapper'
        )

        for card in job_cards:
            try:
                job = await self._parse_job_card(card)
                if job:
                    url = str(job.get("url") or "")
                    if seen_urls is not None and url:
                        if url in seen_urls:
                            continue
                        seen_urls.add(url)
                        if max_results and len(seen_urls) >= max_results:
                            jobs.append(job)
                            return jobs
                    jobs.append(job)
            except Exception as e:
                log_warning(f"Error parsing job card: {e}")
                continue

        return jobs

    async def _parse_job_card(self, card) -> dict | None:
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
        salary_text = (await salary_el.inner_text()).strip() if salary_el else "Not Disclosed"

        experience_el = await card.query_selector('span.expwdth')
        experience = (await experience_el.inner_text()).strip() if experience_el else ""

        tags = []
        tag_els = await card.query_selector_all('ul.tags-gt li.tag-li, ul.tags li')
        for tag_el in tag_els[:6]:
            tag_text = (await tag_el.inner_text()).strip()
            if tag_text:
                tags.append(tag_text)

        description_el = await card.query_selector('.job-desc')
        description = (await description_el.inner_text()).strip() if description_el else ""

        posted_el = await card.query_selector('.job-post-day')
        posted = (await posted_el.inner_text()).strip() if posted_el else ""

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
            "salary": salary_text,
            "experience": experience,
            "tags": tags,
            "description": description,
            "posted": posted,
            "found_date": datetime.now().strftime("%Y-%m-%d"),
        }

    def _maybe_save_apply_report(self, job: dict, result: dict) -> None:
        """Write markdown under reports/applied/ for each attempt (tracker stays in data/)."""
        status = result.get("status", "")
        if status in ("already_applied", "daily_limit"):
            return
        try:
            self._save_apply_report(job, result)
        except Exception as e:
            log_warning(f"Could not write apply report: {e}")

    def _save_apply_report(self, job: dict, result: dict) -> None:
        reports_dir = Path("reports") / "applied"
        reports_dir.mkdir(parents=True, exist_ok=True)
        company_slug = re.sub(r"[^a-z0-9]+", "-", (job.get("company") or "unknown").lower()).strip("-") or "unknown"
        status = result.get("status", "unknown")
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        fname = f"{ts}-{company_slug}-{status}.md"
        path = reports_dir / fname

        err = result.get("error") or ""
        match = job.get("match_details", {})
        
        lines = [
            f"# Application — {job.get('company', 'Unknown')}: {job.get('title', 'Unknown')}",
            "",
            f"**When:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Status:** {status}",
            f"**Job URL:** {job.get('url', 'N/A')}",
            "",
            "## Job Match Analysis",
            f"- **Match Score:** {match.get('match_score', 'N/A')}",
            f"- **Early Applicant:** {match.get('early_applicant', 'No')}",
            f"- **Location Match:** {match.get('location_match', 'N/A')}",
            f"- **Exp Match:** {match.get('exp_match', 'N/A')}",
            f"- **Keyskills:** {', '.join(match.get('keyskills', [])) or 'N/A'}",
            "",
        ]
        if err:
            lines.extend([f"**Details:** {err}", ""])
        lines.extend(
            [
                "## Job snapshot",
                "",
                f"| Field | Value |",
                f"|-------|-------|",
                f"| Location | {job.get('location', 'N/A')} |",
                f"| Salary | {job.get('salary', 'N/A')} |",
                f"| Experience | {job.get('experience', 'N/A')} |",
                f"| Job ID | {job.get('id', 'N/A')} |",
                "",
                "*Generated by naukri-automation*",
            ]
        )
        path.write_text("\n".join(lines), encoding="utf-8")
        log_success(f"Apply report saved: {path}")

    async def _extract_match_details(self) -> dict:
        """Extract job match score and other details from the job page."""
        details = {
            "match_score": "N/A",
            "early_applicant": "No",
            "keyskills": [],
            "location_match": "N/A",
            "exp_match": "N/A"
        }
        try:
            # Match score (often in a circular progress or text like "90% Match")
            score_el = self.page.locator('.match-score, [class*="matchScore"], .job-match-score').first
            if await score_el.is_visible(timeout=2000):
                details["match_score"] = (await score_el.inner_text()).strip()

            # Early applicant status
            early_el = self.page.locator('text="Early Applicant", .early-applicant, [class*="earlyApplicant"]').first
            if await early_el.is_visible(timeout=1000):
                details["early_applicant"] = "Yes"

            # Keyskills from the page
            keyskill_els = await self.page.query_selector_all('.key-skill, .skill-tag, [class*="keySkill"]')
            for el in keyskill_els:
                txt = (await el.inner_text()).strip()
                if txt:
                    details["keyskills"].append(txt)

            # Location and Exp match indicators
            loc_match = self.page.locator('.location-match, [class*="locationMatch"]').first
            if await loc_match.is_visible(timeout=1000):
                details["location_match"] = "Matched"
                
            exp_match = self.page.locator('.exp-match, [class*="expMatch"]').first
            if await exp_match.is_visible(timeout=1000):
                details["exp_match"] = "Matched"

        except Exception as e:
            log_warning(f"  Error extracting match details: {e}")
        
        return details

    async def apply_to_job(self, job: dict, skip_external: bool = True, max_retries: int = 2) -> dict:
        result = {
            "job_id": job.get("id", ""),
            "title": job.get("title", ""),
            "company": job.get("company", ""),
            "url": job.get("url", ""),
            "status": "pending",
            "error": None,
            "timestamp": datetime.now().isoformat(),
        }

        if not job.get("url"):
            result["status"] = "skipped"
            result["error"] = "No URL"
            self._maybe_save_apply_report(job, result)
            return result

        already_applied = self.tracker.is_applied(job.get("id", ""))
        if already_applied:
            result["status"] = "already_applied"
            result["error"] = "Already applied to this job"
            log_info(f"Already applied to {job['company']} - {job['title']}")
            return result

        if self.session_applied >= self.max_per_day:
            result["status"] = "daily_limit"
            result["error"] = f"Daily limit of {self.max_per_day} reached"
            log_warning(f"Daily application limit reached ({self.max_per_day})")
            return result

        log_step(f"Applying to: {job['company']} - {job['title']}")

        try:
            await self.page.goto(job["url"], wait_until="domcontentloaded")
            await human_delay(2, 4)

            # Gather Job match details first
            match_details = await self._extract_match_details()
            job["match_details"] = match_details
            
            # STRICT FILTERING: Check job title against primary target roles
            job_title_lower = job.get("title", "").lower()
            target_roles_primary = [r.lower() for r in self.profile.get("target_roles", {}).get("primary", [])]
            title_matches_role = any(role in job_title_lower for role in target_roles_primary)
            
            if not title_matches_role:
                result["status"] = "skipped"
                result["error"] = f"Job title '{job['title']}' doesn't match target roles: {', '.join(target_roles_primary)}"
                log_info(f"Skipping {job['title']} - title doesn't match target roles")
                self._maybe_save_apply_report(job, result)
                return result
            
            # Filter by keywords_positive and keywords_negative
            keywords_positive = [k.lower() for k in self.profile.get("target_roles", {}).get("keywords_positive", [])]
            keywords_negative = [k.lower() for k in self.profile.get("target_roles", {}).get("keywords_negative", [])]
            
            job_keyskills_lower = set([k.lower() for k in match_details.get("keyskills", [])])
            full_job_text = (job_title_lower + " " + " ".join(job_keyskills_lower)).lower()
            
            # Check for negative keywords
            if keywords_negative:
                for neg_kw in keywords_negative:
                    if neg_kw in full_job_text:
                        result["status"] = "skipped"
                        result["error"] = f"Job contains negative keyword: '{neg_kw}'"
                        log_info(f"Skipping {job['title']} - contains negative keyword '{neg_kw}'")
                        self._maybe_save_apply_report(job, result)
                        return result
            
            # Check for at least some positive keywords
            if keywords_positive:
                has_positive = any(pos_kw in full_job_text for pos_kw in keywords_positive)
                if not has_positive:
                    result["status"] = "skipped"
                    result["error"] = f"Job doesn't contain required positive keywords. Required: {', '.join(keywords_positive[:3])}"
                    log_info(f"Skipping {job['title']} - missing positive keywords")
                    self._maybe_save_apply_report(job, result)
                    return result
            
            # Check for external apply button first
            company_site_btn = self.page.locator(
                '#company-site-button, button.company-site-button'
            ).first
            try:
                if await company_site_btn.is_visible(timeout=3000):
                    if skip_external:
                        result["status"] = "external_apply"
                        result["error"] = "Apply on company site - skipping"
                        log_info(f"Skipping {job['title']} (external apply)")
                        self._maybe_save_apply_report(job, result)
                        return result
                    else:
                        result["status"] = "external_apply"
                        result["error"] = "Apply on company site - proceeding anyway"
                        log_info(f"Proceeding with external apply for {job['title']} (target applications specified)")
            except Exception:
                pass

            # Locate quick apply button
            apply_btn_selectors = [
                '#apply-button',
                'button.apply-button',
                'button:has-text("Apply")',
                'button:has-text("Apply Now")',
                'button:has-text("Register to Apply")',
                'button:has-text("Register and Apply")',
                'button:has-text("Register")',
                '#apply-btn',
                '.apply-btn',
            ]

            apply_btn = None
            for selector in apply_btn_selectors:
                try:
                    btn = self.page.locator(selector).first
                    if await btn.is_visible(timeout=2000):
                        apply_btn = btn
                        break
                except Exception:
                    continue

            if not apply_btn:
                result["status"] = "no_apply_button"
                result["error"] = "Could not find Apply button"
                log_warning(f"No Apply button found for {job['title']}")
                self._maybe_save_apply_report(job, result)
                return result

            await random_mouse_move(self.page)
            await apply_btn.click()
            await human_delay(4, 6)

            # Retry form handling if it fails
            form_success = False
            was_chat = False
            for attempt in range(max_retries):
                try:
                    form_success, was_chat = await self._handle_application_form(job)
                    if form_success:
                        break
                    elif attempt < max_retries - 1:
                        log_warning(f"Form handling failed (attempt {attempt + 1}/{max_retries}), retrying...")
                        await self.page.goto(job["url"], wait_until="domcontentloaded")
                        await human_delay(2, 3)
                        await apply_btn.click()
                        await human_delay(4, 6)
                except Exception as e:
                    if attempt < max_retries - 1:
                        log_warning(f"Form error on attempt {attempt + 1}/{max_retries}: {e}, retrying...")
                        await human_delay(2, 3)
                    else:
                        raise

            if not form_success:
                result["status"] = "form_failed"
                result["error"] = "Could not complete application form after retries"
                log_error(f"Application form failed for {job['title']} after {max_retries} attempts")
                self._maybe_save_apply_report(job, result)
                return result

            try:
                await self.page.wait_for_load_state("domcontentloaded", timeout=10000)
            except Exception:
                pass
            await human_delay(1, 2)

            if was_chat:
                # For chat applications, consider applied without checking success
                result["status"] = "applied"
                self.session_applied += 1
                self.tracker.record_application(job, "applied")
                log_success(f"Applied to {job['company']} - {job['title']} ({self.session_applied}/{self.max_per_day})")
            else:
                success = await self._check_application_success()
                if success:
                    result["status"] = "applied"
                    self.session_applied += 1
                    self.tracker.record_application(job, "applied")
                    log_success(f"Applied to {job['company']} - {job['title']} ({self.session_applied}/{self.max_per_day})")
                else:
                    result["status"] = "failed"
                    result["error"] = "Application form completed but success not confirmed"
                    self.tracker.record_application(job, "failed")
                    log_error(f"Could not confirm application success for {job['title']}")

        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
            self.tracker.record_application(job, "error")
            log_error(f"Error applying to {job['title']}: {e}")

        self._maybe_save_apply_report(job, result)

        delay = self.apply_delay + random.uniform(-3, 5)
        delay = max(8, delay)
        log_info(f"Waiting {delay:.0f}s before next application...")
        await human_delay(delay, delay + 3)

        return result

    async def _wait_for_screening_chat(self, timeout: int = 20) -> bool:
        selectors = [
            '._chatBotContainer',
            '.chatbot_Drawer',
            'div[class*="chatbot_MessageContainer"]',
            'div.textArea[contenteditable]',
            'input.ssrc__radio',
            'input[type="checkbox"]',
            '.singleselect-radiobutton-container',
            'div.chatbot_DrawerContentWrapper',
        ]
        for selector in selectors:
            try:
                await self.page.wait_for_selector(
                    selector,
                    state="visible",
                    timeout=timeout * 1000,
                )
                log_info(f"Screening chat element found: {selector}")
                return True
            except Exception:
                continue

        chat_check = await self.page.evaluate("""() => {
            const checks = [
                '._chatBotContainer',
                '.chatbot_Drawer',
                'div[class*="chatbot_MessageContainer"]',
                'div.textArea[contenteditable]',
                'input.ssrc__radio',
                'input[type="checkbox"]',
                '.singleselect-radiobutton-container'
            ];
            for (const sel of checks) {
                try {
                    if (document.querySelector(sel)) return sel;
                } catch(e) {}
            }
            return null;
        }""")
        if chat_check:
            log_info(f"Screening chat found via JS evaluate: {chat_check}")
            return True

        return False

    async def _get_current_chat_question(self) -> str:
        for wait_attempt in range(3):
            result = await self.page.evaluate("""() => {
                const listItems = document.querySelectorAll('li.chatbot_ListItem');
                let lastBotQuestion = '';
                for (let i = listItems.length - 1; i >= 0; i--) {
                    const li = listItems[i];
                    if (li.classList.contains('botItem')) {
                        const msgDiv = li.querySelector('div.botMsg');
                        if (msgDiv) {
                            const text = msgDiv.innerText.trim();
                            if (text.length > 5 && !text.includes('Kindly answer all')) {
                                lastBotQuestion = text;
                                break;
                            }
                        }
                    }
                }

                const hasTextInput = (() => {
                    const input = document.querySelector('div.textArea[contenteditable="true"], div.textArea[contenteditable=""]');
                    if (!input) return false;
                    const rect = input.getBoundingClientRect();
                    return rect.width > 0 && rect.height > 0;
                })();

                const hasRadio = document.querySelectorAll('input.ssrc__radio').length > 0;
                const hasCheckbox = Array.from(document.querySelectorAll('input[type="checkbox"]')).some(cb => {
                    const rect = cb.getBoundingClientRect();
                    return rect.width > 0 && rect.height > 0;
                });

                if (lastBotQuestion && (hasTextInput || hasRadio || hasCheckbox)) {
                    return lastBotQuestion;
                }
                return '';
            }""")
            if result:
                return result
            await human_delay(1, 2)
        return ''

    async def _has_active_text_input(self) -> bool:
        return await self.page.evaluate("""() => {
            const input = document.querySelector('div.textArea[contenteditable="true"], div.textArea[contenteditable=""]');
            if (!input) return false;
            const rect = input.getBoundingClientRect();
            return rect.width > 0 && rect.height > 0;
        }""")

    async def _has_active_radio_options(self) -> bool:
        return await self.page.evaluate("""() => {
            const radios = document.querySelectorAll('input.ssrc__radio');
            return radios.length > 0;
        }""")

    async def _has_active_checkbox_options(self) -> bool:
        return await self.page.evaluate("""() => {
            const checkboxes = document.querySelectorAll('input[type="checkbox"]');
            return Array.from(checkboxes).some(cb => {
                const rect = cb.getBoundingClientRect();
                return rect.width > 0 && rect.height > 0;
            });
        }""")

    async def _get_radio_options(self) -> list[dict]:
        return await self.page.evaluate("""() => {
            const radios = document.querySelectorAll('input.ssrc__radio');
            return Array.from(radios).map(r => {
                const container = r.closest('.ssrc__radio-btn-container');
                const label = container ? container.innerText.trim() : '';
                return {
                    id: r.id || '',
                    name: r.name || '',
                    value: r.value || '',
                    label: label
                };
            });
        }""")

    async def _get_checkbox_options(self) -> list[dict]:
        return await self.page.evaluate("""() => {
            const checkboxes = Array.from(document.querySelectorAll('input[type="checkbox"]'));
            return checkboxes
                .filter(cb => {
                    const rect = cb.getBoundingClientRect();
                    return rect.width > 0 && rect.height > 0;
                })
                .map(cb => {
                    const id = cb.id || '';
                    let label = '';
                    if (id) {
                        const direct = document.querySelector(`label[for="${id}"]`);
                        if (direct) label = (direct.innerText || '').trim();
                    }
                    if (!label) {
                        const container = cb.closest('label, li, div');
                        if (container) label = (container.innerText || '').trim();
                    }
                    return {
                        id: id,
                        name: cb.name || '',
                        value: cb.value || '',
                        label: label,
                    };
                });
        }""")

    async def _click_chat_save_button(self) -> bool:
        save_selectors = [
            'div.sendMsgbtn_container',
            'div.sendMsg',
            'div.send',
            '.chatbot_SendMessageContainer:not(.d-none) div.sendMsg',
            '.chatbot_SendMessageContainer div.send',
        ]
        for sel in save_selectors:
            try:
                btn = await self.page.query_selector(sel)
                if btn:
                    is_visible = await btn.is_visible(timeout=1000)
                    if is_visible:
                        btn_text = (await btn.inner_text()).strip()
                        if btn_text.lower() in ('save', 'submit', 'send', 'apply', 'continue', 'next'):
                            await btn.click()
                            log_info(f"Clicked chat Save button via '{sel}' (text='{btn_text}')")
                            return True
            except Exception:
                continue

        try:
            save_btn = self.page.locator('div.sendMsgbtn_container, div.sendMsg').first
            if await save_btn.is_visible(timeout=2000):
                await save_btn.click()
                log_info("Clicked chat Save button via locator")
                return True
        except Exception:
            pass

        log_warning("No Save/Submit button found after chat answer")
        return False

    async def _answer_chat_text_question(self, question_text: str, screening: dict, compensation: dict) -> bool:
        question_lower = question_text.lower()
        
        # Get defaults from profile or use fallback constants
        chat_defaults = self.profile.get("chatbot_defaults", {})
        def_exp = str(chat_defaults.get("experience", "4"))
        def_notice = str(chat_defaults.get("notice_period", "30"))
        def_salary = str(chat_defaults.get("expected_salary", "25"))

        answer = ""

        # Experience / Idea questions
        if any(kw in question_lower for kw in ["experience", "exp", "idea"]):
            answer = str(screening.get("total_experience_years", def_exp))
        # Notice period / Joining questions
        elif any(kw in question_lower for kw in ["notice", "joining", "join"]):
            answer = def_notice
        # Salary questions
        elif any(kw in question_lower for kw in ["salary", "ctc", "lpa"]):
            answer = str(compensation.get("expected_ctc", def_salary))
        # Worked in company questions
        elif any(kw in question_lower for kw in ["worked in", "previously worked", "worked at", "prior experience"]):
            answer = "No"
        
        # If we couldn't resolve a specific answer, use "Yes" as requested
        if not answer:
            # Check if a number is strictly required
            if any(kw in question_lower for kw in ["how many", "years", "months"]):
                answer = "0"
            else:
                answer = "Yes"

        try:
            input_box = self.page.locator('div.textArea[contenteditable="true"], div.textArea[contenteditable=""], textarea').first
            if await input_box.is_visible(timeout=3000):
                await input_box.click()
                await human_delay(0.3, 0.6)
                await input_box.type(answer, delay=random.randint(40, 80))
                await human_delay(0.5, 1.0)
                
                save_clicked = await self._click_chat_save_button()
                if not save_clicked:
                    await self.page.keyboard.press('Enter')
                    log_info("Text answer: pressed Enter (no Save button)")

                await human_delay(2, 3)
                log_info(f"Chat answered (text): '{question_text[:50]}' -> '{answer}'")
                return True
            else:
                log_warning(f"No visible text input for chat question: '{question_text[:80]}'")
                return False
        except Exception as e:
            log_warning(f"Failed to answer chat text question: {e}")
            return False

    async def _answer_chat_radio_question(self, question_text: str, radio_options: list[dict], screening: dict) -> bool:
        if not radio_options:
            return False
            
        question_lower = question_text.lower()
        target_idx = -1
        
        chat_defaults = self.profile.get("chatbot_defaults", {})
        def_exp = str(chat_defaults.get("experience", "4"))
        def_notice = str(chat_defaults.get("notice_period", "30"))

        # Try to match based on user preferences
        if any(kw in question_lower for kw in ["experience", "exp", "idea"]):
            for i, opt in enumerate(radio_options):
                lbl = opt.get('label', '').lower()
                if def_exp in lbl:
                    target_idx = i
                    break
        elif any(kw in question_lower for kw in ["notice", "joining", "join"]):
            for i, opt in enumerate(radio_options):
                lbl = opt.get('label', '').lower()
                if def_notice in lbl or "immediate" in lbl or "1 month" in lbl:
                    target_idx = i
                    break
        elif any(kw in [o.get('label','').lower() for o in radio_options] for kw in ['yes', 'yeah', 'yep']):
            # Default to "Yes" for yes/no questions
            for i, opt in enumerate(radio_options):
                if any(kw in opt.get('label','').lower() for kw in ['yes', 'yeah', 'yep']):
                    target_idx = i
                    break
        
        # If no match found, pick randomly as requested
        if target_idx == -1:
            target_idx = random.randint(0, len(radio_options) - 1)
            log_info(f"  No specific match for radio Q, picked random option: {radio_options[target_idx].get('label')}")

        best_match = radio_options[target_idx]
        target_value = best_match.get('value', '')
        target_id = best_match.get('id', '')

        try:
            await self.page.evaluate("""([targetId, targetValue]) => {
                const containers = document.querySelectorAll('.ssrc__radio-btn-container');
                for (const c of containers) {
                    const radio = c.querySelector('input.ssrc__radio');
                    if (radio && (radio.id === targetId || radio.value === targetValue)) {
                        c.click();
                        radio.click();
                        radio.checked = true;
                        radio.dispatchEvent(new Event('change', { bubbles: true }));
                        return;
                    }
                }
                if (targetId) {
                    const radio = document.getElementById(targetId);
                    if (radio) {
                        radio.checked = true;
                        radio.click();
                        radio.dispatchEvent(new Event('change', { bubbles: true }));
                    }
                }
            }""", [target_id, target_value])

            await human_delay(0.5, 1.0)
            await self._click_chat_save_button()

            await human_delay(2, 3)
            log_info(f"Chat answered (radio): '{question_text[:50]}' -> '{target_value[:30]}'")
            return True

        except Exception as e:
            log_warning(f"Failed to answer chat radio question: {e}")
            return False

    async def _answer_chat_checkbox_question(self, question_text: str, checkbox_options: list[dict], screening: dict) -> bool:
        if not checkbox_options:
            return False
            
        question_lower = question_text.lower()
        is_known = any(kw in question_lower for kw in ["experience", "notice", "joining", "salary", "ctc", "skill", "location", "relocate"])

        # User requested to "add all" for checkboxes if it's unknown or we want to be thorough
        # If it's a known question, we still "add all" as per previous instruction
        success_count = 0
        try:
            for opt in checkbox_options:
                target_id = opt.get('id', '')
                target_value = opt.get('value', '')
                
                await self.page.evaluate("""([targetId, targetValue]) => {
                    const checkboxes = Array.from(document.querySelectorAll('input[type="checkbox"]'));
                    for (const checkbox of checkboxes) {
                        if ((targetId && checkbox.id === targetId) || (!targetId && targetValue && checkbox.value === targetValue)) {
                            if (!checkbox.checked) {
                                const label = checkbox.id ? document.querySelector(`label[for="${checkbox.id}"]`) : null;
                                if (label) {
                                    label.click();
                                } else {
                                    checkbox.click();
                                }
                                checkbox.checked = true;
                                checkbox.dispatchEvent(new Event('change', { bubbles: true }));
                                checkbox.dispatchEvent(new Event('input', { bubbles: true }));
                            }
                            return true;
                        }
                    }
                    return false;
                }""", [target_id, target_value])
                success_count += 1
                await human_delay(0.2, 0.4)

            if success_count > 0:
                if not is_known:
                    log_info(f"  Unknown checkbox question, selected all {success_count} options randomly/thoroughly")
                await self._click_chat_save_button()
                await human_delay(2, 3)
                log_info(f"Chat answered (checkbox): checked all {success_count} options")
                return True
                
        except Exception as e:
            log_warning(f"Failed to answer chat checkbox question: {e}")
            
        return False

    def _get_preferred_locations(self, screening: dict) -> list[str]:
        raw = screening.get('preferred_locations')
        if isinstance(raw, str):
            locations = [raw]
        elif isinstance(raw, list):
            locations = raw
        else:
            locations = []

        locations = [str(x).strip() for x in locations if str(x).strip()]
        if locations:
            return locations

        preferred_cities = self.profile.get('location', {}).get('preferred_cities', [])
        if isinstance(preferred_cities, list):
            cities = [str(x).strip() for x in preferred_cities if str(x).strip()]
            if cities:
                return cities

        current = screening.get('current_location', 'Faridabad')
        return [current] if current else []

    def _expand_location_aliases(self, locations: list[str]) -> list[str]:
        alias_map = {
            'bangalore': ['bengaluru'],
            'bengaluru': ['bangalore'],
            'bombay': ['mumbai'],
            'mumbai': ['bombay'],
            'madras': ['chennai'],
            'chennai': ['madras'],
        }
        expanded: list[str] = []
        seen: set[str] = set()
        for location in locations:
            cleaned = str(location).strip()
            if not cleaned:
                continue
            variants = [cleaned]
            variants.extend(alias_map.get(cleaned.lower(), []))
            for variant in variants:
                key = variant.lower()
                if key not in seen:
                    seen.add(key)
                    expanded.append(variant)
        return expanded

    def _get_preferred_location(self, screening: dict) -> str:
        locations = self._get_preferred_locations(screening)
        return locations[0] if locations else screening.get('current_location', 'Faridabad')

    def _resolve_screening_answer(self, question_text: str, screening: dict, compensation: dict) -> str | None:
        qt = question_text.lower()

        if 'fresher' in qt and ('experienced' in qt or 'experience' in qt):
            exp = screening.get('total_experience_years', 4)
            return 'experienced' if exp > 0 else 'fresher'

        if 'interview' in qt and any(k in qt for k in ['availability', 'available', 'attend', 'slot', 'schedule']):
            return 'Yes'

        if ('face to face' in qt or 'f2f' in qt or 'virtual interview' in qt) and ('willing' in qt or 'available' in qt or 'attend' in qt):
            return 'Yes'

        if qt.strip().endswith('?'):
            yes_no_questions = {
                'relocate': screening.get('willing_to_relocate', True),
                'night shift': screening.get('comfortable_night_shifts', False),
                'rotational shift': screening.get('comfortable_rotational_shifts', True),
                'gap': screening.get('has_gap', False),
                'passport': screening.get('passport_valid', True),
                'work from office': True,
                'work from home': True,
                'remote': True,
                'hybrid': True,
                'f2f': True,
                'face to face': True,
                'c2h': True,
                'contract': True,
                'onsite': True,
            }
            for kw, answer in yes_no_questions.items():
                if kw in qt:
                    return 'Yes' if answer else 'No'

        answer_map = {
            'total_experience': str(screening.get('total_experience_years', 4)),
            'relevant_experience': str(screening.get('total_experience_years', 4)),
            'notice_period': screening.get('notice_period', '30 Days'),
            'current_ctc': compensation.get('current_ctc', screening.get('current_ctc', '20 LPA')),
            'expected_ctc': compensation.get('expected_ctc', screening.get('expected_ctc', '25-40 LPA')),
            'current_location': screening.get('current_location', 'Faridabad'),
            'preferred_location': self._get_preferred_location(screening),
            'highest_education': screening.get('highest_education', 'B.Tech'),
            'education_type': screening.get('education_type', 'Full Time'),
            'team_size_managed': str(screening.get('team_size_managed', 5)),
        }

        field_id = self._identify_field(qt)
        if field_id and field_id in answer_map:
            return answer_map[field_id]

        bool_answer_map = {
            'willing_to_relocate': screening.get('willing_to_relocate', True),
            'comfortable_night_shifts': screening.get('comfortable_night_shifts', False),
            'comfortable_rotational_shifts': screening.get('comfortable_rotational_shifts', True),
            'has_gap': screening.get('has_gap', False),
            'passport_valid': screening.get('passport_valid', True),
        }
        if field_id and field_id in bool_answer_map:
            return 'Yes' if bool_answer_map[field_id] else 'No'

        skills = screening.get('skills_experience', {})
        if skills:
            for skill_name, years in skills.items():
                patterns = [
                    skill_name.lower(),
                    skill_name.lower().replace(' ', ''),
                    skill_name.lower().replace(' ', '-'),
                    skill_name.lower().split()[0] if ' ' in skill_name else skill_name.lower(),
                ]
                if any(p in qt for p in patterns):
                    if 'experience' in qt or 'year' in qt or 'how many' in qt:
                        return str(years)
                    if 'worked' in qt or 'familiar' in qt or 'know' in qt or 'do you' in qt:
                        return 'Yes' if years > 0 else 'No'

        if 'experience' in qt and ('year' in qt or 'how many' in qt):
            return str(screening.get('total_experience_years', 4))

        if 'ctc' in qt or 'salary' in qt or 'compensation' in qt or 'lacs' in qt or 'lpa' in qt:
            if 'current' in qt or 'present' in qt or 'existing' in qt:
                return compensation.get('current_ctc', screening.get('current_ctc', '20 LPA'))
            if 'expected' in qt or 'desired' in qt:
                return compensation.get('expected_ctc', screening.get('expected_ctc', '25-40 LPA'))

        if 'notice' in qt and ('period' in qt or 'month' in qt or 'day' in qt):
            return screening.get('notice_period', '30 Days')

        if 'location' in qt or 'city' in qt:
            if 'preferred' in qt or 'prefer' in qt:
                return self._get_preferred_location(screening)
            return screening.get('current_location', 'Faridabad')

        if 'education' in qt or 'qualification' in qt or 'degree' in qt:
            return screening.get('highest_education', 'B.Tech')

        if 'employment' in qt and 'status' in qt:
            return screening.get('employment_status', 'Serving Notice')

        if 'domain' in qt or 'industry' in qt:
            industries = screening.get('industries_worked', [])
            if industries:
                return industries[0]

        candidate = self.profile.get('candidate', {})
        if 'mobile' in qt or 'phone' in qt or 'number' in qt:
            phone = candidate.get('phone', '')
            if phone:
                digits = re.sub(r'[^\d+]', '', phone)
                return digits

        if 'email' in qt or 'mail' in qt:
            email = candidate.get('email', '')
            if email:
                return email

        if 'name' in qt and ('your' in qt or 'full' in qt):
            name = candidate.get('full_name', '')
            if name:
                return name

        return None

    def _resolve_radio_answer(self, question_text: str, radio_options: list[dict], screening: dict) -> dict | None:
        qt = question_text.lower()
        field_id = self._identify_field(qt)

        if 'interview' in qt and any(k in qt for k in ['availability', 'available', 'attend', 'slot', 'schedule']):
            return self._find_yes_no_radio_option(radio_options, True) or self._find_radio_option(radio_options, 'available', partial=True)

        if ('face to face' in qt or 'f2f' in qt or 'virtual interview' in qt) and ('willing' in qt or 'available' in qt or 'attend' in qt):
            return self._find_yes_no_radio_option(radio_options, True)

        skills = screening.get('skills_experience', {})
        if skills:
            for skill_name, years in skills.items():
                patterns = [
                    skill_name.lower(),
                    skill_name.lower().replace(' ', ''),
                    skill_name.lower().replace(' ', '-'),
                ]
                if any(p in qt for p in patterns):
                    return self._find_best_skill_radio(radio_options, skill_name, skills)

        skill_keywords = ['technical competency', 'skill', 'technology', 'stack', 'domain', 'expertise', 'specialization']
        if any(kw in qt for kw in skill_keywords):
            return self._find_best_skill_radio(radio_options, '', skills)

        bool_map = {
            'willing_to_relocate': screening.get('willing_to_relocate', True),
            'comfortable_night_shifts': screening.get('comfortable_night_shifts', False),
            'comfortable_rotational_shifts': screening.get('comfortable_rotational_shifts', True),
            'has_gap': screening.get('has_gap', False),
            'passport_valid': screening.get('passport_valid', True),
        }
        if field_id and field_id in bool_map:
            return self._find_yes_no_radio_option(radio_options, bool_map[field_id])

        if field_id == 'notice_period':
            return self._find_notice_period_radio(radio_options, screening.get('notice_period', '30 Days'))

        value_map = {
            'current_ctc': screening.get('current_ctc', ''),
            'expected_ctc': screening.get('expected_ctc', ''),
            'current_location': screening.get('current_location', ''),
            'preferred_location': self._get_preferred_location(screening),
            'education_type': screening.get('education_type', 'Full Time'),
            'highest_education': screening.get('highest_education', 'B.Tech'),
            'team_size_managed': str(screening.get('team_size_managed', 5)),
            'total_experience': str(screening.get('total_experience_years', 4)),
            'relevant_experience': str(screening.get('total_experience_years', 4)),
        }
        if field_id and field_id in value_map:
            match = self._find_radio_option(radio_options, str(value_map[field_id]), partial=True)
            if match:
                return match

        return None

    def _find_radio_option(self, radio_options: list[dict], target: str, partial: bool = False) -> dict | None:
        target_lower = str(target).lower().strip()
        if not target_lower:
            return None
        target_digits = re.sub(r'[^\d.]', '', target_lower)

        for opt in radio_options:
            combined = f"{opt.get('value', '')} {opt.get('label', '')}".lower().strip()
            if combined == target_lower:
                return opt

        for opt in radio_options:
            combined = f"{opt.get('value', '')} {opt.get('label', '')}".lower().strip()
            if target_lower in combined:
                return opt

        if partial:
            for opt in radio_options:
                combined = f"{opt.get('value', '')} {opt.get('label', '')}".lower().strip()
                if combined in target_lower:
                    return opt

        if target_digits:
            for opt in radio_options:
                combined = f"{opt.get('value', '')} {opt.get('label', '')}".lower().strip()
                opt_digits = re.sub(r'[^\d.]', '', combined)
                if opt_digits == target_digits:
                    return opt

        return None

    def _find_yes_no_radio_option(self, radio_options: list[dict], answer: bool) -> dict | None:
        yes_labels = ['yes', 'ye', 'true', '1', 'yeah', 'yep', 'available', 'ok']
        no_labels = ['no', 'false', '0', 'nope', 'none']
        target_labels = yes_labels if answer else no_labels
        for opt in radio_options:
            combined = f"{opt.get('value', '')} {opt.get('label', '')}".lower().strip()
            if any(label == combined or label in combined for label in target_labels):
                return opt
        return None

    def _find_notice_period_radio(self, radio_options: list[dict], notice_period: str) -> dict | None:
        desired = str(notice_period).strip()
        if not desired:
            return None

        direct = self._find_radio_option(radio_options, desired, partial=True)
        if direct:
            return direct

        desired_lower = desired.lower()
        desired_days_match = re.search(r'(\d+)', desired_lower)
        desired_days = int(desired_days_match.group(1)) if desired_days_match else None

        if 'immediate' in desired_lower:
            for keyword in ['immediate', 'join immediately', 'immediate joiner']:
                match = self._find_radio_option(radio_options, keyword, partial=True)
                if match:
                    return match

        if desired_days is not None:
            keyword_groups: list[list[str]] = []
            if desired_days <= 15:
                keyword_groups.append(['immediate', 'join immediately', '15 day', '15 days'])
            elif desired_days <= 45:
                keyword_groups.append(['1 month', '30 day', '30 days', 'serving notice'])
            elif desired_days <= 75:
                keyword_groups.append(['2 month', '60 day', '60 days'])
            elif desired_days <= 105:
                keyword_groups.append(['3 month', '90 day', '90 days'])
            else:
                keyword_groups.append(['more than 3 months', '4 month', '120 day'])

            for keywords in keyword_groups:
                for keyword in keywords:
                    match = self._find_radio_option(radio_options, keyword, partial=True)
                    if match:
                        return match

        return None

    def _find_best_skill_radio(self, radio_options: list[dict], skill_name: str, skills: dict) -> dict | None:
        if not skills:
            return radio_options[0] if radio_options else None

        best_option = None
        best_score = -1

        for opt in radio_options:
            opt_text = opt.get('value', '').lower() + ' ' + opt.get('label', '').lower()
            score = 0
            for sname, syears in skills.items():
                s_lower = sname.lower()
                s_nospace = s_lower.replace(' ', '')
                if s_lower in opt_text or s_nospace in opt_text.replace(' ', ''):
                    score += syears
            if score > best_score:
                best_score = score
                best_option = opt

        return best_option

    async def _handle_application_form(self, job: dict) -> tuple[bool, bool]:
        """Handle form filling and submission. Returns (success, was_chat)."""
        try:
            await self.page.wait_for_load_state("domcontentloaded", timeout=15000)
            await human_delay(1, 2)

            screening = self.profile.get("screening_answers", {})
            compensation = self.profile.get("compensation", {})
            if not screening:
                log_warning("No screening answers found in config")
                screening = {}

            has_chat = await self._wait_for_screening_chat(timeout=10)
            if has_chat:
                log_info("Screening chatbot detected - starting sequential Q&A")
                filled_count = await self._handle_screening_chat(screening, compensation)
                log_info(f"Screening chat: answered {filled_count} questions")
                if filled_count > 0:
                    log_success("Application submitted via chatbot")
                    return True, True
            else:
                log_info("No screening chatbot found, trying traditional form fill")
                filled_count = await self._handle_traditional_form(screening, compensation)
                log_info(f"Traditional form: filled {filled_count} fields")

            if await self._fill_cover_letter(job):
                pass

            await self._submit_form()
            return True, False

        except Exception as e:
            log_error(f"Error handling application form: {e}")
            try:
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                path = f"debug_form_error_{ts}.png"
                await self.page.screenshot(path=path, full_page=True)
                log_info(f"Screenshot saved as {path}")
            except Exception:
                pass
            try:
                submit_btn = self.page.locator('button:has-text("Submit"), input[type="submit"]')
                if await submit_btn.first.is_visible(timeout=2000):
                    await submit_btn.first.click()
                    log_info("Final form submission attempt after error")
            except Exception:
                pass
            return False, False

    async def _handle_screening_chat(self, screening: dict, compensation: dict) -> int:
        filled_count = 0
        max_questions = 20
        last_question = ""
        stale_count = 0

        for q_num in range(max_questions):
            await human_delay(2, 3)

            question_text = await self._get_current_chat_question()
            if not question_text:
                log_info("No more chat questions found")
                break

            if question_text == last_question:
                stale_count += 1
                if stale_count >= 3:
                    log_warning(f"Same question repeated 3 times: '{question_text[:50]}' - skipping")
                    break
                log_warning(f"Same question repeated (attempt {stale_count}), retrying...")
                await human_delay(2, 3)
            else:
                stale_count = 0

            last_question = question_text
            log_info(f"Chat Q{q_num + 1}: {question_text[:80]}")

            has_text = await self._has_active_text_input()
            has_radio = await self._has_active_radio_options()
            has_checkbox = await self._has_active_checkbox_options()

            if has_radio:
                radio_options = await self._get_radio_options()
                log_info(f"  Radio options: {[r.get('value','')[:25] for r in radio_options[:5]]}")
                success = await self._answer_chat_radio_question(question_text, radio_options, screening)
                if success:
                    filled_count += 1
                else:
                    log_warning(f"  Could not answer radio Q{q_num + 1}")
            elif has_checkbox:
                checkbox_options = await self._get_checkbox_options()
                log_info(f"  Checkbox options: {[c.get('label','')[:25] for c in checkbox_options[:5]]}")
                success = await self._answer_chat_checkbox_question(question_text, checkbox_options, screening)
                if success:
                    filled_count += 1
                else:
                    log_warning(f"  Could not answer checkbox Q{q_num + 1}")
            elif has_text:
                success = await self._answer_chat_text_question(question_text, screening, compensation)
                if success:
                    filled_count += 1
                else:
                    log_warning(f"  Could not answer text Q{q_num + 1}")
            else:
                log_warning(f"  No input method found for Q{q_num + 1}")

            await human_delay(3, 5)

            if not question_text:
                break

        return filled_count

    async def _handle_traditional_form(self, screening: dict, compensation: dict) -> int:
        form_elements = []
        for attempt in range(3):
            delay = 2 + attempt * 2
            if attempt > 0:
                log_info(f"Retry {attempt + 1}/3: waiting {delay}s for form elements...")
                await human_delay(delay, delay + 1)

            await human_delay(2, 3)
            form_elements = await self._collect_form_elements()
            if form_elements:
                break
            log_warning(f"Attempt {attempt + 1}/3: No form elements found")

        if not form_elements:
            log_warning("No form elements found after all retries")
            return 0

        log_info(f"Found {len(form_elements)} form elements for processing")
        filled_count = 0
        unfilled_elements = []

        radio_groups: dict[str, list] = {}
        multi_select_groups: list[dict] = []
        for elem in form_elements:
            info = elem['info']
            if info.get('type') == 'radio':
                group_name = info.get('name', '') or info.get('id', '')
                if group_name:
                    radio_groups.setdefault(group_name, []).append(elem)
            if info.get('isMultiSelect'):
                group_key = info.get('name', '') or info.get('id', '') or f"multi_{len(multi_select_groups)}"
                multi_select_groups.append({'key': group_key, 'element': elem['element'], 'info': info})

        for elem in form_elements:
            el = elem['element']
            info = elem['info']
            field_id = info.get('id', '').lower()
            field_name = info.get('name', '').lower()
            field_placeholder = info.get('placeholder', '').lower()
            field_label = info.get('text', '').lower()
            field_class = info.get('className', '').lower()
            field_tag = info.get('tag', '').lower()
            field_type = info.get('type', '').lower()
            field_text_combined = f"{field_id} {field_name} {field_placeholder} {field_label} {field_class} {info.get('questionText', '').lower()}"

            if field_type == 'radio':
                continue
            if info.get('isMultiSelect') and not info.get('multiple'):
                continue

            if field_type == 'contenteditable':
                if await self._fill_contenteditable_field(el, info, field_text_combined, screening, compensation):
                    filled_count += 1
                else:
                    unfilled_elements.append({'type': 'contenteditable', 'text': field_text_combined[:100]})
                continue

            if field_tag == 'select' and not info.get('multiple'):
                if await self._fill_select_field(el, info, field_text_combined, screening, compensation):
                    filled_count += 1
                else:
                    unfilled_elements.append({'type': 'select', 'text': field_text_combined[:100]})
                continue

            if field_tag == 'select' and info.get('multiple'):
                if await self._fill_multiselect_field(el, info, field_text_combined, screening, compensation):
                    filled_count += 1
                else:
                    unfilled_elements.append({'type': 'multiselect', 'text': field_text_combined[:100]})
                continue

            if info.get('customDropdown') and info.get('dropdownOptions'):
                if await self._fill_custom_dropdown(el, info, field_text_combined, screening, compensation):
                    filled_count += 1
                else:
                    unfilled_elements.append({'type': 'custom_dropdown', 'text': field_text_combined[:100]})
                continue

            if field_type == 'checkbox':
                if await self._fill_checkbox_field(el, info, field_text_combined, screening):
                    filled_count += 1
                else:
                    unfilled_elements.append({'type': 'checkbox', 'text': field_text_combined[:100]})
                continue

            if field_type in ('text', 'number', 'tel', 'email'):
                if await self._fill_text_field(el, info, field_text_combined, screening, compensation):
                    filled_count += 1
                else:
                    unfilled_elements.append({'type': 'text', 'text': field_text_combined[:100]})
                continue

        for group_name, radio_elems in radio_groups.items():
            if await self._fill_radio_group(radio_elems, screening, compensation):
                filled_count += 1
            else:
                unfilled_elements.append({'type': 'radio_group', 'name': group_name})

        for msg in multi_select_groups:
            if await self._fill_multiselect_group(msg, screening):
                filled_count += 1
            else:
                unfilled_elements.append({'type': 'multiselect_group', 'key': msg['key']})

        if unfilled_elements:
            log_warning(f"Could not fill {len(unfilled_elements)} elements:")
            for uf in unfilled_elements:
                detail = f"type={uf['type']}"
                if uf.get('text'):
                    detail += f" text='{uf['text'][:50]}'"
                log_warning(f"  - {detail}")

        return filled_count

    async def _collect_form_elements(self) -> list[dict]:
        form_elements = []
        seen_signatures = set()
        for frame in self._get_frames():
            try:
                filtered_inputs = await frame.query_selector_all(
                    "input, select, textarea, [contenteditable='true'], [contenteditable=''], div.textArea"
                )
            except Exception:
                continue

            for inp in filtered_inputs:
                try:
                    if not await inp.is_visible(timeout=1000):
                        continue
                    info = await inp.evaluate("""el => {
                    const tag = el.tagName.toLowerCase();
                    const isContentEditable = el.contentEditable === 'true' || el.contentEditable === '';
                    const type = (el.type || (isContentEditable ? 'contenteditable' : tag));
                    const name = el.name || '';
                    const id = el.id || '';
                    const placeholder = el.placeholder || '';
                    const className = (el.className || '').toString();
                    const multiple = el.multiple || false;

                    let labelText = '';
                    if (id) {
                        const label = document.querySelector('label[for="' + id + '"]');
                        if (label) labelText = label.innerText || '';
                    }
                    if (!labelText && name) {
                        const label = document.querySelector('label[for="' + name + '"]');
                        if (label) labelText = label.innerText || '';
                    }
                    if (!labelText) {
                        const parent = el.closest('div[class], section[class], li[class], fieldset');
                        if (parent) {
                            const lbl = parent.querySelector('label, legend, .label, .question, .field-label, [class*="label"], [class*="question"]');
                            if (lbl && lbl !== el) labelText = lbl.innerText || '';
                        }
                    }

                    let questionText = '';
                    let walkEl = el.parentElement;
                    for (let i = 0; i < 8 && walkEl; i++) {
                        const allText = walkEl.innerText || '';
                        const lines = allText.split('\\n').map(l => l.trim()).filter(l => l.length > 3 && l.length < 300);
                        if (lines.length >= 1 && lines.length <= 5) {
                            for (const line of lines) {
                                if (line.includes('?') || line.toLowerCase().includes('experience') ||
                                    line.toLowerCase().includes('notice') || line.toLowerCase().includes('ctc') ||
                                    line.toLowerCase().includes('relocate') || line.toLowerCase().includes('shift') ||
                                    line.toLowerCase().includes('education') || line.toLowerCase().includes('skill') ||
                                    line.toLowerCase().includes('location') || line.toLowerCase().includes('gap') ||
                                    line.toLowerCase().includes('passport') || line.toLowerCase().includes('team')) {
                                    questionText = line;
                                    break;
                                }
                            }
                            if (questionText) break;
                        }
                        walkEl = walkEl.parentElement;
                    }

                    let options = [];
                    if (tag === 'select') {
                        options = Array.from(el.options).map(o => ({
                            value: o.value,
                            text: o.text.trim()
                        }));
                    }

                    let isMultiSelect = false;
                    let multiSelectOptions = [];
                    if (tag === 'select' && el.multiple) {
                        isMultiSelect = true;
                        multiSelectOptions = options;
                    }
                    const parent = el.closest('div[class], section[class], li[class], fieldset, [role="group"]');
                    if (parent && !isMultiSelect) {
                        const checkboxes = parent.querySelectorAll('input[type="checkbox"]');
                        const visibleCheckboxes = Array.from(checkboxes).filter(cb => cb.offsetParent !== null || cb.type === 'checkbox');
                        if (visibleCheckboxes.length >= 2) {
                            isMultiSelect = true;
                            multiSelectOptions = Array.from(visibleCheckboxes).map(cb => {
                                const lbl = parent.querySelector('label[for="' + (cb.id || '') + '"]');
                                const parentDiv = cb.closest('label, div, li');
                                return {
                                    value: cb.value || cb.id || '',
                                    text: (lbl ? lbl.innerText : (parentDiv ? parentDiv.innerText : '')).trim().substring(0, 100),
                                    id: cb.id || '',
                                    checked: cb.checked
                                };
                            });
                        }
                    }

                    let customDropdown = false;
                    let dropdownOptions = [];
                    if (className.includes('dropdown') || className.includes('select') || className.includes('multiselect')) {
                        customDropdown = true;
                        const parent2 = el.closest('div[class]');
                        if (parent2) {
                            const items = parent2.querySelectorAll('[class*="option"], [class*="item"], [role="option"], [role="listbox"] > div, li[class*="option"]');
                            dropdownOptions = Array.from(items).map(item => ({
                                value: item.getAttribute('data-value') || item.getAttribute('value') || '',
                                text: (item.innerText || '').trim().substring(0, 100)
                            }));
                        }
                    }

                    return {
                        tag: tag,
                        type: type,
                        name: name,
                        id: id,
                        placeholder: placeholder,
                        className: className,
                        text: (labelText || '').substring(0, 200),
                        questionText: questionText.substring(0, 300),
                        options: options,
                        value: el.value || '',
                        isContentEditable: isContentEditable,
                        isMultiSelect: isMultiSelect,
                        multiSelectOptions: multiSelectOptions,
                        customDropdown: customDropdown,
                        dropdownOptions: dropdownOptions,
                        multiple: multiple
                    };
                }""")
                    info['frameUrl'] = frame.url
                    signature = (
                        info.get('frameUrl', ''),
                        info.get('id', ''),
                        info.get('name', ''),
                        info.get('type', ''),
                        info.get('text', ''),
                    )
                    if signature in seen_signatures:
                        continue
                    seen_signatures.add(signature)
                    form_elements.append({'element': inp, 'info': info})
                except Exception:
                    continue

        return form_elements

    def _identify_field(self, field_text: str) -> str | None:
        field_lower = field_text.lower()

        field_patterns = [
            ('notice_period', ['notice period', 'notice_period', 'noticeperiod']),
            ('current_ctc', ['current ctc', 'current_ctc', 'present ctc', 'current salary', 'present salary']),
            ('expected_ctc', ['expected ctc', 'expected_ctc', 'desired ctc', 'expected salary', 'desired salary']),
            ('current_location', ['current location', 'current_location', 'current city']),
            ('education_type', ['education type', 'course type', 'education mode', 'mode of education', 'education_type']),
            ('highest_education', ['highest education', 'highest qualification', 'education', 'degree', 'qualification']),
            ('willing_to_relocate', ['relocate', 'willing to relocate', 'relocation', 'willing_to_relocate']),
            ('comfortable_night_shifts', ['night shift', 'night_shift', 'comfortable night', 'willing to work night']),
            ('comfortable_rotational_shifts', ['rotational shift', 'rotational_shift', 'rotating shift']),
            ('has_gap', ['employment gap', 'gap year', 'career gap', 'gap in employment', 'has_gap']),
            ('passport_valid', ['passport', 'valid passport', 'passport_valid']),
            ('team_size_managed', ['team size', 'team managed', 'team_size']),
            ('total_experience', ['total experience', 'total_experience', 'years of experience', 'year of experience', 'overall experience']),
            ('relevant_experience', ['relevant experience', 'relevant_experience']),
        ]

        for field_id, patterns in field_patterns:
            for pattern in patterns:
                if pattern in field_lower:
                    neg_keywords = {
                        'total_experience': ['skill', 'notice', 'relevant'],
                        'relevant_experience': ['skill'],
                        'current_ctc': ['expected', 'desired'],
                        'highest_education': ['type', 'mode'],
                        'current_location': ['preferred', 'prefer'],
                    }
                    negs = neg_keywords.get(field_id, [])
                    if any(neg in field_lower for neg in negs):
                        continue
                    return field_id

        salary_kw = ['salary', 'ctc', 'compensation']
        if any(kw in field_lower for kw in salary_kw):
            if any(kw in field_lower for kw in ['current', 'present', 'existing']):
                return 'current_ctc'
            if any(kw in field_lower for kw in ['expected', 'desired']):
                return 'expected_ctc'

        location_kw = ['location', 'city']
        if any(kw in field_lower for kw in location_kw):
            if any(kw in field_lower for kw in ['preferred', 'prefer']):
                return 'preferred_location'
            return 'current_location'

        experience_kw = ['experience', 'exp year', 'years of exp']
        if any(kw in field_lower for kw in experience_kw):
            if any(kw in field_lower for kw in ['relevant']):
                return 'relevant_experience'
            if not any(kw in field_lower for kw in ['skill', 'notice']):
                return 'total_experience'

        return None

    def _find_option(self, options: list[dict], target: str, partial: bool = False) -> str | None:
        target_lower = target.lower().strip()
        for opt in options:
            opt_text = opt.get('text', '').lower().strip()
            opt_value = opt.get('value', '').lower().strip()
            if opt_text == target_lower or opt_value == target_lower:
                return opt.get('value') or opt.get('text')
        if partial:
            for opt in options:
                opt_text = opt.get('text', '').lower().strip()
                if target_lower in opt_text or opt_text in target_lower:
                    return opt.get('value') or opt.get('text')
            target_digits = re.sub(r'[^\d.]', '', target)
            if target_digits:
                for opt in options:
                    opt_digits = re.sub(r'[^\d.]', '', opt.get('text', ''))
                    if opt_digits == target_digits:
                        return opt.get('value') or opt.get('text')
        return None

    def _find_yes_no_option(self, options: list[dict], answer: bool) -> str | None:
        yes_labels = ['yes', 'ye', 'true', '1']
        no_labels = ['no', 'false', '0', 'none']
        target_labels = yes_labels if answer else no_labels
        for opt in options:
            opt_text = opt.get('text', '').lower().strip()
            if opt_text in target_labels:
                return opt.get('value') or opt.get('text')
        return None

    def _find_shift_option(self, options: list[dict], screening: dict) -> str | None:
        night = screening.get('comfortable_night_shifts', False)
        rotational = screening.get('comfortable_rotational_shifts', True)
        if night:
            preferred = ['night', 'night shift', 'any', 'all', 'flexible', 'rotational']
        elif rotational:
            preferred = ['rotational', 'day', 'general', 'flexible', 'any']
        else:
            preferred = ['day', 'day shift', 'general', 'morning', 'regular']
        for pref in preferred:
            for opt in options:
                opt_text = opt.get('text', '').lower().strip()
                if pref == opt_text or pref in opt_text:
                    return opt.get('value') or opt.get('text')
        return None

    async def _fill_select_field(self, el, info: dict, field_text: str, screening: dict, compensation: dict) -> bool:
        options = info.get('options', [])
        if not options:
            return False

        field_id = self._identify_field(field_text)
        if not field_id:
            return False

        value_map = {
            'notice_period': screening.get('notice_period', '30 Days'),
            'current_ctc': compensation.get('current_ctc', screening.get('current_ctc', '20 LPA')),
            'expected_ctc': compensation.get('expected_ctc', screening.get('expected_ctc', '25-40 LPA')),
            'current_location': screening.get('current_location', 'Faridabad'),
            'preferred_location': self._get_preferred_location(screening),
            'education_type': screening.get('education_type', 'Full Time'),
            'highest_education': screening.get('highest_education', 'B.Tech'),
            'team_size_managed': str(screening.get('team_size_managed', 5)),
            'total_experience': str(screening.get('total_experience_years', 4)),
            'relevant_experience': str(screening.get('total_experience_years', 4)),
        }

        bool_map = {
            'willing_to_relocate': screening.get('willing_to_relocate', True),
            'comfortable_night_shifts': screening.get('comfortable_night_shifts', False),
            'comfortable_rotational_shifts': screening.get('comfortable_rotational_shifts', True),
            'has_gap': screening.get('has_gap', False),
            'passport_valid': screening.get('passport_valid', True),
        }

        try:
            if field_id in value_map:
                target_value = value_map[field_id]
                match = self._find_option(options, str(target_value), partial=True)
                if match:
                    await el.select_option(value=match)
                    await human_delay(0.5, 1.0)
                    log_info(f"Selected dropdown {field_id} with: {target_value}")
                    return True
                opt_texts = [o.get('text', '') for o in options]
                log_warning(f"No matching option for {field_id}={target_value} in {opt_texts}")
                return False

            if field_id in bool_map:
                answer = bool_map[field_id]
                if field_id in ('comfortable_night_shifts', 'comfortable_rotational_shifts'):
                    match = self._find_shift_option(options, screening)
                else:
                    match = self._find_yes_no_option(options, answer)
                if match:
                    await el.select_option(value=match)
                    await human_delay(0.5, 1.0)
                    log_info(f"Selected dropdown {field_id} with: {answer}")
                    return True
                return False
        except Exception as e:
            log_warning(f"Could not select dropdown {field_id}: {e}")
        return False

    async def _fill_text_field(self, el, info: dict, field_text: str, screening: dict, compensation: dict) -> bool:
        field_id = self._identify_field(field_text)

        value_map = {
            'notice_period': screening.get('notice_period', '30 Days'),
            'current_ctc': compensation.get('current_ctc', screening.get('current_ctc', '20 LPA')),
            'expected_ctc': compensation.get('expected_ctc', screening.get('expected_ctc', '25-40 LPA')),
            'current_location': screening.get('current_location', 'Faridabad'),
            'preferred_location': self._get_preferred_location(screening),
            'education_type': screening.get('education_type', 'Full Time'),
            'highest_education': screening.get('highest_education', 'B.Tech'),
            'team_size_managed': str(screening.get('team_size_managed', 5)),
            'total_experience': str(screening.get('total_experience_years', 4)),
            'relevant_experience': str(screening.get('total_experience_years', 4)),
        }

        if field_id and field_id in value_map:
            try:
                await el.fill(value_map[field_id])
                await human_delay(0.5, 1.0)
                log_info(f"Filled text field {field_id} with: {value_map[field_id]}")
                return True
            except Exception as e:
                log_warning(f"Could not fill text field {field_id}: {e}")
                return False

        skills = screening.get('skills_experience', {})
        if skills:
            field_lower = field_text.lower()
            for skill_name, years in skills.items():
                patterns = [
                    skill_name.lower(),
                    skill_name.lower().replace(' ', ''),
                    skill_name.lower().replace(' ', '-'),
                    skill_name.lower().split()[0] if ' ' in skill_name else skill_name.lower(),
                ]
                if any(p in field_lower for p in patterns):
                    try:
                        await el.fill(str(years))
                        await human_delay(0.5, 1.0)
                        log_info(f"Filled skill field for {skill_name} with: {years} years")
                        return True
                    except Exception as e:
                        log_warning(f"Could not fill skill field for {skill_name}: {e}")
                        return False

        return False

    async def _fill_contenteditable_field(self, el, info: dict, field_text: str, screening: dict, compensation: dict) -> bool:
        field_id = self._identify_field(field_text)

        value_map = {
            'notice_period': screening.get('notice_period', '30 Days'),
            'current_ctc': compensation.get('current_ctc', screening.get('current_ctc', '20 LPA')),
            'expected_ctc': compensation.get('expected_ctc', screening.get('expected_ctc', '25-40 LPA')),
            'current_location': screening.get('current_location', 'Faridabad'),
            'preferred_location': self._get_preferred_location(screening),
            'education_type': screening.get('education_type', 'Full Time'),
            'highest_education': screening.get('highest_education', 'B.Tech'),
            'team_size_managed': str(screening.get('team_size_managed', 5)),
            'total_experience': str(screening.get('total_experience_years', 4)),
            'relevant_experience': str(screening.get('total_experience_years', 4)),
        }

        if field_id and field_id in value_map:
            fill_value = value_map[field_id]
            try:
                await el.click()
                await human_delay(0.3, 0.5)
                await el.type(fill_value, delay=50)
                await human_delay(0.5, 1.0)
                log_info(f"Filled contenteditable {field_id} with: {fill_value}")
                return True
            except Exception as e:
                log_warning(f"Could not fill contenteditable {field_id}: {e}")
                return False

        skills = screening.get('skills_experience', {})
        if skills:
            field_lower = field_text.lower()
            for skill_name, years in skills.items():
                patterns = [
                    skill_name.lower(),
                    skill_name.lower().replace(' ', ''),
                    skill_name.lower().replace(' ', '-'),
                    skill_name.lower().split()[0] if ' ' in skill_name else skill_name.lower(),
                ]
                if any(p in field_lower for p in patterns):
                    try:
                        await el.click()
                        await human_delay(0.3, 0.5)
                        await el.type(str(years), delay=50)
                        await human_delay(0.5, 1.0)
                        log_info(f"Filled contenteditable skill {skill_name} with: {years} years")
                        return True
                    except Exception as e:
                        log_warning(f"Could not fill contenteditable skill {skill_name}: {e}")
                        return False

        return False

    async def _fill_checkbox_field(self, el, info: dict, field_text: str, screening: dict) -> bool:
        field_id = self._identify_field(field_text)

        checkbox_map = {
            'willing_to_relocate': screening.get('willing_to_relocate', True),
            'comfortable_night_shifts': screening.get('comfortable_night_shifts', False),
            'comfortable_rotational_shifts': screening.get('comfortable_rotational_shifts', True),
            'has_gap': screening.get('has_gap', False),
            'passport_valid': screening.get('passport_valid', True),
        }

        if field_id and field_id in checkbox_map:
            desired = checkbox_map[field_id]
            try:
                is_checked = await el.is_checked()
                if is_checked != desired:
                    await el.click()
                await human_delay(0.5, 1.0)
                log_info(f"Set checkbox {field_id} to: {desired}")
                return True
            except Exception as e:
                log_warning(f"Could not set checkbox {field_id}: {e}")
        return False

    async def _fill_multiselect_field(self, el, info: dict, field_text: str, screening: dict, compensation: dict) -> bool:
        options = info.get('options', [])
        if not options:
            return False

        field_id = self._identify_field(field_text)
        if not field_id:
            return False

        multi_value_map = {
            'notice_period': [screening.get('notice_period', '30 Days')],
            'current_location': [screening.get('current_location', 'Faridabad')],
            'preferred_location': self._get_preferred_locations(screening),
            'education_type': [screening.get('education_type', 'Full Time')],
            'highest_education': [screening.get('highest_education', 'B.Tech')],
        }

        if field_id not in multi_value_map:
            return False

        target_values = multi_value_map[field_id]
        values_to_select = []
        for target in target_values:
            match = self._find_option(options, str(target), partial=True)
            if match:
                values_to_select.append(match)

        if not values_to_select:
            log_warning(f"Multiselect {field_id}: no matching options found among {[o.get('text','') for o in options]}")
            return False

        try:
            await el.select_option(value=values_to_select)
            await human_delay(0.5, 1.0)
            log_info(f"Selected multiselect {field_id} with: {values_to_select}")
            return True
        except Exception as e:
            log_warning(f"Could not select multiselect {field_id}: {e}")
            return False

    async def _fill_multiselect_group(self, msg: dict, screening: dict) -> bool:
        info = msg['info']
        options = info.get('multiSelectOptions', [])
        if not options:
            return False

        field_text = f"{info.get('id', '').lower()} {info.get('name', '').lower()} {info.get('text', '').lower()} {info.get('questionText', '').lower()}"
        field_id = self._identify_field(field_text)

        bool_map = {
            'willing_to_relocate': screening.get('willing_to_relocate', True),
            'comfortable_night_shifts': screening.get('comfortable_night_shifts', False),
            'comfortable_rotational_shifts': screening.get('comfortable_rotational_shifts', True),
            'has_gap': screening.get('has_gap', False),
            'passport_valid': screening.get('passport_valid', True),
        }

        if field_id in bool_map:
            answer = bool_map[field_id]
            target_label = 'yes' if answer else 'no'
            for opt in options:
                opt_text = opt.get('text', '').lower().strip()
                if target_label in opt_text:
                    try:
                        checkbox = self.page.locator(f'#{opt.get("id", "")}').first
                        if await checkbox.is_visible(timeout=1000):
                            is_checked = await checkbox.is_checked()
                            if not is_checked:
                                await checkbox.click()
                            await human_delay(0.3, 0.5)
                            log_info(f"Checked multiselect option for {field_id}: {opt.get('text', '')}")
                            return True
                    except Exception:
                        continue
                    try:
                        label = self.page.locator(f'label[for="{opt.get("id", "")}"]').first
                        if await label.is_visible(timeout=1000):
                            await label.click()
                            await human_delay(0.3, 0.5)
                            log_info(f"Clicked multiselect label for {field_id}: {opt.get('text', '')}")
                            return True
                    except Exception:
                        continue
            log_warning(f"Multiselect group {field_id}: no matching option for answer={answer}")
            return False

        skills = screening.get('skills_experience', {})
        if skills and not field_id:
            for skill_name, years in skills.items():
                patterns = [
                    skill_name.lower(),
                    skill_name.lower().replace(' ', ''),
                    skill_name.lower().replace(' ', '-'),
                ]
                if any(p in field_text for p in patterns):
                    answer = years > 0
                    target_label = 'yes' if answer else 'no'
                    for opt in options:
                        opt_text = opt.get('text', '').lower().strip()
                        if target_label in opt_text:
                            try:
                                checkbox = self.page.locator(f'#{opt.get("id", "")}').first
                                if await checkbox.is_visible(timeout=1000):
                                    is_checked = await checkbox.is_checked()
                                    if not is_checked:
                                        await checkbox.click()
                                    await human_delay(0.3, 0.5)
                                    log_info(f"Checked skill multiselect for {skill_name}: {opt.get('text', '')}")
                                    return True
                            except Exception:
                                continue
                            try:
                                label = self.page.locator(f'label[for="{opt.get("id", "")}"]').first
                                if await label.is_visible(timeout=1000):
                                    await label.click()
                                    await human_delay(0.3, 0.5)
                                    log_info(f"Clicked skill multiselect label for {skill_name}: {opt.get('text', '')}")
                                    return True
                            except Exception:
                                continue

        return False

    async def _fill_custom_dropdown(self, el, info: dict, field_text: str, screening: dict, compensation: dict) -> bool:
        dropdown_options = info.get('dropdownOptions', [])
        if not dropdown_options:
            return False

        field_id = self._identify_field(field_text)
        if not field_id:
            return False

        value_map = {
            'notice_period': screening.get('notice_period', '30 Days'),
            'current_ctc': compensation.get('current_ctc', screening.get('current_ctc', '20 LPA')),
            'expected_ctc': compensation.get('expected_ctc', screening.get('expected_ctc', '25-40 LPA')),
            'current_location': screening.get('current_location', 'Faridabad'),
            'preferred_location': screening.get('current_location', 'Faridabad'),
            'education_type': screening.get('education_type', 'Full Time'),
            'highest_education': screening.get('highest_education', 'B.Tech'),
            'team_size_managed': str(screening.get('team_size_managed', 5)),
            'total_experience': str(screening.get('total_experience_years', 4)),
            'relevant_experience': str(screening.get('total_experience_years', 4)),
        }

        bool_map = {
            'willing_to_relocate': screening.get('willing_to_relocate', True),
            'comfortable_night_shifts': screening.get('comfortable_night_shifts', False),
            'comfortable_rotational_shifts': screening.get('comfortable_rotational_shifts', True),
            'has_gap': screening.get('has_gap', False),
            'passport_valid': screening.get('passport_valid', True),
        }

        target = None
        if field_id in value_map:
            target = str(value_map[field_id]).lower()
        elif field_id in bool_map:
            target = 'yes' if bool_map[field_id] else 'no'
        else:
            return False

        for opt in dropdown_options:
            opt_text = opt.get('text', '').lower().strip()
            opt_value = opt.get('value', '').lower().strip()
            if target in opt_text or target in opt_value or opt_text in target or opt_value in target:
                try:
                    await el.click()
                    await human_delay(0.5, 1.0)

                    if opt.get('value'):
                        option_el = self.page.locator(f'[data-value="{opt["value"]}"], [value="{opt["value"]}"]').first
                    else:
                        option_el = self.page.get_by_text(opt.get('text', ''), exact=True).first

                    try:
                        if await option_el.is_visible(timeout=2000):
                            await option_el.click()
                            await human_delay(0.5, 1.0)
                            log_info(f"Selected custom dropdown {field_id} with: {opt.get('text', '')}")
                            return True
                    except Exception:
                        pass

                    all_dropdown_items = await self.page.query_selector_all(
                        '[class*="option"], [class*="item"], [role="option"]'
                    )
                    for item in all_dropdown_items:
                        try:
                            if await item.is_visible(timeout=500):
                                item_text = (await item.inner_text()).strip().lower()
                                if target in item_text or item_text in target:
                                    await item.click()
                                    await human_delay(0.5, 1.0)
                                    log_info(f"Selected custom dropdown {field_id} via item search: {item_text}")
                                    return True
                        except Exception:
                            continue

                    log_warning(f"Custom dropdown {field_id}: opened but couldn't find option '{target}'")
                    return False
                except Exception as e:
                    log_warning(f"Custom dropdown {field_id} click failed: {e}")
                    continue

        log_warning(f"Custom dropdown {field_id}: no matching option for '{target}' in {[o.get('text','') for o in dropdown_options]}")
        return False

    async def _fill_radio_group(self, radio_elems: list[dict], screening: dict, compensation: dict) -> bool:
        if not radio_elems:
            return False

        first_info = radio_elems[0]['info']
        field_name = first_info.get('name', '').lower()
        field_id_attr = first_info.get('id', '').lower()

        group_text_parts = [field_name, field_id_attr]
        for elem in radio_elems:
            el = elem['element']
            try:
                parent_text = await el.evaluate("""el => {
                    const parent = el.closest('div[class], section[class], li[class], fieldset, [role="group"]');
                    if (parent) {
                        const lbl = parent.querySelector('label, legend, .label, .question, .field-label, [class*="label"], [class*="question"]');
                        if (lbl && lbl !== el) return lbl.innerText || '';
                    }
                    return '';
                }""")
                if parent_text:
                    group_text_parts.append(parent_text.lower())
            except Exception:
                pass

        question_text = await radio_elems[0]['element'].evaluate("""el => {
            let walkEl = el.parentElement;
            for (let i = 0; i < 10 && walkEl; i++) {
                const allText = walkEl.innerText || '';
                const lines = allText.split('\\n').map(l => l.trim()).filter(l => l.length > 5 && l.length < 300);
                for (const line of lines) {
                    if (line.includes('?') || line.toLowerCase().includes('experience') ||
                        line.toLowerCase().includes('notice') || line.toLowerCase().includes('ctc') ||
                        line.toLowerCase().includes('relocate') || line.toLowerCase().includes('shift') ||
                        line.toLowerCase().includes('education') || line.toLowerCase().includes('skill') ||
                        line.toLowerCase().includes('location') || line.toLowerCase().includes('gap') ||
                        line.toLowerCase().includes('passport') || line.toLowerCase().includes('team') ||
                        line.toLowerCase().includes('computer vision') || line.toLowerCase().includes('worked') ||
                        line.toLowerCase().includes('years') || line.toLowerCase().includes('salary')) {
                        return line.toLowerCase();
                    }
                }
                walkEl = walkEl.parentElement;
            }
            return '';
        }""")
        if question_text:
            group_text_parts.append(question_text)

        group_text = ' '.join(group_text_parts)
        field_id_result = self._identify_field(group_text)

        if not field_id_result:
            return False

        bool_map = {
            'willing_to_relocate': screening.get('willing_to_relocate', True),
            'comfortable_night_shifts': screening.get('comfortable_night_shifts', False),
            'comfortable_rotational_shifts': screening.get('comfortable_rotational_shifts', True),
            'has_gap': screening.get('has_gap', False),
            'passport_valid': screening.get('passport_valid', True),
        }

        if field_id_result in bool_map:
            answer = bool_map[field_id_result]
            return await self._click_radio_by_value(radio_elems, answer)

        value_map = {
            'notice_period': screening.get('notice_period', '30 Days'),
            'current_ctc': compensation.get('current_ctc', screening.get('current_ctc', '20 LPA')),
            'expected_ctc': compensation.get('expected_ctc', screening.get('expected_ctc', '25-40 LPA')),
            'current_location': screening.get('current_location', 'Faridabad'),
            'preferred_location': screening.get('current_location', 'Faridabad'),
            'education_type': screening.get('education_type', 'Full Time'),
            'highest_education': screening.get('highest_education', 'B.Tech'),
            'team_size_managed': str(screening.get('team_size_managed', 5)),
            'total_experience': str(screening.get('total_experience_years', 4)),
            'relevant_experience': str(screening.get('total_experience_years', 4)),
        }

        if field_id_result in value_map:
            target = value_map[field_id_result]
            return await self._click_radio_by_label(radio_elems, str(target))

        skills = screening.get('skills_experience', {})
        if skills:
            for skill_name, years in skills.items():
                patterns = [
                    skill_name.lower(),
                    skill_name.lower().replace(' ', ''),
                    skill_name.lower().replace(' ', '-'),
                ]
                if any(p in group_text for p in patterns):
                    answer = years > 0
                    log_info(f"Skill radio: {skill_name} -> {'Yes' if answer else 'No'}")
                    return await self._click_radio_by_value(radio_elems, answer)

        return False

    async def _click_radio_by_value(self, radio_elems: list[dict], answer: bool) -> bool:
        yes_labels = ['yes', 'ye', 'true', '1', 'yeah', 'yep']
        no_labels = ['no', 'false', '0', 'nope', 'none']
        target_labels = yes_labels if answer else no_labels

        for elem in radio_elems:
            el = elem['element']
            info = elem['info']
            val = info.get('value', '').lower().strip()
            elem_text = ''
            try:
                elem_text = await el.evaluate("""el => {
                    const parent = el.closest('label, div, li');
                    if (parent) return parent.innerText || '';
                    return el.value || '';
                }""")
            except Exception:
                pass

            combined = f"{val} {elem_text.lower()}"

            if any(t in combined for t in target_labels):
                try:
                    radio_id = info.get('id', '')
                    if radio_id:
                        label = self.page.locator(f'label[for="{radio_id}"]').first
                        if await label.is_visible(timeout=1000):
                            await label.click()
                            await human_delay(0.5, 1.0)
                            log_info(f"Clicked radio label for answer={answer}: id={radio_id}")
                            return True
                    await el.click(force=True)
                    await human_delay(0.5, 1.0)
                    log_info(f"Clicked radio for answer={answer}: value={val}")
                    return True
                except Exception as e:
                    log_warning(f"Could not click radio: {e}")
        return False

    async def _click_radio_by_label(self, radio_elems: list[dict], target: str) -> bool:
        target_lower = target.lower().strip()
        target_digits = re.sub(r'[^\d.]', '', target)

        for elem in radio_elems:
            el = elem['element']
            info = elem['info']
            val = info.get('value', '').lower().strip()
            elem_text = ''
            try:
                elem_text = await el.evaluate("""el => {
                    const parent = el.closest('label, div, li');
                    if (parent) return parent.innerText || '';
                    return el.value || '';
                }""")
            except Exception:
                pass

            combined = f"{val} {elem_text.lower()}"
            if target_lower in combined:
                try:
                    await el.click()
                    await human_delay(0.5, 1.0)
                    log_info(f"Clicked radio matching '{target}': value={val}")
                    return True
                except Exception as e:
                    log_warning(f"Could not click radio: {e}")

            if target_digits:
                opt_digits = re.sub(r'[^\d.]', '', combined)
                if opt_digits == target_digits:
                    try:
                        await el.click()
                        await human_delay(0.5, 1.0)
                        log_info(f"Clicked radio matching digits '{target_digits}': value={val}")
                        return True
                    except Exception as e:
                        log_warning(f"Could not click radio: {e}")

        for elem in radio_elems:
            el = elem['element']
            info = elem['info']
            val = info.get('value', '').lower().strip()
            if target_lower in val or val in target_lower:
                try:
                    await el.click()
                    await human_delay(0.5, 1.0)
                    log_info(f"Clicked radio partial match '{target}': value={val}")
                    return True
                except Exception as e:
                    log_warning(f"Could not click radio: {e}")
        return False

    async def _fill_cover_letter(self, job: dict) -> bool:
        cover_letter_selectors = [
            'textarea[name*="cover"]',
            'textarea[name*="message"]',
            'textarea[placeholder*="cover"]',
            'textarea[placeholder*="message"]',
            'textarea[id*="cover"]',
            'textarea[id*="message"]',
            'textarea[aria-label*="cover"]',
            'textarea[aria-label*="message"]',
        ]

        for frame in self._get_frames():
            for selector in cover_letter_selectors:
                try:
                    textarea = frame.locator(selector).first
                    if await textarea.is_visible(timeout=2000):
                        placeholder = await textarea.get_attribute('placeholder') or ''
                        aria_label = await textarea.get_attribute('aria-label') or ''
                        combined = f"{placeholder} {aria_label}".lower()
                        if 'cover' in combined or 'message' in combined:
                            cover_text = self._generate_cover_letter(job)
                            await textarea.fill(cover_text)
                            await human_delay(0.5, 1.0)
                            log_info("Cover letter filled")
                            return True
                except Exception:
                    continue

            try:
                all_textareas = await frame.query_selector_all('textarea')
                for ta in all_textareas:
                    if await ta.is_visible(timeout=1000):
                        placeholder = await ta.get_attribute('placeholder') or ''
                        aria_label = await ta.get_attribute('aria-label') or ''
                        combined = f"{placeholder} {aria_label}".lower()
                        if 'cover' in combined or 'message' in combined:
                            cover_text = self._generate_cover_letter(job)
                            await ta.fill(cover_text)
                            await human_delay(0.5, 1.0)
                            log_info("Cover letter filled via fallback")
                            return True
            except Exception as e:
                log_warning(f"Cover letter fallback failed: {e}")
        return False

    async def _submit_form(self):
        screening_save_selectors = [
            'button:has-text("Save")',
            'button:has-text("Submit")',
            '[class*="ssrc"] button:has-text("Save")',
            '[class*="ssrc"] button:has-text("Submit")',
        ]
        for frame in self._get_frames():
            for selector in screening_save_selectors:
                try:
                    btn = frame.locator(selector).first
                    if await btn.is_visible(timeout=2000):
                        cls = await btn.get_attribute('class') or ''
                        if 'save-job-button' in cls:
                            continue
                        await random_mouse_move(self.page)
                        await btn.click()
                        await human_delay(2, 3)
                        log_info("Clicked screening form Save/Submit")
                        break
                except Exception:
                    continue

        submit_selectors = [
            'button:has-text("Submit")',
            'button:has-text("Apply")',
            'button:has-text("Send")',
            'button:has-text("Continue")',
            'button:has-text("Save")',
            'input[type="submit"]',
            'button[type="submit"]',
            '.submit-btn',
            'button.submit',
            'button.primary',
            'button.btn-primary',
        ]

        for attempt in range(3):
            for frame in self._get_frames():
                for selector in submit_selectors:
                    try:
                        submit_btn = frame.locator(selector).first
                        if await submit_btn.is_visible(timeout=2000):
                            cls = await submit_btn.get_attribute('class') or ''
                            if 'save-job-button' in cls:
                                continue
                            await random_mouse_move(self.page)
                            await submit_btn.click()
                            await human_delay(3, 5)
                            log_success("Form submitted successfully")
                            return True
                    except Exception:
                        continue
            await human_delay(2, 3)
        log_warning("No visible submit/apply button found after retries")
        return False

    async def _check_application_success(self) -> bool:
        success_indicators = [
            "application submitted",
            "applied successfully",
            "thank you for applying",
            "your application has been",
            "application sent",
            "already applied",
            "successfully applied",
            "application completed",
            "you have successfully applied",
            "view application",
            "application is successful",
            "congratulations",
            "successfully submitted",
            "applied on",
            "application received",
        ]

        # Check in common success containers first for speed
        containers = [
            '.success-msg', '.applied-msg', '.toast-success', 
            '.application-status', '#status-message', '.msg-container'
        ]
        for frame in self._get_frames():
            for sel in containers:
                try:
                    el = frame.locator(sel).first
                    if await el.is_visible(timeout=500):
                        text = (await el.inner_text()).lower()
                        if any(ind in text for ind in success_indicators):
                            return True
                except Exception:
                    continue

            # Fallback to full body check
            try:
                page_text = (await frame.inner_text("body")).lower()
                if any(ind in page_text for ind in success_indicators):
                    return True
                if ' applied ' in f" {page_text} " and 'not applied' not in page_text:
                    return True
            except Exception:
                pass

            try:
                # Check if an "Applied" button exists - definitive proof
                applied_btn = frame.locator('button:has-text("Applied"), button:has-text("Already Applied"), text="Already Applied"').first
                if await applied_btn.is_visible(timeout=1000):
                    return True
            except Exception:
                pass

        return False

    def _generate_cover_letter(self, job: dict) -> str:
        profile = self.profile
        candidate = profile.get("candidate", {})
        narrative = profile.get("narrative", {})
        superpowers = narrative.get("superpowers", [])

        name = candidate.get("full_name", "Candidate")
        headline = narrative.get("headline", "")
        exit_story = narrative.get("exit_story", "")
        role = job.get("title", "the position")
        company = job.get("company", "your company")

        cover = (
            f"Dear Hiring Manager,\n\n"
            f"I am writing to express my strong interest in the {role} position at {company}. "
        )

        if headline:
            cover += f"As a {headline.lower()}, "

        if exit_story:
            cover += f"{exit_story} "

        if superpowers:
            cover += f"My key strengths include: {', '.join(superpowers[:3]).lower()}. "

        cover += (
            f"\n\nI believe my experience and skills make me a strong fit for this role, "
            f"and I would welcome the opportunity to discuss how I can contribute to {company}'s success.\n\n"
            f"Best regards,\n{name}"
        )

        return cover

    async def auto_apply(
        self,
        keywords: list[str] | None = None,
        location: str = "",
        max_jobs: int = 0,
        dry_run: bool = False,
        fresh_only: bool = True,
        sort_by_date: bool = True,
    ) -> list[dict]:
        requested_max_jobs = max_jobs

        if not keywords:
            primary = self.profile.get("target_roles", {}).get("primary", [])
            secondary = self.profile.get("target_roles", {}).get("secondary", [])
            # Use a broader keyword list by default so targets like "--max-jobs 50" have enough supply.
            keywords = list(primary) + [k for k in secondary if k not in primary]

        if not max_jobs:
            max_jobs = self.profile.get("search_preferences", {}).get("max_jobs_per_search", 50)

        # If user explicitly requested a target (via CLI `--max-jobs`), treat it as the
        # session cap as well, even if `max_applications_per_day` in profile.yaml is lower.
        if requested_max_jobs and requested_max_jobs > 0:
            self.max_per_day = requested_max_jobs

        # Handle early access first
        try:
            await self.handle_early_access()
        except Exception as e:
            log_warning(f"Early access handling skipped: {e}")

        target_candidate_pool = 0
        if max_jobs and max_jobs > 0:
            # We need more candidates than the target because some will be skipped/failed/external/already applied.
            target_candidate_pool = min(max(150, max_jobs * 15), 2000)

        max_pages = self.profile.get("search_preferences", {}).get("max_pages_per_search", 5)
        try:
            max_pages = int(max_pages)
        except Exception:
            max_pages = 5
        max_pages = max(1, min(max_pages, 25))

        all_jobs: list[dict] = []

        if location:
            search_locations = [location]
        else:
            configured_locations = [
                str(city).strip()
                for city in self.profile.get("location", {}).get("preferred_cities", [])
                if str(city).strip()
            ]
            search_locations = configured_locations or [""]

        if max_jobs and max_jobs > 0:
            log_info(
                f"Target: {max_jobs} successful applies. Collecting up to {target_candidate_pool} candidates "
                f"across {len(keywords)} keyword(s) × {len(search_locations)} location(s), "
                f"{max_pages} page(s) each..."
            )

        for keyword in keywords:
            for search_location in search_locations:
                jobs = await self.search_jobs(
                    keyword,
                    search_location,
                    fresh_only=fresh_only,
                    sort_by_date=sort_by_date,
                    max_pages=max_pages,
                    max_results=target_candidate_pool,
                )
                all_jobs.extend(jobs)

                if target_candidate_pool and len(all_jobs) >= target_candidate_pool:
                    break
            if target_candidate_pool and len(all_jobs) >= target_candidate_pool:
                break

        seen_urls = set()
        unique_jobs = []
        for job in all_jobs:
            url = job.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_jobs.append(job)
        all_jobs = unique_jobs

        log_info(f"Total unique jobs found: {len(all_jobs)}")

        filtered_jobs = self._filter_jobs(all_jobs)
        log_info(f"Jobs after filtering: {len(filtered_jobs)}")
        if max_jobs and max_jobs > 0 and len(filtered_jobs) < max_jobs:
            log_warning(
                f"Not enough eligible jobs to reach target {max_jobs} (only {len(filtered_jobs)} after filtering). "
                f"Try increasing 'search_preferences.max_pages_per_search' or loosening filters/locations."
            )

        if dry_run:
            log_info("DRY RUN - Showing jobs without applying:")
            for i, job in enumerate(filtered_jobs[:max_jobs], 1):
                log_info(
                    f"  {i}. {job['company']} | {job['title']} | {job['location']} | {job['salary']}"
                )
            return filtered_jobs[:max_jobs]

        # Keep scanning past company-site-only listings so --max-jobs counts successful attempts only
        results = []
        successful_count = 0
        for job in filtered_jobs:
            if successful_count >= max_jobs:
                log_info(f"Reached target of {max_jobs} successful applications.")
                break
            
            if self.session_applied >= self.max_per_day:
                log_warning(f"Daily application limit reached ({self.max_per_day})")
                break

            # Default to skipping "Apply on company site" listings (they don't count as applied).
            result = await self.apply_to_job(job, skip_external=True)
            results.append(result)
            
            # Only count TRUE successful applications (status == "applied")
            if result.get("status") == "applied":
                successful_count += 1
                log_success(f"Progress: {successful_count}/{max_jobs} successful applications completed")

        if max_jobs > 0:
            log_success(f"Session complete. Successfully applied to {successful_count}/{max_jobs} applications.")
            if successful_count < max_jobs:
                counts: dict[str, int] = {}
                for r in results:
                    status = str(r.get("status") or "unknown")
                    counts[status] = counts.get(status, 0) + 1
                breakdown = ", ".join(f"{k}={v}" for k, v in sorted(counts.items()))
                log_warning(f"Target not reached ({successful_count}/{max_jobs}). Breakdown: {breakdown}")
        else:
            log_success(f"Session complete. Successfully applied to {successful_count} jobs out of {len(results)} attempts.")

        return results

    def _filter_jobs(self, jobs: list[dict]) -> list[dict]:
        target = self.profile.get("target_roles", {})
        positive_kw = [k.lower() for k in target.get("keywords_positive", [])]
        negative_kw = [k.lower() for k in target.get("keywords_negative", [])]
        seniority = [s.lower() for s in target.get("seniority", [])]
        preferred_cities = [c.lower() for c in self.profile.get("location", {}).get("preferred_cities", [])]
        min_ctc = extract_salary_lakhs(self.profile.get("compensation", {}).get("minimum_ctc", ""))

        filtered = []
        for job in jobs:
            title_lower = job.get("title", "").lower()
            tags_lower = " ".join(job.get("tags", [])).lower()
            desc_lower = job.get("description", "").lower()
            combined = f"{title_lower} {tags_lower} {desc_lower}"

            has_negative = any(nk in combined for nk in negative_kw)
            if has_negative:
                continue

            location_lower = job.get("location", "").lower()
            if preferred_cities and location_lower:
                location_match = any(city in location_lower for city in preferred_cities)
                if not location_match and "remote" not in location_lower:
                    if self.profile.get("location", {}).get("remote_preference") != "remote_first":
                        continue

            has_positive = any(pk in combined for pk in positive_kw) if positive_kw else True
            has_seniority = any(s in title_lower for s in seniority) if seniority else True

            if not has_positive and not has_seniority:
                continue

            if min_ctc > 0:
                salary_lakhs = extract_salary_lakhs(job.get("salary", ""))
                if 0 < salary_lakhs < min_ctc:
                    continue

            # Filter out "early" (old) jobs - e.g. 30+ days ago or >= 3 weeks
            posted = job.get("posted", "").lower()
            if any(x in posted for x in ["30+", "15+", "3 week", "21 day"]):
                continue

            filtered.append(job)

        return filtered

    async def get_applied_jobs(self) -> list[dict]:
        log_step("Fetching applied jobs from Naukri...")

        try:
            await self.page.goto(
                f"{self.NAUKRI_BASE}/myapply/historypage",
                wait_until="domcontentloaded",
            )
            await human_delay(3, 5)

            await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await human_delay(2, 3)

            applied = []

            cards = await self.page.query_selector_all(
                '.jdTupleContainer, .ot__jdTupleContainer, [class*="jdTupleContainer"]'
            )
            if not cards:
                cards = await self.page.query_selector_all(
                    '.jobTuple, .job-card, .appliedJobsTuple, [data-job-id], [class*="jobTuple"], [class*="job-card"]'
                )

            if not cards:
                for fallback_url in [
                    f"{self.NAUKRI_BASE}/mnjuser/homepage",
                    f"{self.NAUKRI_BASE}/myapply/historypage",
                ]:
                    await self.page.goto(fallback_url, wait_until="domcontentloaded")
                    await human_delay(2, 4)
                    cards = await self.page.query_selector_all(
                        '.jdTupleContainer, .ot__jdTupleContainer, [class*="jdTupleContainer"], .jobTuple, .job-card, .appliedJobsTuple, [data-job-id], [class*="jobTuple"], [class*="job-card"]'
                    )
                    if cards:
                        break

            for card in cards:
                try:
                    title_parts = []
                    title_els = await card.query_selector_all('a, [class*="title"], [class*="Title"]')
                    for el in title_els[:3]:
                        text = (await el.inner_text()).strip()
                        if text and len(text) > 5:
                            title_parts.append(text)
                    title = title_parts[0] if title_parts else ""

                    if not title:
                        all_text = (await card.inner_text()).strip()
                        lines = [l.strip() for l in all_text.split("\n") if l.strip()]
                        title = lines[0] if lines else ""

                    company_el = await card.query_selector(
                        '.comp-name, [class*="comp"], [class*="company"]'
                    )
                    company = (await company_el.inner_text()).strip() if company_el else ""

                    if not company:
                        all_text = (await card.inner_text()).strip()
                        lines = [l.strip() for l in all_text.split("\n") if l.strip()]
                        if len(lines) > 1:
                            company = lines[1]

                    status = "Applied"
                    status_el = await card.query_selector(
                        '.apply-status, .statusCont, [class*="status"], .app-status, .application-status'
                    )
                    if status_el:
                        status_text = (await status_el.inner_text()).strip()
                        lower = status_text.lower()
                        if "shortlist" in lower or "selected" in lower:
                            status = "Shortlisted"
                        elif "rejected" in lower:
                            status = "Rejected"
                        elif "interview" in lower:
                            status = "Interview"
                        elif "viewed" in lower or "seen" in lower:
                            status = "Viewed"
                        elif "applied" in lower or "application sent" in lower:
                            status = "Applied"
                        else:
                            status = status_text

                    date_el = await card.query_selector(
                        '.applied-date, .date, .applied-on, .appliedOn, .applied-text, .app-date'
                    )
                    applied_date = (await date_el.inner_text()).strip() if date_el else ""
                    if not applied_date:
                        all_text = (await card.inner_text()).strip()
                        date_match = re.search(r'application (sent|submitted)\s*(today|\d{1,2}\s*\w+|\d{1,2}\s*ago)', all_text, re.I)
                        if date_match:
                            applied_date = date_match.group(0)

                    raw_text = (await card.inner_text()).strip()
                    source = "naukri"
                    if "external" in raw_text.lower() or "external site" in raw_text.lower() or "apply on external" in raw_text.lower():
                        source = "external"

                    url = ""
                    link_el = await card.query_selector('a[href*="job"]')
                    if not link_el:
                        link_el = await card.query_selector('a')
                    if link_el:
                        href = await link_el.get_attribute('href')
                        if href:
                            url = href.strip()
                            if url.startswith('/'):
                                url = f"https://www.naukri.com{url}"

                    job_id = await card.get_attribute('data-job-id')
                    if not job_id and url:
                        match = re.search(r'/([A-Za-z0-9_-]+)\?\w*', url)
                        job_id = match.group(1) if match else ""

                    if title:
                        applied.append({
                            "title": title[:80],
                            "company": company[:40],
                            "status": status,
                            "applied_date": applied_date,
                            "url": url,
                            "job_id": job_id or "",
                            "source": source,
                        })
                except Exception:
                    continue

            log_success(f"Found {len(applied)} applied jobs on Naukri")
            return applied

        except Exception as e:
            log_error(f"Error fetching applied jobs: {e}")
            return []

    def get_session_stats(self) -> dict:
        return {
            "date": self.session_date,
            "applied": self.session_applied,
            "max_per_day": self.max_per_day,
            "remaining": max(0, self.max_per_day - self.session_applied),
        }
