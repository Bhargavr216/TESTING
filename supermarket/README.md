Supermarket Website (PHP + MySQL)

## End-to-End Explanation
This PHP/MySQL project delivers a complete e-commerce experience: users register/login (`auth/`), browse products (`products/`), manage carts (`cart/`), place orders (`orders/`), and administrators perform product CRUD (`admin/`). The frontend (`index.php`, `partials/` for header/footer) talks to the backend via secure PHP controllers that rely on prepared statements (`config/config.php`) to talk to MySQL. The site is deployed locally through XAMPP, and sample data seeds product catalogs plus an admin email (`admin@supermarket.local`).

## Key Components & Coverage
- **`index.php`**: hero, feature callouts, product highlights, cart triggers, and responsive layout.
- **`auth/`**: registration, login, logout flows that set PHP sessions.
- **`products/`, `cart/`, `orders/`**: controllers for browsing, adding/removing items, updating cart totals, and checkout.
- **`admin/`**: product CRUD screens accessible via the `admin@supermarket.local` account.
- **`partials/`**: reusable header/footer/nav components.
- **`config/config.php`**: centralizes database credentials and PDO connection logic.
- **`schema.sql`**: defines `supermarket_db` tables plus sample products.

## Setup & Execution
1. Install **XAMPP** and start `Apache` + `MySQL` from the control panel.
2. Open `http://localhost/phpmyadmin/`, create a new database (e.g., `supermarket_db`), and import `schema.sql`.
3. Copy the project folder into `C:\\xampp\\htdocs\\supermarket\\`.
4. Update `config/config.php` if you changed MySQL credentials (default is `root` with no password).
5. Visit `http://localhost/supermarket/` and test the features (sign-up, login, carts, checkout). Use `admin@supermarket.local` for admin access.

## Reporting & Observability
- Standard PHP logging and exception handling (if enabled) track issues under `logs/` (if configured).
- Browser dev tools help verify responsive layouts and network requests during cart/checkout.
- Manual walkthroughs (sign up, add to cart, place order) provide quick regression feedback.

## Important Interview Questions & Answers
1. **Q:** How do you protect against SQL injection in this project?  
   **A:** All database interactions go through PDO prepared statements in `config/config.php`, eliminating manual concatenation of user input into queries.
2. **Q:** How does the cart persist data between requests?  
   **A:** Cart details are stored in PHP sessions and/or database tables, ensuring items remain when navigating between product and cart pages.
3. **Q:** How does admin functionality differ from user functionality?  
   **A:** Admins register with `admin@supermarket.local`, which triggers admin-specific checks (`is_admin` flag) to render the `admin/` UI for product creation and editing.

## Theory Knowledge for Interviews
- **MVC-ish PHP Structure:** While not a full framework, separation between controllers (`products/`, `cart/`), views (`partials/`), and configuration makes the design maintainable.
- **Session Management:** PHP sessions track logged-in users and carts; logouts clear the session to prevent reused credentials.
- **Prepared Statements:** They sanitize inputs at the driver level, so even strings from forms (`$_POST`) remain safe.

## Troubleshooting & Tips
- If `Apache` won’t start, free up ports 80/443 (stop Skype or another service) or change XAMPP’s listening ports.
- If database queries fail, re-import `schema.sql` and verify the `supermarket_db` tables exist with sample data.
- Use `php.ini` to enable error display during development for faster debugging.

## Next Steps
- Add PHPUnit or Behat automated tests to validate carts and checkout flows.
- Introduce API endpoints for headless frontends or mobile apps, then pair with Postman/Newman tests.
