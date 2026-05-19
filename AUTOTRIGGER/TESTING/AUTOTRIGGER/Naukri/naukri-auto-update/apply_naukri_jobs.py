import os
import time
import json
from datetime import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

BASE_DIR = Path(__file__).resolve().parent
AUTH_PATH = BASE_DIR / "auth.json"
JOB_FILTER_PATH = BASE_DIR / "job_filter.json"
RECOMMENDED_JOBS_CLASSIFICATION_PATH = BASE_DIR / "recommended_jobs_apply_classification.json"
RECOMMENDED_JOBS_DIRECT_APPLY_PATH = BASE_DIR / "recommended_jobs_direct_apply.json"
RECOMMENDED_JOBS_APPLY_ON_SITE_PATH = BASE_DIR / "recommended_jobs_apply_on_site.json"
LOGIN_URL = "https://www.naukri.com/nlogin/login"
HOME_URL = "https://www.naukri.com"


def wait_for_navigation(page):
    try:
        page.wait_for_load_state("networkidle", timeout=15000)
    except PlaywrightTimeoutError:
        pass


def is_login_page(page):
    url = page.url.lower()
    if "nlogin" in url or "login" in url:
        return True
    return bool(page.query_selector("input#usernameField, input[name='username'], input#passwordField"))


def login_with_credentials(page):
    email = os.getenv("NAUKRI_EMAIL")
    password = os.getenv("NAUKRI_PASSWORD")
    if not email or not password:
        raise EnvironmentError("Set NAUKRI_EMAIL and NAUKRI_PASSWORD or use auth.json saved session.")

    print("Logging in using NAUKRI_EMAIL / NAUKRI_PASSWORD")
    page.goto(LOGIN_URL)
    page.wait_for_selector("#usernameField", timeout=30000)
    page.fill("#usernameField", email)
    page.fill("#passwordField", password)
    page.click("button[type='submit']")
    page.wait_for_timeout(7000)
    wait_for_navigation(page)


def open_recommended_jobs(page):
    print("Opening Naukri home page and locating Recommended Jobs")
    page.goto(HOME_URL)
    wait_for_navigation(page)
    page.wait_for_timeout(3000)

    for _ in range(2):
        try:
            recommended = page.query_selector("section:has-text('Recommended Jobs')")
            if recommended:
                print("Located Recommended Jobs section on home page.")
                return True
        except Exception:
            pass

        jobs_link = page.query_selector("a:has-text('Jobs'), a[title='Jobs']")
        if jobs_link:
            try:
                jobs_link.click()
                wait_for_navigation(page)
                page.wait_for_timeout(2000)
            except Exception:
                pass

    try:
        recommended = page.query_selector("section:has-text('Recommended Jobs')")
        if recommended:
            print("Located Recommended Jobs section after navigating to Jobs.")
            return True
    except Exception:
        pass

    print("Could not locate Recommended Jobs section on the page.")
    return False


def get_job_cards(page):
    selectors = [
        "article[class*='jobTuple']",
        "div[class*='jobTuple']",
        "[data-jk]",
        "[data-job-id]",
        "li[data-job-id]",
        "div[class*='jobListing']",
    ]
    for selector in selectors:
        cards = page.query_selector_all(selector)
        if cards:
            print(f"Found {len(cards)} job cards with selector: {selector}")
            return cards
    return []


def get_text_from_element(element):
    text = (element.inner_text() or "").strip()
    if text:
        return text
    return (element.get_attribute("aria-label") or element.get_attribute("title") or "").strip()


def extract_job_title(card):
    for selector in ["h2 a.title", "a.title", ".title", "h2", "a.jobTitle"]:
        element = card.query_selector(selector)
        if element:
            title = get_text_from_element(element)
            if title:
                return title
    raw = card.inner_text() or ""
    return raw.splitlines()[0].strip() if raw else ""


def extract_job_company(card):
    for selector in [
        ".companyInfo .companyName",
        ".company",
        ".company-name",
        "span.comp-name",
        "a.company",
        "p.company",
    ]:
        element = card.query_selector(selector)
        if element:
            company = get_text_from_element(element)
            if company:
                return company
    return "Unknown company"


def extract_job_link(card):
    for selector in [
        "h2 a.title",
        "a.title",
        "a.jobTitle",
        "a[href*='/view-job/']",
        "a[href*='/job-listings']",
    ]:
        element = card.query_selector(selector)
        if element:
            href = element.get_attribute("href")
            if href:
                if href.startswith("/"):
                    return "https://www.naukri.com" + href
                return href
    return None


def get_open_job_click_element(card):
    selectors = [
        "h2 a.title",
        "a.title",
        "a.jobTitle",
        "a[href*='/view-job/']",
        "a[href*='/job-listings']",
        "a > span",
        "span.jobTitle",
        "span.title",
    ]
    for selector in selectors:
        element = card.query_selector(selector)
        if not element:
            continue
        try:
            if not element.is_visible():
                continue
        except Exception:
            continue
        text = get_text_from_element(element).lower()
        if "review" in text or "ambition" in text:
            continue
        return element
    return None


def get_apply_button_text_from_job_page(page):
    candidates = page.query_selector_all("button, a")
    for element in candidates:
        try:
            if not element.is_visible():
                continue
        except Exception:
            continue
        text = get_text_from_element(element)
        if not text:
            continue
        if "apply" in text.lower():
            return text
    return "N/A"


