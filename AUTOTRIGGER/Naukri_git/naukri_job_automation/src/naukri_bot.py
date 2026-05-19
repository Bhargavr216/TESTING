import asyncio
import asyncio
import os
import random
import re
import json
from datetime import datetime
from pathlib import Path

from playwright.async_api import async_playwright, Page, Browser, BrowserContext, Frame

from src.profile import load_profile, resolve_storage_state_path
from src.tracker import ApplicationTracker
from src.local_ai import LocalAIClient, LocalAIConfig
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
        self._local_ai: LocalAIClient | None = None
        self.session_applied = 0
        self.session_date = datetime.now().strftime("%Y-%m-%d")
        self.max_per_day = self.profile.get("search_preferences", {}).get(
            "max_applications_per_day", 30
        )
        self.apply_delay = self.profile.get("search_preferences", {}).get(
            "apply_delay_seconds", 15
        )
        # Track external/company site jobs
        self.external_jobs = []

    def _local_ai_client(self) -> LocalAIClient | None:
        cfg = self.profile.get("local_ai", {}) or {}
        enabled = bool(cfg.get("enabled", False))
        if not enabled:
            return None

        if self._local_ai:
            return self._local_ai

        provider = str(cfg.get("provider", "ollama") or "ollama").strip().lower()
        base_url = str(cfg.get("base_url", "http://127.0.0.1:11434") or "http://127.0.0.1:11434").strip()
        model = str(cfg.get("model", "llama3.1:8b") or "llama3.1:8b").strip()
        timeout_seconds = int(cfg.get("timeout_seconds", 20) or 20)
        temperature = float(cfg.get("temperature", 0.2) or 0.2)
        max_tokens = int(cfg.get("max_tokens", 256) or 256)

        self._local_ai = LocalAIClient(
            LocalAIConfig(
                enabled=True,
                provider=provider,
                base_url=base_url,
                model=model,
                timeout_seconds=timeout_seconds,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        )
        return self._local_ai

    def _local_ai_mode(self) -> str:
        cfg = self.profile.get("local_ai", {}) or {}
        mode = str(cfg.get("mode", "fallback") or "fallback").strip().lower()
        return mode if mode in ("fallback", "always") else "fallback"

    def _ai_context(self, screening: dict, compensation: dict) -> dict:
        candidate = dict(self.profile.get("candidate", {}) or {})
        # Never include credentials or storage_state data in model context.
        candidate.pop("password", None)
        candidate.pop("storage_state_path", None)

        return {
            "candidate": {
                "full_name": candidate.get("full_name", ""),
                "email": candidate.get("email", ""),
                "phone": candidate.get("phone", ""),
                "location": candidate.get("location", ""),
                "current_company": candidate.get("current_company", ""),
                "current_role": candidate.get("current_role", ""),
                "experience_years": candidate.get("experience_years", screening.get("total_experience_years", "")),
                "notice_period_days": candidate.get("notice_period_days", ""),
                "github": candidate.get("github", ""),
                "linkedin": candidate.get("linkedin", ""),
            },
            "screening_answers": screening,
            "compensation": compensation,
            "target_roles": self.profile.get("target_roles", {}),
            "location_preferences": self.profile.get("location", {}),
            "narrative": self.profile.get("narrative", {}),
        }

    def _chatbot_custom_answer(self, *, kind: str, question_text: str) -> str | list[str] | None:
        """
        Optional user-defined overrides from config/profile.yaml:

        chatbot_custom_answers:
          - kind: "text" | "radio" | "checkbox" | "any"
            match_type: "contains" | "regex" | "exact"
            match: "some text or regex"
            answer: "Yes" | "No" | "Bangalore" | "5" | ["Bangalore", "Remote"]
        """
        rules = self.profile.get("chatbot_custom_answers", []) or []
        if not isinstance(rules, list):
            return None

        qt = str(question_text or "").strip()
        qt_lower = qt.lower()
        kind_lower = str(kind or "any").lower().strip()

        for rule in rules:
            if not isinstance(rule, dict):
                continue

            rule_kind = str(rule.get("kind", "any") or "any").lower().strip()
            if rule_kind not in ("any", kind_lower):
                continue

            match_type = str(rule.get("match_type", "contains") or "contains").lower().strip()
            match = str(rule.get("match", "") or "").strip()
            if not match:
                continue

            ok = False
            if match_type == "exact":
                ok = qt_lower == match.lower()
            elif match_type == "regex":
                try:
                    ok = bool(re.search(match, qt_lower))
                except Exception:
                    ok = False
            else:  # contains
                ok = match.lower() in qt_lower

            if not ok:
                continue

            ans = rule.get("answer", None)
            if isinstance(ans, (str, list)):
                return ans

        return None

    async def _ai_decide_chat(self, *, kind: str, question: str, options: list[dict] | None, screening: dict, compensation: dict) -> dict | None:
        client = self._local_ai_client()
        if not client:
            return None

        payload = {
            "kind": kind,
            "question": question,
            "options": [{"label": o.get("label", ""), "value": o.get("value", ""), "id": o.get("id", "")} for o in (options or [])],
            "profile": self._ai_context(screening, compensation),
            "output_format": {
                "text": {"type": "text", "answer": "string"},
                "radio": {"type": "radio", "choice": "string"},
                "checkbox": {"type": "checkbox", "choices": ["string"]},
            },
        }

        return await asyncio.to_thread(client.decide, payload)

    def _match_choice_to_option_index(self, choice: str, options: list[dict]) -> int:
        c = str(choice or "").strip().lower()
        if not c:
            return -1
        c_digits = re.sub(r"[^\d.]", "", c)

        for i, opt in enumerate(options):
            combined = f"{opt.get('label','')} {opt.get('value','')}".lower().strip()
            if combined == c:
                return i

        for i, opt in enumerate(options):
            combined = f"{opt.get('label','')} {opt.get('value','')}".lower().strip()
            if c in combined or combined in c:
                return i

        if c_digits:
            for i, opt in enumerate(options):
                combined = f"{opt.get('label','')} {opt.get('value','')}".lower().strip()
                o_digits = re.sub(r"[^\d.]", "", combined)
                if o_digits and o_digits == c_digits:
                    return i

        return -1

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

    async def _ensure_browser_session(self) -> bool:
        """
        Ensure Playwright browser+page exist and are not closed.
        If the browser/page were closed unexpectedly, restart and re-login.
        """
        def _looks_closed_error(err: Exception) -> bool:
            msg = str(err or "").lower()
            return "has been closed" in msg or "target page" in msg and "closed" in msg

        try:
            if not self.browser or not self.context or not self.page:
                await self.start()
                return await self.login()

            # Page.is_closed() is a sync method.
            try:
                if self.page.is_closed():
                    raise RuntimeError("Target page has been closed")
            except Exception as e:
                if _looks_closed_error(e):
                    raise

            try:
                await self.page.evaluate("() => 1")
                return True
            except Exception as e:
                if _looks_closed_error(e):
                    raise
                return True
        except Exception as e:
            if not _looks_closed_error(e):
                log_warning(f"Browser session check failed (continuing): {e}")
                return True

            log_warning("Browser/page closed unexpectedly; restarting session...")
            try:
                await self.close()
            except Exception:
                pass
            await self.start()
            return await self.login()

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
                await human_delay(2, 3)

                # Look for Early access section
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
            # Click "View all" to open the full early access page
            view_all = early_section.locator('a.spc__view-all, a:has-text("View all")').first
            if await view_all.is_visible(timeout=3000):
                await view_all.click()
                await human_delay(2, 3)
                log_info("Clicked 'View all' for early access roles")

                # Now we're on the early access page - scroll down and click ALL "Share Interest" buttons
                share_selector = 'button.unshared, button:has-text("Share interest")'
                
                clicked_count = 0
                max_scrolls = 20
                
                for scroll_attempt in range(max_scrolls):
                    # Find all visible "Share Interest" buttons
                    share_buttons = await self.page.query_selector_all(share_selector)
                    
                    if not share_buttons:
                        log_info(f"No more Share Interest buttons found after {clicked_count} clicks")
                        break
                    
                    # Click all visible buttons
                    clicked_this_round = False
                    for btn in share_buttons:
                        try:
                            if not await btn.is_visible():
                                continue
                            
                            # Scroll button into view
                            await btn.scroll_into_view_if_needed()
                            await human_delay(0.3, 0.5)
                            
                            # Click the button
                            try:
                                await btn.click(force=True, timeout=3000)
                            except Exception:
                                await self.page.evaluate("(el) => el.click()", btn)
                            
                            clicked_count += 1
                            clicked_this_round = True
                            log_success(f"  Shared interest #{clicked_count}")
                            await human_delay(0.5, 1)
                            
                        except Exception as e:
                            log_warning(f"  Error clicking Share Interest button: {e}")
                            continue
                    
                    if not clicked_this_round:
                        # No buttons clicked this round, scroll down to load more
                        await self.page.evaluate("window.scrollBy(0, 500)")
                        await human_delay(1, 2)
                    else:
                        # Buttons were clicked, scroll a bit to see if there are more
                        await self.page.evaluate("window.scrollBy(0, 300)")
                        await human_delay(0.5, 1)
                
                if clicked_count > 0:
                    log_success(f"Shared interest for {clicked_count} early access roles")
                    return True
                else:
                    log_info("No Share Interest buttons found on the page")
                    return False
            else:
                log_warning("Could not find 'View all' link in Early Access section")
                return False
        except Exception as e:
            log_error(f"Error handling early access: {e}")
            return False

        return False

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
                # Give Naukri extra time to render (especially in non-headless mode)
                await human_delay(2, 3)
                if await self._detect_logged_in():
                    log_success("Already logged in (session detected after wait)")
                    return True
                # If we're not on a login page and auth.json exists, trust the session
                auth_path = resolve_storage_state_path(self.profile)
                if auth_path.exists():
                    log_info("Not on login page and auth.json exists — assuming session valid")
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

    async def search_jobs(self, keyword: str, location: str = "", experience: str = "", fresh_only: bool = False, sort_by_date: bool = True) -> list[dict]:
        log_step(f"Searching jobs: keyword='{keyword}', location='{location}'")

        search_slug = re.sub(r"[^a-z0-9]+", "-", keyword.lower()).strip("-")
        search_url = f"{self.NAUKRI_BASE}/{search_slug}-jobs"
        if location:
            loc_slug = re.sub(r"[^a-z0-9]+", "-", location.lower()).strip("-")
            search_url += f"-in-{loc_slug}"

        all_jobs = []

        max_pages = int(self.profile.get("search_preferences", {}).get("max_search_pages", 3) or 3)
        max_pages = max(1, min(max_pages, 10))

        # Search multiple pages to get more jobs (3 pages ~= 60 jobs)
        for page_num in range(1, max_pages + 1):
            page_url = search_url if page_num == 1 else f"{search_url}-{page_num}"
             
            try:
                await self.page.goto(page_url, wait_until="domcontentloaded")
                await human_delay(1, 2)
            except Exception as e:
                log_warning(f"Could not load page {page_num}: {e}")
                break

            # Only apply filters on first page
            if page_num == 1:
                if sort_by_date:
                    try:
                        # Click sort button: button#filter-sort
                        sort_btn = self.page.locator('button#filter-sort').first
                        if await sort_btn.is_visible(timeout=5000):
                            await sort_btn.click()
                            await human_delay(1, 2)
                            
                            # Click "Date" from dropdown: ul[data-filter-id="sort"] li[title="Date"] a
                            date_option = self.page.locator('ul[data-filter-id="sort"] li[title="Date"] a').first
                            if await date_option.is_visible(timeout=3000):
                                await date_option.click()
                                await human_delay(2, 4)
                                log_info("Sorted results by Date (Newest first)")
                            else:
                                # Fallback by data-id
                                date_option2 = self.page.locator('a[data-id="filter-sort-f"]').first
                                if await date_option2.is_visible(timeout=2000):
                                    await date_option2.click()
                                    await human_delay(2, 4)
                                    log_info("Sorted results by Date (fallback)")
                                else:
                                    log_warning("Could not find 'Date' option in sort menu")
                        else:
                            log_warning("Could not find sort button")
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

            page_jobs = await self._extract_job_listings()
            if not page_jobs:
                log_info(f"No more jobs found on page {page_num}, stopping pagination")
                break
                
            all_jobs.extend(page_jobs)
            log_info(f"Page {page_num}: Found {len(page_jobs)} jobs (Total so far: {len(all_jobs)})")
            
            # Stop if we have enough jobs (100+ should be plenty)
            if len(all_jobs) >= 100:
                log_info(f"Collected {len(all_jobs)} jobs, stopping pagination")
                break

        log_success(f"Found {len(all_jobs)} total jobs for '{keyword}'")
        return all_jobs

    async def _extract_job_listings(self) -> list[dict]:
        jobs = []
        try:
            await self.page.wait_for_selector(
                'div.srp-jobtuple-wrapper, [data-job-id]',
                timeout=15000,
            )
        except Exception:
            log_warning("No job listings found on page")
            return jobs

        job_cards = await self.page.query_selector_all(
            'div.srp-jobtuple-wrapper'
        )

        for card in job_cards:
            try:
                job = await self._parse_job_card(card)
                if job:
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

        # Filter job title against target roles (primary + secondary) early to avoid page loads.
        job_title_lower = job.get("title", "").lower()
        target_roles_cfg = self.profile.get("target_roles", {}) or {}
        target_roles_primary = [r.lower() for r in target_roles_cfg.get("primary", [])]
        target_roles_secondary = [r.lower() for r in target_roles_cfg.get("secondary", [])]
        target_roles_all = [r for r in (target_roles_primary + target_roles_secondary) if r]
        title_matches_role = True
        if target_roles_all:
            title_matches_role = any(role in job_title_lower for role in target_roles_all)

        if not title_matches_role:
            result["status"] = "skipped"
            result["error"] = f"Job title '{job.get('title','')}' doesn't match target roles"
            log_info(f"Skipping {job.get('title','')} - title doesn't match target roles")
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
            await human_delay(1, 2)

            # Gather Job match details first
            match_details = await self._extract_match_details()
            job["match_details"] = match_details
            
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
            
            # Positive keywords are a signal for fit, but don't hard-skip if the title already matches a target role.
            if keywords_positive and not any(pos_kw in full_job_text for pos_kw in keywords_positive):
                log_info(f"Job missing positive keywords (continuing): {job.get('title','')[:60]}")
            
            # Check for external apply button first
            company_site_btn = self.page.locator(
                '#company-site-button, button.company-site-button'
            ).first
            try:
                if await company_site_btn.is_visible(timeout=3000):
                    # Store external job details with posted date
                    self.external_jobs.append({
                        "title": job.get("title", ""),
                        "company": job.get("company", ""),
                        "url": job.get("url", ""),
                        "location": job.get("location", ""),
                        "salary": job.get("salary", ""),
                        "posted": job.get("posted", ""),
                        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    })
                    
                    if skip_external:
                        result["status"] = "external_apply"
                        result["error"] = "Apply on company site - skipping"
                        log_info(f"Skipping {job['title']} (external apply) - stored in external_jobs.json")
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
            await human_delay(2, 3)

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
                        await human_delay(1, 2)
                        await apply_btn.click()
                        await human_delay(2, 3)
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

        # Reduced delay for faster applications
        delay = self.apply_delay + random.uniform(-1, 2)
        delay = max(2, delay)  # Minimum 2 seconds
        log_info(f"Waiting {delay:.0f}s before next application...")
        await human_delay(delay, delay + 1)

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

    async def _click_chat_skip_question_button(self) -> bool:
        skip_selectors = [
            'button:has-text("Skip")',
            'a:has-text("Skip")',
            'div[role="button"]:has-text("Skip")',
            'span:has-text("Skip")',
            'li:has-text("Skip")',
            'text=/skip(\\s+the)?\\s+question/i',
        ]
        for sel in skip_selectors:
            try:
                loc = self.page.locator(sel).first
                if await loc.is_visible(timeout=750):
                    await loc.click()
                    log_info(f"Clicked chat Skip button via '{sel}'")
                    return True
            except Exception:
                continue

        try:
            clicked_text = await self.page.evaluate("""() => {
                const root =
                    document.querySelector('._chatBotContainer') ||
                    document.querySelector('.chatbot_Drawer') ||
                    document.querySelector('div[class*="chatbot_MessageContainer"]') ||
                    document.querySelector('div.chatbot_DrawerContentWrapper') ||
                    document;

                const targets = [
                    'skip the question',
                    'skip question',
                    'skip this question',
                    'skip',
                ];

                const candidates = Array.from(root.querySelectorAll('button, a, div[role="button"], li, span'));
                for (const el of candidates) {
                    const t = (el.innerText || '').trim().toLowerCase();
                    if (!t) continue;
                    if (targets.some(s => t === s || t.includes(s))) {
                        el.click();
                        return t;
                    }
                }
                return null;
            }""")
            if clicked_text:
                log_info(f"Clicked chat Skip via JS (text='{clicked_text}')")
                return True
        except Exception:
            pass

        return False

    def _radio_options_look_yes_no(self, radio_options: list[dict]) -> bool:
        parts: list[str] = []
        for opt in radio_options:
            parts.append(str(opt.get("label", "")).lower())
            parts.append(str(opt.get("value", "")).lower())
        joined = " ".join(parts)
        return any(k in joined for k in ["yes", "yeah", "yep", "true", "no", "false", "nope"])

    def _normalize_token(self, text: str) -> str:
        return re.sub(r"[^a-z0-9]+", "", str(text or "").lower())

    def _text_mentions_skill(self, text: str, skill_name: str) -> bool:
        t = str(text or "").lower()
        s = str(skill_name or "").lower().strip()
        if not t or not s:
            return False

        # Exact phrase match for multi-word skills ("api testing", "rest assured", etc.)
        if " " in s or "-" in s or "." in s:
            if s in t:
                return True

        # Word-boundary match for single tokens ("java", "sql", etc.)
        if re.search(rf"\b{re.escape(s)}\b", t):
            return True

        # Normalized fallback: handles "restassured" vs "rest assured"
        ns = self._normalize_token(s)
        nt = self._normalize_token(t)
        return bool(ns and nt and ns in nt)

    def _desired_experience_years_for_question(self, question_text: str, screening: dict, default_years: float) -> float:
        qt = str(question_text or "").lower()
        skills = screening.get("skills_experience", {}) or {}
        if isinstance(skills, dict):
            for skill_name, years in skills.items():
                if self._text_mentions_skill(qt, str(skill_name)):
                    try:
                        return float(years)
                    except Exception:
                        continue

        try:
            return float(screening.get("total_experience_years", default_years))
        except Exception:
            try:
                return float(default_years)
            except Exception:
                return 0.0

    def _pick_experience_radio_option(self, radio_options: list[dict], desired_years: float) -> dict | None:
        if not radio_options:
            return None

        desired_years_f = 0.0
        try:
            desired_years_f = float(desired_years)
        except Exception:
            desired_years_f = 0.0

        INF = 1e9

        def parsed_intervals(text: str) -> list[tuple[float, float]]:
            t = str(text or "").lower()
            intervals: list[tuple[float, float]] = []

            # Closed ranges: "3-5", "4 to 6"
            for m in re.finditer(r"(\d+(?:\.\d+)?)\s*(?:-|to)\s*(\d+(?:\.\d+)?)", t):
                try:
                    lo = float(m.group(1))
                    hi = float(m.group(2))
                    if hi < lo:
                        lo, hi = hi, lo
                    intervals.append((lo, hi))
                except Exception:
                    continue

            # Open-ended: "5+", "5 years+", ">= 5", "at least 5", "5 and above"
            for m in re.finditer(r"(\d+(?:\.\d+)?)\s*\+", t):
                try:
                    lo = float(m.group(1))
                    intervals.append((lo, INF))
                except Exception:
                    continue
            for m in re.finditer(r"(?:>=|at\s+least|min(?:imum)?|more\s+than|above|over)\s*(\d+(?:\.\d+)?)", t):
                try:
                    lo = float(m.group(1))
                    intervals.append((lo, INF))
                except Exception:
                    continue
            for m in re.finditer(r"(\d+(?:\.\d+)?)\s*(?:and\s+above|or\s+more|years?\s+and\s+above)", t):
                try:
                    lo = float(m.group(1))
                    intervals.append((lo, INF))
                except Exception:
                    continue

            # Lower-bounded: "up to 5", "<= 5", "less than 5"
            for m in re.finditer(r"(?:<=|up\s*to|upto|at\s+most|max(?:imum)?|less\s+than|below|under)\s*(\d+(?:\.\d+)?)", t):
                try:
                    hi = float(m.group(1))
                    intervals.append((0.0, hi))
                except Exception:
                    continue

            # Fresher / no-exp buckets
            if any(k in t for k in ["fresher", "no experience", "0 year", "0 years"]):
                intervals.append((0.0, 0.0))

            # Exact number buckets like "5 years" (only if no better interval was found)
            if not intervals:
                nums = re.findall(r"\d+(?:\.\d+)?", t)
                for n in nums[:3]:
                    try:
                        v = float(n)
                        intervals.append((v, v))
                    except Exception:
                        continue

            # De-dupe while keeping order
            seen: set[tuple[float, float]] = set()
            out: list[tuple[float, float]] = []
            for lo, hi in intervals:
                key = (lo, hi)
                if key not in seen:
                    seen.add(key)
                    out.append(key)
            return out

        best: dict | None = None
        best_score: tuple[int, int, int, float, float, float] | None = None

        for opt in radio_options:
            combined = f"{opt.get('value', '')} {opt.get('label', '')}".lower().strip()
            intervals = parsed_intervals(combined)
            if not intervals:
                continue

            contains = False
            boundary = False
            best_width = INF
            best_mid_delta = INF
            best_distance = INF
            is_exact = False

            for lo, hi in intervals:
                lo_f = float(lo)
                hi_f = float(hi)
                if hi_f < lo_f:
                    lo_f, hi_f = hi_f, lo_f

                in_interval = lo_f <= desired_years_f <= hi_f
                if in_interval:
                    contains = True
                    if abs(desired_years_f - lo_f) < 1e-6 or abs(desired_years_f - hi_f) < 1e-6:
                        boundary = True
                    width = hi_f - lo_f if hi_f < INF else INF
                    midpoint = (lo_f + hi_f) / 2.0 if hi_f < INF else lo_f
                    mid_delta = abs(midpoint - desired_years_f)
                    if lo_f == hi_f and abs(lo_f - desired_years_f) < 1e-6:
                        is_exact = True

                    if width < best_width or (abs(width - best_width) < 1e-9 and mid_delta < best_mid_delta):
                        best_width = width
                        best_mid_delta = mid_delta
                else:
                    # Distance to interval (for fallbacks when no option contains desired)
                    if desired_years_f < lo_f:
                        dist = lo_f - desired_years_f
                    elif desired_years_f > hi_f:
                        dist = desired_years_f - hi_f
                    else:
                        dist = 0.0
                    if dist < best_distance:
                        best_distance = dist

            if not contains and best_distance >= INF:
                best_distance = INF

            # Prefer: contains desired > exact > boundary match > narrower width > closer to desired
            # Extra rule: prefer ranges where desired is NOT the lower bound (avoid "5-9", "5+")
            # i.e. prefer "4-5", "3-5" over "5-9", "5-10" when desired=5
            is_lower_bound = False
            is_upper_bound = False
            for lo, hi in intervals:
                lo_f = float(lo)
                hi_f = float(hi)
                if abs(lo_f - desired_years_f) < 1e-6 and hi_f > desired_years_f:
                    is_lower_bound = True  # e.g. "5-9" when desired=5
                if abs(hi_f - desired_years_f) < 1e-6 and lo_f < desired_years_f:
                    is_upper_bound = True  # e.g. "4-5" when desired=5

            # Score: prefer upper-bound ranges (4-5) over lower-bound ranges (5-9)
            # is_upper_bound=1 beats is_lower_bound=0
            bound_preference = 1 if is_upper_bound else (0 if is_lower_bound else 0)

            width_score = -best_width if best_width < INF else -INF
            score = (
                1 if contains else 0,
                1 if is_exact else 0,
                bound_preference,          # prefer "4-5" over "5-9"
                1 if boundary else 0,
                width_score,
                -best_mid_delta,
                -best_distance,
            )
            if best_score is None or score > best_score:
                best_score = score
                best = opt

        return best

    async def _click_radio_exact(self, radio_elems: list[dict], target_id: str = "", target_value: str = "") -> bool:
        target_id = str(target_id or "").strip()
        target_value = str(target_value or "").strip()
        if not target_id and not target_value:
            return False

        for elem in radio_elems:
            el = elem["element"]
            info = elem["info"]
            info_id = str(info.get("id", "") or "")
            info_val = str(info.get("value", "") or "")
            if target_id and info_id and info_id == target_id:
                try:
                    label = self.page.locator(f'label[for="{info_id}"]').first
                    if await label.is_visible(timeout=1000):
                        await label.click()
                        await human_delay(0.4, 0.8)
                        return True
                except Exception:
                    pass
                try:
                    await el.click(force=True)
                    await human_delay(0.4, 0.8)
                    return True
                except Exception:
                    continue

            if target_value and info_val and info_val == target_value:
                try:
                    await el.click(force=True)
                    await human_delay(0.4, 0.8)
                    return True
                except Exception:
                    continue

        return False

    async def _answer_chat_text_question(self, question_text: str, screening: dict, compensation: dict) -> bool:
        question_lower = question_text.lower()
        
        # Get defaults from profile or use fallback constants
        chat_defaults = self.profile.get("chatbot_defaults", {})
        def_exp = str(chat_defaults.get("experience", "4"))
        def_notice = str(chat_defaults.get("notice_period", "30"))
        def_salary = str(chat_defaults.get("expected_salary", "25"))

        answer = ""

        custom = self._chatbot_custom_answer(kind="text", question_text=question_text)
        if isinstance(custom, str) and custom.strip():
            answer = custom.strip()

        if not answer and self._local_ai_mode() == "always":
            ai = await self._ai_decide_chat(
                kind="text",
                question=question_text,
                options=None,
                screening=screening,
                compensation=compensation,
            )
            if isinstance(ai, dict) and str(ai.get("type", "")).lower() == "text":
                ai_answer = str(ai.get("answer", "") or "").strip()
                if ai_answer:
                    answer = ai_answer

        def _has_exp_token(text: str) -> bool:
            # Avoid matching "exp" inside words like "expected".
            return bool(re.search(r"\bexp\b|\bexp\.", text))

        # Experience / Idea questions - Always answer 5
        if not answer and (("experience" in question_lower) or _has_exp_token(question_lower) or ("idea" in question_lower)):
            answer = "5"

        # Location questions - Prefer Hyderabad, Bangalore, Chennai
        if not answer and any(kw in question_lower for kw in ["location", "city", "where", "place"]):
            if any(kw in question_lower for kw in ["prefer", "preferred", "current", "present"]):
                answer = "Hyderabad"
            else:
                answer = "Hyderabad"

        # F2F / Walk-in questions - Always Yes
        if not answer and any(kw in question_lower for kw in ["f2f", "face to face", "walk-in", "walk in", "walkin", "come to office", "visit office"]):
            answer = "Yes"

        # Previously employed / worked before - Always No
        if not answer and any(kw in question_lower for kw in ["previously employed", "worked before", "prior employment", "past employment"]):
            answer = "No"

        # General resolver (education, CTC, etc.)
        if not answer:
            try:
                resolved = self._resolve_screening_answer(question_text, screening, compensation)
                if resolved:
                    answer = str(resolved)
            except Exception:
                answer = ""
        # Notice period / Joining questions
        if not answer and any(kw in question_lower for kw in ["notice", "joining", "join"]):
            answer = def_notice
        # Salary questions
        elif not answer and any(kw in question_lower for kw in ["salary", "ctc", "lpa"]):
            answer = str(compensation.get("expected_ctc", def_salary))
        # Worked in company questions
        elif not answer and any(kw in question_lower for kw in ["worked in", "worked at", "prior experience"]):
            answer = "No"
        
        # If we couldn't resolve a specific answer, try local AI (if enabled), then fall back.
        if not answer:
            ai = await self._ai_decide_chat(
                kind="text",
                question=question_text,
                options=None,
                screening=screening,
                compensation=compensation,
            )
            if isinstance(ai, dict) and str(ai.get("type", "")).lower() == "text":
                ai_answer = str(ai.get("answer", "") or "").strip()
                if ai_answer:
                    answer = ai_answer

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
        compensation = self.profile.get("compensation", {}) or {}
        
        chat_defaults = self.profile.get("chatbot_defaults", {})
        def_exp = str(chat_defaults.get("experience", "4"))
        def_notice = str(chat_defaults.get("notice_period", "30"))

        resolved = None
        try:
            resolved = self._resolve_radio_answer(question_text, radio_options, screening)
        except Exception:
            resolved = None

        custom = self._chatbot_custom_answer(kind="radio", question_text=question_text)
        if target_idx == -1 and isinstance(custom, str) and custom.strip():
            custom_str = custom.strip()
            custom_digits = re.sub(r"[^\d.]", "", custom_str)
            # If user gave a number for an experience-like radio, try range selection.
            if custom_digits and any(re.search(r"\d", (o.get("label", "") or "") + (o.get("value", "") or "")) for o in radio_options):
                try:
                    desired = float(custom_digits)
                    best = self._pick_experience_radio_option(radio_options, desired)
                    if best:
                        for i, opt in enumerate(radio_options):
                            if opt.get("id") and best.get("id") and opt.get("id") == best.get("id"):
                                target_idx = i
                                break
                            if opt.get("value") and best.get("value") and opt.get("value") == best.get("value"):
                                target_idx = i
                                break
                except Exception:
                    pass

            if target_idx == -1:
                idx = self._match_choice_to_option_index(custom_str, radio_options)
                if idx != -1:
                    target_idx = idx

        if target_idx == -1 and self._local_ai_mode() == "always":
            ai = await self._ai_decide_chat(
                kind="radio",
                question=question_text,
                options=radio_options,
                screening=screening,
                compensation=compensation,
            )
            if isinstance(ai, dict) and str(ai.get("type", "")).lower() == "radio":
                choice = str(ai.get("choice", "") or "").strip()
                ai_idx = self._match_choice_to_option_index(choice, radio_options)
                if ai_idx != -1:
                    target_idx = ai_idx

        # Try to match based on user preferences
        exp_in_q = ("experience" in question_lower) or bool(re.search(r"\bexp\b|\bexp\.", question_lower)) or ("idea" in question_lower)
        if exp_in_q:
            # Always use 5 years for experience questions (user requirement)
            desired_years = 5.0

            # Prefer the range/tokens-based resolver (it tends to pick options like "4-6 years")
            # before falling back to exact-year substring matches.
            if resolved:
                for i, opt in enumerate(radio_options):
                    if opt.get("id") and resolved.get("id") and opt.get("id") == resolved.get("id"):
                        target_idx = i
                        break
                    if opt.get("value") and resolved.get("value") and opt.get("value") == resolved.get("value"):
                        target_idx = i
                        break

            if target_idx == -1:
                best = self._pick_experience_radio_option(radio_options, float(desired_years))
                if best:
                    for i, opt in enumerate(radio_options):
                        if opt.get("id") and best.get("id") and opt.get("id") == best.get("id"):
                            target_idx = i
                            break
                        if opt.get("value") and best.get("value") and opt.get("value") == best.get("value"):
                            target_idx = i
                            break

            if target_idx == -1:
                for i, opt in enumerate(radio_options):
                    lbl = opt.get('label', '').lower()
                    desired_str = str(int(desired_years)) if abs(float(desired_years) - int(float(desired_years))) < 1e-6 else str(desired_years)
                    if desired_str in lbl:
                        target_idx = i
                        break
        elif any(kw in question_lower for kw in ["notice", "joining", "join"]):
            for i, opt in enumerate(radio_options):
                lbl = opt.get('label', '').lower()
                if def_notice in lbl or "immediate" in lbl or "1 month" in lbl:
                    target_idx = i
                    break
        elif resolved:
            for i, opt in enumerate(radio_options):
                if opt.get("id") and resolved.get("id") and opt.get("id") == resolved.get("id"):
                    target_idx = i
                    break
                if opt.get("value") and resolved.get("value") and opt.get("value") == resolved.get("value"):
                    target_idx = i
                    break
        
        # If no match found: try skipping unknown questions; otherwise default to "No".
        if target_idx == -1:
            ai = await self._ai_decide_chat(
                kind="radio",
                question=question_text,
                options=radio_options,
                screening=screening,
                compensation=compensation,
            )
            if isinstance(ai, dict) and str(ai.get("type", "")).lower() == "radio":
                choice = str(ai.get("choice", "") or "").strip()
                ai_idx = self._match_choice_to_option_index(choice, radio_options)
                if ai_idx != -1:
                    target_idx = ai_idx

        if target_idx == -1:
            # Prefer answering Yes/No sets instead of skipping.
            if self._radio_options_look_yes_no(radio_options):
                no_opt = self._find_yes_no_radio_option(radio_options, False)
                if no_opt:
                    for i, opt in enumerate(radio_options):
                        if opt.get("id") and no_opt.get("id") and opt.get("id") == no_opt.get("id"):
                            target_idx = i
                            break
                        if opt.get("value") and no_opt.get("value") and opt.get("value") == no_opt.get("value"):
                            target_idx = i
                            break

        if target_idx == -1:
            if await self._click_chat_skip_question_button():
                await human_delay(1, 2)
                log_info(f"Chat radio: skipped unknown question: '{question_text[:60]}'")
                return True

            if target_idx == -1:
                # If it's not a yes/no radio set, fall back to the first option.
                if not self._radio_options_look_yes_no(radio_options):
                    target_idx = 0
                    log_info(
                        f"  No match/no-skip for radio Q, defaulting to first option: {radio_options[target_idx].get('label')}"
                    )

            if target_idx == -1:
                target_idx = 0
                log_info(f"  No match/no-skip for radio Q, defaulting to first option: {radio_options[target_idx].get('label')}")

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
        compensation = self.profile.get("compensation", {}) or {}

        def _combined(opt: dict) -> str:
            return f"{opt.get('label', '')} {opt.get('value', '')}".lower().strip()

        selected: list[dict] = []

        custom = self._chatbot_custom_answer(kind="checkbox", question_text=question_text)
        if isinstance(custom, str) and custom.strip():
            idx = self._match_choice_to_option_index(custom.strip(), checkbox_options)
            if idx != -1:
                selected = [checkbox_options[idx]]
        elif isinstance(custom, list) and custom:
            picked: list[dict] = []
            for c in custom[:10]:
                idx = self._match_choice_to_option_index(str(c), checkbox_options)
                if idx != -1:
                    picked.append(checkbox_options[idx])
            if picked:
                selected = picked

        if self._local_ai_mode() == "always":
            ai = await self._ai_decide_chat(
                kind="checkbox",
                question=question_text,
                options=checkbox_options,
                screening=screening,
                compensation=compensation,
            )
            if isinstance(ai, dict) and str(ai.get("type", "")).lower() == "checkbox":
                choices = ai.get("choices", [])
                if isinstance(choices, list):
                    picked: list[dict] = []
                    for c in choices[:5]:
                        idx = self._match_choice_to_option_index(str(c), checkbox_options)
                        if idx != -1:
                            picked.append(checkbox_options[idx])
                    if picked:
                        selected = picked

        # 1) Experience-style checkboxes (rare, but handle like radio ranges)
        if any(k in question_lower for k in ["experience", "exp", "years"]):
            desired = self._desired_experience_years_for_question(question_lower, screening, float(screening.get("total_experience_years", 0) or 0))
            best = self._pick_experience_radio_option(checkbox_options, float(desired))
            if best:
                selected = [best]

        # 2) Skills/Technology checkboxes: select skills you have years for
        if not selected and any(k in question_lower for k in ["skill", "technology", "tech", "stack", "tools"]):
            skills = screening.get("skills_experience", {}) or {}
            positive = self.profile.get("target_roles", {}).get("keywords_positive", []) or []
            chosen: list[dict] = []
            for opt in checkbox_options:
                text = _combined(opt)
                matched = False
                if isinstance(skills, dict):
                    for skill_name, years in skills.items():
                        try:
                            if float(years) <= 0:
                                continue
                        except Exception:
                            pass
                        if self._text_mentions_skill(text, str(skill_name)):
                            matched = True
                            break
                if not matched:
                    for kw in positive:
                        if kw and str(kw).lower() in text:
                            matched = True
                            break
                if matched:
                    chosen.append(opt)
            if chosen:
                selected = chosen

        # 3) Location checkboxes: select preferred locations
        if not selected and any(k in question_lower for k in ["location", "city", "preferred location", "preferred city"]):
            preferred_locations = screening.get("preferred_locations", None)
            if not preferred_locations:
                preferred_locations = self.profile.get("location", {}).get("preferred_cities", [])
            if isinstance(preferred_locations, str):
                preferred_list = [preferred_locations]
            elif isinstance(preferred_locations, list):
                preferred_list = preferred_locations
            else:
                preferred_list = []

            preferred_list = [str(x).strip() for x in preferred_list if str(x).strip()]
            preferred_expanded = self._expand_location_aliases(preferred_list) if preferred_list else []
            chosen: list[dict] = []
            for opt in checkbox_options:
                text = _combined(opt)
                if any(loc.lower() in text for loc in preferred_expanded):
                    chosen.append(opt)
            if chosen:
                selected = chosen

        # 4) Yes/No style checkboxes
        if not selected:
            joined = " ".join(_combined(o) for o in checkbox_options)
            looks_yes_no = any(k in joined for k in [" yes ", " no ", "true", "false"])
            if looks_yes_no:
                field_id = self._identify_field(question_lower) or ""
                bool_map = {
                    "willing_to_relocate": screening.get("willing_to_relocate", True),
                    "comfortable_night_shifts": screening.get("comfortable_night_shifts", False),
                    "comfortable_rotational_shifts": screening.get("comfortable_rotational_shifts", True),
                    "has_gap": screening.get("has_gap", False),
                    "passport_valid": screening.get("passport_valid", True),
                    "any_offer_in_hand": screening.get("any_offer_in_hand", False),
                }
                desired_bool = bool_map.get(field_id, True)
                target_labels = ["yes", "true", "1", "yep", "yeah"] if desired_bool else ["no", "false", "0", "nope"]
                for opt in checkbox_options:
                    text = _combined(opt)
                    if any(t in text for t in target_labels):
                        selected = [opt]
                        break

        # 5) Fallback: select first option to proceed
        if not selected and checkbox_options:
            selected = [checkbox_options[0]]

        # If we ended up with a fallback selection, prefer local AI to pick better matches (if enabled).
        if selected and checkbox_options and selected[0] == checkbox_options[0]:
            ai = await self._ai_decide_chat(
                kind="checkbox",
                question=question_text,
                options=checkbox_options,
                screening=screening,
                compensation=compensation,
            )
            if isinstance(ai, dict) and str(ai.get("type", "")).lower() == "checkbox":
                choices = ai.get("choices", [])
                if isinstance(choices, list):
                    picked: list[dict] = []
                    for c in choices[:5]:
                        idx = self._match_choice_to_option_index(str(c), checkbox_options)
                        if idx != -1:
                            picked.append(checkbox_options[idx])
                    if picked:
                        selected = picked

        try:
            success_count = 0
            seen_keys: set[tuple[str, str]] = set()
            for opt in selected:
                target_id = str(opt.get("id", "") or "")
                target_value = str(opt.get("value", "") or "")
                key = (target_id, target_value)
                if key in seen_keys:
                    continue
                seen_keys.add(key)

                await self.page.evaluate("""([targetId, targetValue]) => {
                    const checkboxes = Array.from(document.querySelectorAll('input[type="checkbox"]'));
                    for (const checkbox of checkboxes) {
                        if ((targetId && checkbox.id === targetId) || (!targetId && targetValue && checkbox.value === targetValue)) {
                            if (!checkbox.checked) {
                                const label = checkbox.id ? document.querySelector(`label[for="${checkbox.id}"]`) : null;
                                if (label) label.click();
                                else checkbox.click();
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
                await self._click_chat_save_button()
                await human_delay(2, 3)
                log_info(f"Chat answered (checkbox): checked {success_count} option(s)")
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
            'any_offer_in_hand': screening.get('any_offer_in_hand', False),
        }
        if field_id and field_id in bool_map:
            return self._find_yes_no_radio_option(radio_options, bool_map[field_id])

        if field_id == 'notice_period':
            return self._find_notice_period_radio(radio_options, screening.get('notice_period', '30 Days'))

        if field_id in ('total_experience', 'relevant_experience'):
            desired_years = screening.get('total_experience_years', 4)
            best = self._pick_experience_radio_option(radio_options, float(desired_years))
            if best:
                return best

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
            # Backward-compat: allow `search_preferences.any_offer_in_hand` to drive screening answers.
            if isinstance(screening, dict) and "any_offer_in_hand" not in screening:
                offer_pref = self.profile.get("search_preferences", {}).get("any_offer_in_hand", None)
                if offer_pref is not None:
                    screening["any_offer_in_hand"] = bool(offer_pref)

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
        for attempt in range(2):  # Reduced from 3 to 2 retries
            delay = 2 + attempt * 2
            if attempt > 0:
                log_info(f"Retry {attempt + 1}/2: waiting {delay}s for form elements...")
                await human_delay(delay, delay + 1)

            await human_delay(1, 2)  # Reduced initial wait
            form_elements = await self._collect_form_elements()
            if form_elements:
                break
            log_warning(f"Attempt {attempt + 1}/2: No form elements found")

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
            ('any_offer_in_hand', ['offer in hand', 'offers in hand', 'offer letter', 'holding offer', 'have an offer']),
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
            'any_offer_in_hand': screening.get('any_offer_in_hand', False),
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

        is_experience_group = any(k in group_text for k in ["experience", " exp", "years of", "years"])
        if not field_id_result and not is_experience_group:
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

        if field_id_result in ('total_experience', 'relevant_experience') or is_experience_group:
            desired_years = self._desired_experience_years_for_question(group_text, screening, float(screening.get("total_experience_years", 4) or 4))
            opt_list: list[dict] = []
            for elem in radio_elems:
                el = elem["element"]
                info = elem["info"]
                try:
                    elem_text = await el.evaluate("""el => {
                        const parent = el.closest('label, div, li');
                        if (parent) return parent.innerText || '';
                        return el.value || '';
                    }""")
                except Exception:
                    elem_text = ""
                opt_list.append(
                    {
                        "id": info.get("id", ""),
                        "value": info.get("value", ""),
                        "label": str(elem_text or ""),
                    }
                )

            # Only use range selection when options look numeric (e.g., "3-5 years").
            if any(re.search(r"\d", f"{o.get('label','')} {o.get('value','')}") for o in opt_list):
                best = self._pick_experience_radio_option(opt_list, float(desired_years))
                if best:
                    if await self._click_radio_exact(radio_elems, target_id=best.get("id", ""), target_value=best.get("value", "")):
                        log_info(f"Experience radio: picked '{best.get('label','')[:40]}'")
                        return True

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

    async def _parallel_search_jobs(
        self, 
        keywords: list[str], 
        locations: list[str], 
        fresh_only: bool = True, 
        sort_by_date: bool = True
    ) -> list[dict]:
        """
        Search for jobs in PARALLEL using multiple browser tabs.
        Opens all keyword+location combinations simultaneously for maximum speed.
        """
        all_jobs: list[dict] = []

        search_tasks: list[tuple[str, str]] = []
        for keyword in keywords:
            for location in locations:
                search_tasks.append((keyword, location))

        log_info(f"Opening {len(search_tasks)} tabs for PARALLEL search...")

        # Create all tabs first
        pages_and_tasks = []
        for keyword, location in search_tasks:
            try:
                new_page = await self.context.new_page()
                pages_and_tasks.append((new_page, keyword, location))
            except Exception as e:
                log_warning(f"Could not create tab for {keyword} in {location}: {e}")

        # Define search function for each tab
        async def search_in_tab(page, keyword, location):
            try:
                # Build search URL
                search_slug = re.sub(r"[^a-z0-9]+", "-", keyword.lower()).strip("-")
                search_url = f"{self.NAUKRI_BASE}/{search_slug}-jobs"
                if location:
                    loc_slug = re.sub(r"[^a-z0-9]+", "-", location.lower()).strip("-")
                    search_url += f"-in-{loc_slug}"

                jobs = []
                date_sorted = False  # Track if we've already sorted by date
                sorted_base_url = None  # URL after sort is applied (used for pagination)

                # Search up to 3 pages
                for page_num in range(1, 4):
                    if page_num == 1:
                        page_url = search_url
                    else:
                        # Use the sorted URL as base for page 2, 3 to keep sort filter
                        base = sorted_base_url if sorted_base_url else search_url
                        # Strip any existing page number suffix from base URL
                        # e.g. /qa-automation-jobs-in-bangalore?sort=f -> /qa-automation-jobs-in-bangalore-2?sort=f
                        if "?" in base:
                            path_part, query_part = base.split("?", 1)
                            page_url = f"{path_part}-{page_num}?{query_part}"
                        else:
                            page_url = f"{base}-{page_num}"
                    
                    try:
                        await page.goto(page_url, wait_until="domcontentloaded", timeout=30000)
                        await asyncio.sleep(1.5)  # Brief wait for content
                    except Exception as e:
                        log_warning(f"Could not load page {page_num} for {keyword}: {e}")
                        break

                    # On first page, apply date sorting + freshness filter ONCE
                    # After clicking Date, Naukri reloads with a new URL - capture it for pagination
                    if page_num == 1 and sort_by_date and not date_sorted:
                        try:
                            # Step 1: Click the sort button (id="filter-sort")
                            sort_btn = page.locator('button#filter-sort').first
                            if await sort_btn.is_visible(timeout=4000):
                                await sort_btn.click()
                                await asyncio.sleep(1.0)
                                # Step 2: Click "Date" option from dropdown
                                date_opt = page.locator('ul[data-filter-id="sort"] li[title="Date"] a').first
                                if await date_opt.is_visible(timeout=2000):
                                    await date_opt.click()
                                    await asyncio.sleep(2.5)  # Wait for page to reload sorted by date
                                    date_sorted = True
                                    # Capture the new URL (Naukri adds sort param to URL)
                                    current_url = page.url
                                    # Store as base for page 2, 3 pagination
                                    # Remove any page number from current URL to get base
                                    sorted_base_url = re.sub(r'-(\d+)(\?|$)', r'\2', current_url)
                                    if not sorted_base_url:
                                        sorted_base_url = current_url
                                    log_info(f"  Sorted by Date: {keyword} in {location} | base: {sorted_base_url[:60]}")
                                else:
                                    # Fallback: try clicking by data-id attribute
                                    date_opt2 = page.locator('a[data-id="filter-sort-f"]').first
                                    if await date_opt2.is_visible(timeout=1000):
                                        await date_opt2.click()
                                        await asyncio.sleep(2.5)
                                        date_sorted = True
                                        current_url = page.url
                                        sorted_base_url = re.sub(r'-(\d+)(\?|$)', r'\2', current_url)
                                        if not sorted_base_url:
                                            sorted_base_url = current_url
                                        log_info(f"  Sorted by Date (fallback): {keyword} in {location}")
                        except Exception:
                            pass  # Continue without sorting if it fails

                        # Step 3: Apply "Last 7 days" freshness filter
                        # Selector from HTML: button#filter-freshness → li[title="Last 7 days"] a[data-id="filter-freshness-7"]
                        try:
                            freshness_btn = page.locator('button#filter-freshness').first
                            if await freshness_btn.is_visible(timeout=3000):
                                await freshness_btn.click()
                                await asyncio.sleep(0.8)
                                fresh_opt = page.locator('a[data-id="filter-freshness-7"]').first
                                if await fresh_opt.is_visible(timeout=2000):
                                    await fresh_opt.click()
                                    await asyncio.sleep(2.5)  # Wait for page to reload with freshness filter
                                    # Update base URL after freshness filter applied
                                    current_url = page.url
                                    sorted_base_url = re.sub(r'-(\d+)(\?|$)', r'\2', current_url)
                                    if not sorted_base_url:
                                        sorted_base_url = current_url
                                    log_info(f"  Freshness filter (7 days) applied: {keyword} in {location}")
                        except Exception:
                            pass  # Continue without freshness filter if it fails

                    # Extract jobs from this page
                    try:
                        await page.wait_for_selector('div.srp-jobtuple-wrapper, [data-job-id]', timeout=10000)
                    except Exception:
                        break

                    job_cards = await page.query_selector_all('div.srp-jobtuple-wrapper')
                    
                    for card in job_cards:
                        try:
                            # Extract job details
                            title_el = await card.query_selector('a.title')
                            if not title_el:
                                continue

                            title = (await title_el.inner_text()).strip()
                            job_url = await title_el.get_attribute("href")
                            if job_url and not job_url.startswith("http"):
                                job_url = self.NAUKRI_BASE + job_url

                            company_el = await card.query_selector('a.comp-name')
                            company = (await company_el.inner_text()).strip() if company_el else "Unknown"

                            location_el = await card.query_selector('span.locWdth')
                            loc = (await location_el.inner_text()).strip() if location_el else ""

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

                            jobs.append({
                                "id": job_id,
                                "title": title,
                                "url": job_url,
                                "company": company,
                                "location": loc,
                                "salary": salary_text,
                                "experience": experience,
                                "tags": tags,
                                "description": description,
                                "posted": posted,
                            })
                        except Exception as e:
                            continue
                    
                    # No early stop - scrape all pages to get all date-sorted jobs
                
                log_info(f"  {keyword} in {location}: {len(jobs)} jobs")
                return jobs
                
            except Exception as e:
                log_warning(f"Error searching {keyword} in {location}: {e}")
                return []
            finally:
                try:
                    await page.close()
                except Exception:
                    pass

        # Execute all searches in parallel
        log_info("Executing parallel searches...")
        search_coroutines = [
            search_in_tab(page, keyword, location) 
            for page, keyword, location in pages_and_tasks
        ]
        
        results = await asyncio.gather(*search_coroutines, return_exceptions=True)
        
        # Collect all jobs
        for result in results:
            if isinstance(result, list):
                all_jobs.extend(result)
            elif isinstance(result, Exception):
                log_warning(f"Search task failed: {result}")

        log_success(f"Parallel search complete! Found {len(all_jobs)} total jobs")
        return all_jobs

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
            keywords = self.profile.get("target_roles", {}).get("primary", [])

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

        if location:
            search_locations = [location]
        else:
            configured_locations = [
                str(city).strip()
                for city in self.profile.get("location", {}).get("preferred_cities", [])
                if str(city).strip()
            ]
            max_locations = int(self.profile.get("search_preferences", {}).get("max_locations_per_run", 4) or 4)
            max_locations = max(1, min(max_locations, 10))
            search_locations = (configured_locations[:max_locations] if configured_locations else [""])

        # Search across role+location combinations (sequential for stability).
        log_step(f"Starting search for {len(keywords)} roles across {len(search_locations)} locations...")
        all_jobs = await self._parallel_search_jobs(keywords, search_locations, fresh_only, sort_by_date)

        seen_urls = set()
        unique_jobs = []
        for job in all_jobs:
            url = job.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_jobs.append(job)
        all_jobs = unique_jobs

        log_info(f"Total unique jobs found: {len(all_jobs)}")

        filtered_jobs = self._filter_jobs(all_jobs, relaxed=False)
        log_info(f"Jobs after filtering (strict): {len(filtered_jobs)}")

        # If the user requested a big run, fall back to a relaxed filter set to increase coverage.
        if max_jobs and max_jobs > 0 and len(filtered_jobs) < max_jobs:
            relaxed_jobs = self._filter_jobs(all_jobs, relaxed=True)
            if len(relaxed_jobs) > len(filtered_jobs):
                log_warning(
                    f"Strict filters yielded only {len(filtered_jobs)} jobs; using relaxed filters ({len(relaxed_jobs)}) to try to reach the target."
                )
                filtered_jobs = relaxed_jobs
            log_info(f"Jobs after filtering (final): {len(filtered_jobs)}")

        if dry_run:
            log_info("DRY RUN - Showing jobs without applying:")
            for i, job in enumerate(filtered_jobs[:max_jobs], 1):
                log_info(
                    f"  {i}. {job['company']} | {job['title']} | {job['location']} | {job['salary']}"
                )
            return filtered_jobs[:max_jobs]

        # Keep trying until we get max_jobs SUCCESSFUL applications
        results = []
        successful_count = 0
        job_index = 0
        
        # We'll keep looping through available jobs until we hit the target SUCCESSFUL applications
        while successful_count < max_jobs and job_index < len(filtered_jobs):
            job = filtered_jobs[job_index]
            job_index += 1

            # Recover from unexpected browser/page closures between applications.
            try:
                ok = await self._ensure_browser_session()
                if not ok:
                    log_warning("Could not ensure browser session; stopping apply loop")
                    break
            except Exception as e:
                log_warning(f"Could not ensure browser session: {e}")
                break
            
            if self.session_applied >= self.max_per_day:
                log_warning(f"Daily application limit reached ({self.max_per_day})")
                break

            # Default to skipping "Apply on company site" listings (they don't count as applied).
            result = await self.apply_to_job(job, skip_external=True)
            results.append(result)

            # If the browser/page closed during this attempt, restart for the next job.
            if str(result.get("status", "")).lower() == "error" and "closed" in str(result.get("error", "")).lower():
                try:
                    await self._ensure_browser_session()
                except Exception:
                    pass
            
            # Only count TRUE successful applications (status == "applied")
            if result.get("status") == "applied":
                successful_count += 1
                log_success(f"Progress: {successful_count}/{max_jobs} successful applications completed")
         
        # If we ran out of filtered jobs but haven't hit target, log it
        if successful_count < max_jobs and job_index >= len(filtered_jobs):
            log_warning(
                f"Ran out of suitable jobs. Applied: {successful_count}/{max_jobs}. "
                f"Try expanding search criteria or running again later."
            )

        if max_jobs > 0:
            log_success(f"Session complete. Successfully applied to {successful_count}/{max_jobs} jobs (Total attempts: {len(results)}).")
            if successful_count < max_jobs:
                counts: dict[str, int] = {}
                for r in results:
                    status = str(r.get("status") or "unknown")
                    counts[status] = counts.get(status, 0) + 1
                breakdown = ", ".join(f"{k}={v}" for k, v in sorted(counts.items()))
                log_warning(f"Breakdown: {breakdown}")
        else:
            log_success(f"Session complete. Successfully applied to {successful_count} jobs out of {len(results)} attempts.")

        # Save external jobs and generate report
        if self.external_jobs:
            self.save_external_jobs()
        
        self.generate_session_report(results)
        
        return results

    def _filter_jobs(self, jobs: list[dict], *, relaxed: bool = False) -> list[dict]:
        target = self.profile.get("target_roles", {})
        roles_primary = [r.lower() for r in target.get("primary", [])]
        roles_secondary = [r.lower() for r in target.get("secondary", [])]
        target_roles = [r for r in (roles_primary + roles_secondary) if r]
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

            if not relaxed:
                if target_roles and not any(r in title_lower for r in target_roles):
                    continue

            has_negative = any(nk in combined for nk in negative_kw)
            if has_negative:
                continue

            location_lower = job.get("location", "").lower()
            if not relaxed:
                if preferred_cities and location_lower:
                    location_match = any(city in location_lower for city in preferred_cities)
                    if not location_match and "remote" not in location_lower:
                        if self.profile.get("location", {}).get("remote_preference") != "remote_first":
                            continue

            has_positive = any(pk in combined for pk in positive_kw) if positive_kw else True
            has_seniority = any(s in title_lower for s in seniority) if seniority else True

            if not relaxed:
                if not has_positive and not has_seniority:
                    continue

            if not relaxed:
                if min_ctc > 0:
                    salary_lakhs = extract_salary_lakhs(job.get("salary", ""))
                    if 0 < salary_lakhs < min_ctc:
                        continue

            if not relaxed:
                # Filter out jobs older than 7 days
                posted = job.get("posted", "").lower()
                
                # Skip anything explicitly old
                if any(x in posted for x in ["30+", "15+", "2 week", "3 week", "4 week", "8 day", "9 day", "10 day", "11 day", "12 day", "13 day", "14 day", "15 day", "16 day", "17 day", "18 day", "19 day", "20 day", "21 day", "22 day", "23 day", "24 day", "25 day", "26 day", "27 day", "28 day", "29 day", "30 day"]):
                    continue
                
                # Parse "X days ago" - skip if > 7 days
                if "day" in posted:
                    try:
                        match = re.search(r'(\d+)\s*day', posted)
                        if match:
                            days = int(match.group(1))
                            if days > 7:
                                continue
                    except Exception:
                        pass
                
                # Skip if 1+ weeks old (1 week = 7 days, so skip anything "1 week ago" or more)
                if "week" in posted:
                    try:
                        match = re.search(r'(\d+)\s*week', posted)
                        if match:
                            weeks = int(match.group(1))
                            if weeks >= 1:
                                continue
                    except Exception:
                        pass

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

    async def scrape_application_status_page(self) -> list[dict]:
        """
        1. Go directly to https://www.naukri.com/myapply/historypage
        2. Click the 'Applies on Naukri' tab
        3. Scroll-load ALL cards (handles pagination via infinite scroll)
        4. Parse every card and return structured data
        """
        log_step("Navigating to https://www.naukri.com/myapply/historypage ...")
        results = []

        try:
            await self.page.goto(
                "https://www.naukri.com/myapply/historypage",
                wait_until="domcontentloaded",
                timeout=30000,
            )
            await human_delay(3, 5)
        except Exception as e:
            log_error(f"Could not load historypage: {e}")
            return results

        # ── Click "Applies on Naukri" tab ────────────────────────────────────
        log_step("Clicking 'Applies on Naukri' tab...")
        try:
            tab = self.page.locator('p.title[title="Applies on Naukri"]').first
            if not await tab.is_visible(timeout=8000):
                # fallback: any element with that exact text
                tab = self.page.get_by_text("Applies on Naukri", exact=True).first
            await tab.click(timeout=8000)
            await human_delay(2, 3)
            log_success("Clicked 'Applies on Naukri' tab")
        except Exception as e:
            log_warning(f"Could not click tab (continuing anyway): {e}")

        # ── Scroll to load all cards (infinite scroll) ───────────────────────
        log_step("Scrolling to load all applications...")

        CARD_SEL = (
            '.jdTupleContainer, [class*="jdTupleContainer"], '
            '.appliedJobsTuple, [class*="appliedJob"], '
            '.jobTuple, [class*="jobTuple"]'
        )

        prev_count = 0
        no_change_streak = 0

        for scroll_attempt in range(200):  # up to 200 scrolls — enough for 2000+ jobs
            # Scroll to absolute bottom
            await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await human_delay(2, 3)  # wait for new batch to render

            # Also try clicking a "Load more" / "Show more" button if present
            try:
                load_more = self.page.locator(
                    'button:has-text("Load more"), button:has-text("Show more"), '
                    'a:has-text("Load more"), [class*="loadMore"], [class*="load-more"]'
                ).first
                if await load_more.is_visible(timeout=1000):
                    await load_more.click()
                    await human_delay(2, 3)
                    log_info("  Clicked 'Load more' button")
            except Exception:
                pass

            cards_now = await self.page.query_selector_all(CARD_SEL)
            current_count = len(cards_now)
            log_info(f"  Scroll {scroll_attempt+1}: {current_count} cards loaded")

            if current_count == prev_count:
                no_change_streak += 1
                if no_change_streak >= 5:
                    # 5 consecutive scrolls with no new cards = truly done
                    log_info(f"  No new cards after {no_change_streak} scrolls — done")
                    break
                # Wait a bit longer before giving up
                await human_delay(2, 3)
            else:
                no_change_streak = 0  # reset streak whenever new cards appear

            prev_count = current_count

        # ── Find all cards ────────────────────────────────────────────────────
        card_selectors = [
            '.jdTupleContainer',
            '[class*="jdTupleContainer"]',
            '.appliedJobsTuple',
            '[class*="appliedJob"]',
            '.jobTuple',
            '[class*="jobTuple"]',
        ]
        cards = []
        for sel in card_selectors:
            try:
                found = await self.page.query_selector_all(sel)
                if found:
                    cards = found
                    log_info(f"Using selector '{sel}': {len(cards)} cards")
                    break
            except Exception:
                continue

        if not cards:
            # absolute fallback — grab every li that has a job link
            try:
                cards = await self.page.query_selector_all("li:has(a[href*='job-listings'])")
            except Exception:
                pass

        log_info(f"Total cards to parse: {len(cards)}")

        # ── Parse each card ───────────────────────────────────────────────────
        for card in cards:
            try:
                raw = (await card.inner_text()).strip()
                lines = [l.strip() for l in raw.split("\n") if l.strip()]
                raw_lower = raw.lower()
                app: dict = {}

                # Title
                title = ""
                for sel in ["a.title", ".title a", '[class*="title"] a', "h3 a", "h2 a"]:
                    try:
                        el = await card.query_selector(sel)
                        if el:
                            title = (await el.inner_text()).strip()
                            href = await el.get_attribute("href") or ""
                            if href:
                                app["url"] = href if href.startswith("http") else f"https://www.naukri.com{href}"
                            if title:
                                break
                    except Exception:
                        continue
                if not title:
                    title = lines[0] if lines else ""
                if not title:
                    continue
                app["title"] = title[:120]

                # Company
                company = ""
                for sel in [".comp-name", ".companyName", '[class*="comp-name"]', '[class*="companyName"]']:
                    try:
                        el = await card.query_selector(sel)
                        if el:
                            company = (await el.inner_text()).strip()
                            if company:
                                break
                    except Exception:
                        continue
                if not company and len(lines) > 1:
                    company = lines[1]
                app["company"] = company[:80]

                # Company rating
                rating = ""
                try:
                    r_el = await card.query_selector('[class*="rating"], .rating')
                    if r_el:
                        rating = re.sub(r"[^\d.]", "", (await r_el.inner_text()).strip())
                except Exception:
                    pass
                app["company_rating"] = rating

                # Company reviews
                reviews = ""
                try:
                    rv_el = await card.query_selector('[class*="review"], .reviews')
                    if rv_el:
                        reviews = re.sub(r"[^\d,K]", "", (await rv_el.inner_text()).strip())
                except Exception:
                    pass
                app["company_reviews"] = reviews

                # Applied date — "Application sent today" / "Application sent 30 Apr '26"
                applied_date = ""
                m_date = re.search(
                    r"application\s+sent\s+(today|yesterday|\d{1,2}\s+\w+(?:\s+'?\d{2,4})?|\d+\s+\w+\s+ago)",
                    raw, re.I
                )
                if m_date:
                    applied_date = m_date.group(0).strip()
                else:
                    # fallback: look for any date-like string
                    m_date2 = re.search(r"\d{1,2}\s+\w{3}\s+'?\d{2,4}", raw)
                    if m_date2:
                        applied_date = m_date2.group(0).strip()
                app["applied_date"] = applied_date

                # Recruiter last active
                recruiter_active = ""
                m_rec = re.search(r"recruiter\s+last\s+active\s+(.+?)(?:\n|$)", raw, re.I)
                if m_rec:
                    recruiter_active = m_rec.group(1).strip()
                app["recruiter_last_active"] = recruiter_active

                # Normalize status — Naukri has exactly 4 steps:
                # Applied → Application Sent → Application Viewed → Shortlisted/Not Shortlisted
                if "not shortlisted" in raw_lower:
                    norm_status = "not_shortlisted"
                elif "shortlisted" in raw_lower or "selected" in raw_lower:
                    norm_status = "shortlisted"
                elif "application viewed" in raw_lower or "viewed" in raw_lower:
                    norm_status = "viewed"
                elif "application sent" in raw_lower or "sent" in raw_lower:
                    norm_status = "sent"
                elif "external" in raw_lower or "apply on company" in raw_lower:
                    norm_status = "external"
                else:
                    norm_status = "applied"
                app["status"] = norm_status
                app["source"] = "external" if norm_status == "external" else "naukri"

                # 4-step stepper booleans
                app["step_applied"]     = True
                app["step_sent"]        = norm_status in ("sent", "viewed", "shortlisted", "not_shortlisted")
                app["step_viewed"]      = norm_status in ("viewed", "shortlisted", "not_shortlisted")
                app["step_shortlisted"] = norm_status in ("shortlisted", "not_shortlisted")

                # Activity stats
                total_apps_on_job = None
                viewed_by_rec = None
                m_ta = re.search(r"(\d+)\s*total\s*applications?", raw, re.I)
                if m_ta:
                    total_apps_on_job = int(m_ta.group(1))
                m_vr = re.search(r"(\d+)\s*applications?\s*viewed\s*by\s*recruiter", raw, re.I)
                if m_vr:
                    viewed_by_rec = int(m_vr.group(1))
                app["total_applications"]  = total_apps_on_job
                app["viewed_by_recruiter"] = viewed_by_rec

                # Job ID
                job_id = ""
                try:
                    job_id = await card.get_attribute("data-job-id") or ""
                    if not job_id and app.get("url"):
                        m_id = re.search(r"(\d{8,})", app["url"])
                        if m_id:
                            job_id = m_id.group(1)
                except Exception:
                    pass
                app["job_id"] = job_id

                results.append(app)

            except Exception as e:
                log_warning(f"Error parsing card: {e}")
                continue

        log_success(f"Scraped {len(results)} applications from Naukri")
        return results

    def get_session_stats(self) -> dict:
        return {
            "date": self.session_date,
            "applied": self.session_applied,
            "max_per_day": self.max_per_day,
            "remaining": max(0, self.max_per_day - self.session_applied),
            "external_jobs": len(self.external_jobs),
        }

    def save_external_jobs(self) -> None:
        """Save external/company site jobs to JSON file."""
        if not self.external_jobs:
            return
        
        output_dir = Path("output")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        json_file = output_dir / "external_jobs.json"
        
        # Load existing data if file exists
        existing_jobs = []
        if json_file.exists():
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    existing_jobs = json.load(f)
            except Exception:
                pass
        
        # Append new jobs
        existing_jobs.extend(self.external_jobs)
        
        # Save to JSON
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(existing_jobs, f, indent=2, ensure_ascii=False)
        
        log_success(f"Saved {len(self.external_jobs)} external jobs to {json_file}")

    def generate_session_report(self, results: list[dict]) -> None:
        """Generate HTML report for the session."""
        output_dir = Path("output")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        html_file = output_dir / f"session_report_{timestamp}.html"
        
        # Count statuses
        applied_count = sum(1 for r in results if r.get("status") == "applied")
        failed_count = sum(1 for r in results if r.get("status") in ("failed", "error"))
        external_count = len(self.external_jobs)
        
        # Generate HTML
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Naukri Session Report - {timestamp}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f5f5f5; padding: 20px; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); padding: 30px; }}
        h1 {{ color: #333; margin-bottom: 10px; }}
        .date {{ color: #666; font-size: 14px; margin-bottom: 30px; }}
        .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 40px; }}
        .stat-card {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; text-align: center; }}
        .stat-card.success {{ background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); }}
        .stat-card.warning {{ background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); }}
        .stat-card.info {{ background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); }}
        .stat-number {{ font-size: 48px; font-weight: bold; margin-bottom: 5px; }}
        .stat-label {{ font-size: 14px; opacity: 0.9; }}
        .section {{ margin-bottom: 40px; }}
        .section-title {{ font-size: 24px; color: #333; margin-bottom: 20px; border-bottom: 2px solid #667eea; padding-bottom: 10px; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th {{ background: #667eea; color: white; padding: 12px; text-align: left; font-weight: 600; }}
        td {{ padding: 12px; border-bottom: 1px solid #eee; }}
        tr:hover {{ background: #f9f9f9; }}
        .status-badge {{ padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 600; }}
        .status-applied {{ background: #d4edda; color: #155724; }}
        .status-external {{ background: #fff3cd; color: #856404; }}
        .status-failed {{ background: #f8d7da; color: #721c24; }}
        a {{ color: #667eea; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🎯 Naukri Job Application Report</h1>
        <div class="date">Generated on {datetime.now().strftime("%B %d, %Y at %I:%M %p")}</div>
        
        <div class="summary">
            <div class="stat-card success">
                <div class="stat-number">{applied_count}</div>
                <div class="stat-label">Successfully Applied</div>
            </div>
            <div class="stat-card warning">
                <div class="stat-number">{external_count}</div>
                <div class="stat-label">External/Company Sites</div>
            </div>
            <div class="stat-card info">
                <div class="stat-number">{len(results)}</div>
                <div class="stat-label">Total Attempts</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{failed_count}</div>
                <div class="stat-label">Failed/Errors</div>
            </div>
        </div>
"""

        # External jobs section
        if self.external_jobs:
            html_content += """
        <div class="section">
            <div class="section-title">🔗 External/Company Site Jobs</div>
            <table>
                <thead>
                    <tr>
                        <th>#</th>
                        <th>Company</th>
                        <th>Job Title</th>
                        <th>Location</th>
                        <th>Posted</th>
                        <th>Salary</th>
                        <th>Link</th>
                    </tr>
                </thead>
                <tbody>
"""
            for idx, job in enumerate(self.external_jobs, 1):
                posted = job.get('posted', 'N/A')
                html_content += f"""
                    <tr>
                        <td>{idx}</td>
                        <td>{job.get('company', 'N/A')}</td>
                        <td>{job.get('title', 'N/A')}</td>
                        <td>{job.get('location', 'N/A')}</td>
                        <td>{posted}</td>
                        <td>{job.get('salary', 'N/A')}</td>
                        <td><a href="{job.get('url', '#')}" target="_blank">Open Job</a></td>
                    </tr>
"""
            html_content += """
                </tbody>
            </table>
        </div>
"""

        html_content += """
    </div>
</body>
</html>
"""
        
        # Save HTML file
        with open(html_file, "w", encoding="utf-8") as f:
            f.write(html_content)
        
        log_success(f"Session report saved to {html_file}")
        
        # Try to open in browser
        try:
            import webbrowser
            webbrowser.open(str(html_file.absolute()))
        except Exception:
            pass
