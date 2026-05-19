import os
import time
from playwright.sync_api import sync_playwright

EMAIL = os.getenv("NAUKRI_EMAIL")
PASSWORD = os.getenv("NAUKRI_PASSWORD")

LOGIN_URL = "https://www.naukri.com/nlogin/login"
PROFILE_URL = "https://www.naukri.com/mnjuser/profile"

EDIT_BUTTON = '//*[@id="lazyResumeHead"]/div/div/div[1]/span[2]'


def login(page):

    print("Logging in")

    page.goto(LOGIN_URL)

    page.wait_for_selector("#usernameField")

    page.fill("#usernameField", EMAIL)
    page.fill("#passwordField", PASSWORD)

    page.click("button[type='submit']")

    page.wait_for_timeout(5000)


def open_profile(page):

    print("Opening profile")

    page.goto(PROFILE_URL)

    page.wait_for_selector("#lazyResumeHead", timeout=30000)


def update_headline(page):

    print("Editing Resume Headline")

    edit_button = page.wait_for_selector(
        "xpath=//*[@id='lazyResumeHead']/div/div/div[1]/span[2]",
        timeout=30000
    )

    edit_button.click()

    textarea = page.wait_for_selector("textarea")

    current = textarea.input_value()

    headline_version_1 = (
        "4+ years of experience in Software Quality Assurance and Test Automation process "
        "with a solid understanding of Test Planning, Test Design, Test Execution and "
        "Defect Reporting & Tracking for Supermaket Domain."
    )

    headline_version_2 = (
        "4+ years of experience in Software Quality Assurance and Test Automation process "
        "with a solid understanding of Test Planning, Test Design, Test Execution and "
        "Defect Reporting & Tracking for API Data Driven application."
    )

    headline_version_3 = (
        "4+ years of experience in Software Quality Assurance and Test Automation process "
        "with a solid understanding of Test Planning, Test Design, Test Execution and "
        "Defect Reporting & Tracking for Supermaket API Data Driven Domain."
    )

    if "Supermaket" in current:
        updated = headline_version_2
        print("Switching headline → API Data Driven application")
    else:
        updated = headline_version_3
        print("Switching headline → Supermaket API Data Driven Domain")

    textarea.fill(updated)

    page.get_by_role("button", name="Save").click()

    page.wait_for_timeout(3000)

    print("Headline updated successfully")

def main():

    if not EMAIL or not PASSWORD:
        raise Exception("Please set NAUKRI_EMAIL and NAUKRI_PASSWORD")

    with sync_playwright() as p:

        browser = p.chromium.launch(headless=False)

        page = browser.new_page()

        login(page)

        open_profile(page)

        update_headline(page)

        print("Done")

        time.sleep(5)

        browser.close()


if __name__ == "__main__":
    main()