def click_job_card_open_and_read_apply(page, card):
    open_element = get_open_job_click_element(card)
    if not open_element:
        return "N/A", None

    job_page = page
    try:
        with page.expect_popup(timeout=3000) as popup_info:
            open_element.click()
        job_page = popup_info.value
    except Exception:
        try:
            open_element.click()
        except Exception:
            return "N/A", None

    button_text = "N/A"
    final_url = None
    try:
        wait_for_navigation(job_page)
        job_page.wait_for_timeout(2000)
        button_text = get_apply_button_text_from_job_page(job_page)
        final_url = job_page.url
    except Exception:
        pass

    if job_page is page:
        try:
            page.go_back()
            wait_for_navigation(page)
            page.wait_for_timeout(2000)
        except Exception:
            pass
    else:
        job_page.close()

    return button_text, final_url


def load_job_filter():
    if not JOB_FILTER_PATH.exists():
        return {}
    try:
        return json.loads(JOB_FILTER_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def classify_apply_type(button_text: str):
    text = (button_text or "").strip().lower()
    if not text or text == "n/a":
        return "unclassified"
    if "company site" in text:
        return "apply_on_site"
    if "apply" in text:
        return "direct_apply"
    return "unclassified"


def now_timestamp():
    return datetime.now().isoformat(sep=" ", timespec="seconds")


def print_jobs_markdown_table(jobs):
    print("\n| # | Company | Job Title | Apply Type | Apply Button | Link |")
    print("|---:|---|---|---|---|---|")
    for idx, job in enumerate(jobs, start=1):
        company = (job.get("company") or "").replace("\n", " ").replace("|", "\\|").strip()
        title = (job.get("title") or "").replace("\n", " ").replace("|", "\\|").strip()
        apply_type = (job.get("apply_type") or "").strip()
        apply_button = (job.get("apply_button_text") or "").replace("\n", " ").replace("|", "\\|").strip()
        link = (job.get("link") or "").replace("|", "\\|").strip()
        print(f"| {idx} | {company} | {title} | {apply_type} | {apply_button} | {link} |")


def save_recommended_jobs(jobs):
    direct_apply = [j for j in jobs if j.get("apply_type") == "direct_apply"]
    apply_on_site = [j for j in jobs if j.get("apply_type") == "apply_on_site"]
    unclassified = [j for j in jobs if j.get("apply_type") == "unclassified"]

    RECOMMENDED_JOBS_DIRECT_APPLY_PATH.write_text(
        json.dumps(direct_apply, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    RECOMMENDED_JOBS_APPLY_ON_SITE_PATH.write_text(
        json.dumps(apply_on_site, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    RECOMMENDED_JOBS_CLASSIFICATION_PATH.write_text(
        json.dumps(
            {
                "direct_apply": direct_apply,
                "apply_on_site": apply_on_site,
                "unclassified": unclassified,
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def list_recommended_jobs(page, context):
    cards = get_job_cards(page)
    if not cards:
        print("No recommended jobs found with the current selectors.")
        return

    job_filter = load_job_filter()
    max_jobs = job_filter.get("max_jobs")
    try:
        max_jobs = int(max_jobs) if max_jobs is not None else None
    except Exception:
        max_jobs = None

    jobs = []
    total = len(cards) if max_jobs is None else min(len(cards), max_jobs)
    print(f"\nCollecting recommended jobs (max_jobs={max_jobs if max_jobs is not None else 'all'})...")
    for idx in range(total):
        cards = get_job_cards(page)
        if idx >= len(cards):
            break
        card = cards[idx]
        title = extract_job_title(card) or "Untitled job"
        company = extract_job_company(card)
        card_link = extract_job_link(card)
        button_text, opened_url = click_job_card_open_and_read_apply(page, card)
        link = opened_url or card_link
        apply_type = classify_apply_type(button_text)
        jobs.append(
            {
                "title": title,
                "company": company,
                "link": link,
                "apply_button_text": button_text,
                "apply_type": apply_type,
                "timestamp": now_timestamp(),
            }
        )

    print_jobs_markdown_table(jobs)
    save_recommended_jobs(jobs)
    print(
        f"\nSaved: {RECOMMENDED_JOBS_CLASSIFICATION_PATH.name}, "
        f"{RECOMMENDED_JOBS_DIRECT_APPLY_PATH.name}, "
        f"{RECOMMENDED_JOBS_APPLY_ON_SITE_PATH.name}"
    )


def create_context(browser):
    if AUTH_PATH.exists():
        return browser.new_context(storage_state=str(AUTH_PATH))
    return browser.new_context()


def main():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False)
        context = create_context(browser)

        page = context.new_page()
        if AUTH_PATH.exists():
            page.goto(HOME_URL)
            wait_for_navigation(page)
            if is_login_page(page):
                print("Saved session expired or invalid. Re-authenticating...")
                page.close()
                context.close()
                context = browser.new_context()
                page = context.new_page()
                login_with_credentials(page)
                context.storage_state(path=str(AUTH_PATH))
                print(f"Saved new session to {AUTH_PATH}")
        else:
            login_with_credentials(page)
            context.storage_state(path=str(AUTH_PATH))
            print(f"Saved new session to {AUTH_PATH}")

        if not open_recommended_jobs(page):
            print("Unable to reach Recommended Jobs section.")
            page.close()
            browser.close()
            return

        list_recommended_jobs(page, context)
        page.close()
        browser.close()


if __name__ == "__main__":
    main()
