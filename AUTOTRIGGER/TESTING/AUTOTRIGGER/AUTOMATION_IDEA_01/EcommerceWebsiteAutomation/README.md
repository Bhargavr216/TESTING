# EcommerceWebsiteAutomation — End-to-End E-commerce Journey Validation

## End-to-End Explanation
The suite validates a shopper’s journey from login through checkout and logout by invoking `EcommerceWebsiteAutomation.java`, which sequentially calls the `LoginPage`, `ApplyFilter`, `AddToCart`, `CheckoutPage`, and `LogoutPage` helpers. Each test case drives the ChromeDriver (with the tuned `ChromeOptions`) to mimic a real shopper: enter credentials → filter products → add favorites → complete checkout → verify logout and session cleanup. Every component writes detailed logs, and the build completes with Maven-managed artifacts.

## Key Components & Coverage
- **`LoginPage`**: performs authentication, credential checks, and page navigation.
- **`ApplyFilter`**: cover filters (category, price, brand) and sort toggles while validating product counts.
- **`AddToCart`**: picks multiple SKUs (`Sauce Labs Onesie`, `Sauce Labs Fleece Jacket`) and ensures the cart badge and subtotals update correctly.
- **`CheckoutPage`**: fills customer details (`Chanchal Korsewada, 492222`), validates address errors, and verifies order confirmation.
- **`LogoutPage`**: reviews session termination and redirection to the login view.
- **`ChromeOptions` & logging**: disable automation notifications, manage pop-ups, and emit consistent timestamps in the console log for traceability.

## Setup & Execution
1. Ensure **Java 17+**, **Maven 3.6+**, and **Chrome** are installed locally.
2. Clone the repo and run `mvn clean install` inside `EcommerceWebsiteAutomation`.
3. Start the entire suite with `mvn test` (the Maven project calls each `TestCase0X` in order by default).
4. Execute a specific case using `mvn test -Dtest=TestCase02` or run negative flows using custom profiles.
5. Override configuration with `-DchromeHeadless=true` or pass frequent builder properties such as `-DenableLogging=true`.

## Reporting & Observability
- **Console logs** show each step with `logStatus(...)`.
- **Status output** (pass/fail/skip) is printed after each `TestCase` and can be redirected into files.
- **Project documentation** (`PROJECT_DOCS.md`) explains business rules while `target/` contains compiled classes for quick reuse.

## Important Interview Questions & Answers
1. **Q:** How do you ensure the cart totals stay accurate when adding/removing multiple products?  
   **A:** After each `PerformAddToCartFunctionality`, the suite asserts the cart counter and totals. Tests cover multiple SKU additions (`Sauce Labs Onesie`, `Sauce Labs Fleece Jacket`) to spot rounding or pricing drift.
2. **Q:** What keeps the checkout flow resilient across environments?  
   **A:** The `CheckoutPage` method validates required fields, handles postal-code errors, and asserts the success message before returning a boolean so callers can gracefully recover from stage-dependent failures.
3. **Q:** How do you manage flaky UI elements during filtering?  
   **A:** The filtering helper waits for the loader to disappear and validates that expected product cards are visible before continuing, emulating human timing.

## Theory Knowledge for Interviews
- **Page Object Model (POM):** Separate locators and actions (in `LoginPage`, `AddToCart`, etc.) from orchestration so tests can reuse steps without brittle scripts.
- **Data-Driven vs Scripted Tests:** The suite uses multiple `TestCase` methods (same code with different payloads) illustrating balancing coverage with simplicity.
- **User Journey Testing:** Understand the golden path (login → shop → checkout) and how negative cases (invalid login, checkout omission) guard against regressions.

## Troubleshooting & Tips
- Use `mvn -U clean test` when ChromeDriver and dependencies are stale.
- Keep `ChromeOptions` tuned (`disable-automation`, password manager off) to avoid browser pop-ups that derail flows.
- Add explicit waits around filters and cart updates to defeat timing issues in slower environments.

## Next Steps
- Introduce CI artifacts to publish HTML outputs from `target/surefire-reports`.
- Extend to parallel suites covering cross-browser scenarios by abstracting the driver creation logic with `WebDriverManager` profiles.
