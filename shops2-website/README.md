# Shops2-Website — Modern Landing Page + Selenium Validation

## End-to-End Explanation
The project presents a responsive e-commerce landing page (`index.html`, `style.css`, `assets/` for imagery) alongside a Selenium-based regression suite (`HomePageTests.java`). The frontend showcases hero, about, features, pricing, and footer sections, while the automation validates navigation, link behavior, and filter interactions through Maven/Selenium/TestNG. The complete experience demonstrates how a static marketing site can be paired with structured automation to keep UI journeys stable.

## Key Components & Coverage
- **`index.html` & `style.css`**: modern HTML5 structure with CSS Grid/Flexbox, gradients, and responsive breakpoints.
- **`assets/`**: optimized PNG/SVG assets and iconography for the hero, pricing, and social sections.
- **`HomePageTests.java`**: Selenium TestNG class that covers navigation, About section scroll detection, Discord link validation, and pricing filters.
- **`pom.xml`**: Maven driver for dependencies (Selenium, TestNG, WebDriverManager).
- **`README.md`, `PROJECT_DOCS.md`**: documentation of design/test decisions.

## Setup & Execution
1. Install **Java 17+**, **Maven 3.6+**, **Node.js** (optional for static server), and **Chrome** for tests.
2. Clone the repo and run `mvn clean install`.
3. Serve the frontend locally (`python -m http.server 8000` or `npx serve .`) to view `index.html`.
4. Run Selenium tests with `mvn test`.
5. Filter tests using `-Dtest=HomePageTests` or adjust browser via `-Dbrowser=chrome`.

## Reporting & Observability
- TestNG reports appear under `target/test-output/index.html` with method/class outcomes and failure details.
- Screenshots (if enabled) highlight failed UI interactions.
- Frontend assets can be inspected directly for responsive behavior and animations (see CSS `@keyframes`).

## Important Interview Questions & Answers
1. **Q:** How do you validate responsive navigation in Selenium?  
   **A:** The automation resizes the viewport via `driver.manage().window().setSize(...)` (if implemented) and checks that elements such as the mobile menu toggle display/hide as expected.
2. **Q:** Why separate frontend assets from automation logic?  
   **A:** Keeping `index.html`/`style.css` separate from `HomePageTests.java` ensures designers can iterate on UI without changing test structure; tests rely on stable selectors executed from Maven.
3. **Q:** How do you keep filters stable when product cards change?  
   **A:** The tests target high-level assertions (e.g., filter toggles update counts) rather than brittle XPaths so the automation survives minor DOM reshuffles.

## Theory Knowledge for Interviews
- **Responsive Design Principles:** Mobile-first breakpoints, CSS Grid/Flexbox, and AOS-based scroll animations form the UI foundation.
- **Test Automation Flow:** Launch browser → use POM to interact → assert content → close (mirroring the end-to-end user path).
- **Data-driven Landing Pages:** The pricing grid uses semantic markup to keep content accessible and testable.

## Troubleshooting & Tips
- If `mvn test` fails because the site isn’t served, start a simple HTTP server (`python -m http.server`) and point Selenium to `http://localhost:8000/index.html`.
- Keep asset paths relative (no CDN) to avoid cross-origin issues during local testing.
- Use browser dev tools to verify CSS Grid/Flexbox behavior across breakpoints when tests flag layout regressions.

## Next Steps
- Add visual regression tests (Percy or Applitools) to ensure the hero/pricing sections remain pixel-perfect.
- Expand automation to include cross-browser runs by parameterizing `-Dbrowser` values in `HomePageTests.java`.
