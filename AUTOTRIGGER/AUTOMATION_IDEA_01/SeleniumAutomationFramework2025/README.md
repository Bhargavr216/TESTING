# SeleniumAutomationFramework2025 — Enterprise-grade Web Automation

## End-to-End Explanation
The framework starts with Maven dependency resolution, loads test data from `testdata/TestData.xlsx`, boots up the browser via `BaseTest`, and runs TestNG suites (`testng.xml`, `testng1.xml`). Tests interact with POM classes (e.g., `LoginPage`, `UserManagementPage`, `ProductManagementPage`), capture screenshots, log execution via Log4j2, and generate ExtentReports/ TestNG reports plus email notifications. The entire run is designed to simulate the complete user journey: login → manage users/products → logout.

## Key Components and Coverage
- **`src/main/java/com/bhargav/automation/base/BaseTest.java`**: central WebDriver lifecycle (setup, teardown, screenshot capture, report hooks).
- **`pages/`**: all page objects that wrap locators and interactions for login, user management, and product flows.
- **`utils/`**: `ExtentReportManager`, `ExcelUtils`, `EmailUtils`, and `Log` helpers that standardize reporting, data, email, and logging.
- **`test/java/com/bhargav/automation/tests/`**: actual test classes such as `LoginTest`, `UserManagementTest`, `ProductManagementTest`.
- **`testdata/TestData.xlsx`**: drives data-driven tests (user credentials, test descriptions, cross-browser flags).
- **`reports/`, `screenshots/`, `test-output/`**: hold Extent HTML reports, screenshot archives for failures, and TestNG output.
- **`EmailUtils`**: optionally sends Extent reports to stakeholders after runs.

## Setup & Execution
1. Install **Java (JDK 11+)**, **Maven 3.6+**, and ensure Chrome/Firefox/Edge binaries are available.
2. Optionally configure email credentials in `EmailUtils.java`.
3. Run `mvn clean install` from `SeleniumAutomationFramework2025` to grab dependencies.
4. Execute `mvn test` for the default suite, or `mvn test -DsuiteXmlFile=testng.xml`/`testng1.xml` for specific suites.
5. Use `mvn test -Dtest=LoginTest`, `-Dtest=UserManagementTest`, or `-Dbrowser=firefox` to scope runs.

## Reporting & Observability
- Extent HTML reports (`reports/ExtentReport_*.html`) list test steps, embed screenshots, and provide pass/fail metrics.
- TestNG reports (`test-output/index.html`) offer method/class level summaries with timing.
- Failure screenshots appear under `screenshots/` with timestamps for context.
- Log4j2 writes structured logs to console/files for quick debugging.

## Important Interview Questions & Answers
1. **Q:** How do you keep tests maintainable across many pages?  
   **A:** Use the POM pattern to isolate locators and actions; tests only interact with methods like `loginPage.enterCredentials()` so UI changes affect only the page object.
2. **Q:** What makes the framework data-driven?  
   **A:** `ExcelUtils` reads `TestData.xlsx` so tests can loop through credentials/payloads, enabling multiple login scenarios without duplicating code.
3. **Q:** How does the framework report execution outcomes?  
   **A:** ExtentReports capture steps and screenshots, TestNG logs overall status, and `EmailUtils` can distribute the resulting HTML file to stakeholders automatically.

## Theory Knowledge for Interviews
- **Page Object Model:** Separate UI interactions (`pages/`) from business logic (`tests/`) to keep the test suite scalable and readable.
- **Reporting Best Practices:** Combine Extent (rich visuals) with TestNG/Log4j (raw data) so both human and machine stakeholders can consume results.
- **Cross-Browser & Parallel Testing:** Parameterize browsers (`-Dbrowser`) and thread counts (`-Dparallel`, `-DthreadCount`) to speed up execution without compromising isolation.

## Troubleshooting & Tips
- Keep driver binaries synced; mismatched versions often cause `SessionNotCreatedException`.
- Check `reports/ExtentReport_*.html` and `screenshots/` after failures to see the captured context.
- Update `TestData.xlsx` responsibly; column changes mean utilities must be adjusted accordingly.

## Next Steps
- Introduce CI pipeline steps (Jenkins/GitHub Actions) that run `mvn clean test` and publish the Extent report as an artifact.
- Add Visual Regression tests (Percy or Applitools) to complement the existing functional suite.
