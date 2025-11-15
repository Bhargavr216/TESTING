Supermarket Website (PHP + MySQL)

Overview
- Frontend: HTML, CSS, JS
- Backend: PHP (PDO)
- Database: MySQL (phpMyAdmin)
- Local server: XAMPP

Setup Guide (Beginner-Friendly)
1) Install XAMPP
- Download: https://www.apachefriends.org/index.html
- Install using defaults; start the XAMPP Control Panel.

2) Start Services
- In XAMPP Control Panel, click Start for `Apache` and `MySQL`.
- If Apache fails due to port 80/443, change ports in Config or stop other apps using those ports.

3) Open phpMyAdmin
- Visit `http://localhost/phpmyadmin/` in your browser.

4) Create Database and Tables
- In phpMyAdmin, click `Import`.
- Choose the `schema.sql` file from this project.
- Import to create `supermarket_db` and sample data.

5) Place Project in htdocs
- Copy the entire project folder contents into `C:\xampp\htdocs\supermarket` (create the `supermarket` folder if needed).

6) Configure Database Credentials (optional)
- Default credentials assume MySQL user `root` with empty password.
- If you use a password, open `config/config.php` and set `DB_PASS`.

7) Run the Site
- Open `http://localhost/supermarket/` in your browser.

Login and Admin
- Create an account via Sign Up.
- To access Admin panel, register using email `admin@supermarket.local` (this email gets admin access).

Test the Full Flow
1) Sign Up and Login
2) Browse Products
3) Add items to Cart from product cards
4) Open Cart, update quantities, remove items
5) Proceed to Checkout and Place Order
6) View Order History under Orders
7) If using `admin@supermarket.local`, open Admin to Add/Edit/Delete products

Project Structure
- `index.php` — Homepage with hero, offers, featured products
- `products/` — Product listing with search and category filters
- `auth/` — Register, Login, Logout
- `cart/` — Add/Update/Remove, Checkout, Place Order
- `orders/` — Order history
- `admin/` — Product CRUD (admin only)
- `partials/` — Shared header, navbar, footer
- `config/` — Database config and connection
- `public/assets/css/style.css` — Styles
- `public/assets/js/app.js` — JS
- `schema.sql` — Database schema + sample products

Notes
- Passwords are hashed using PHP `password_hash`.
- All SQL queries use prepared statements.
- Cart and orders enforce stock checks during checkout.
- UI is responsive and uses a modern dark theme.

Screenshots
- The following screenshots illustrate key pages and flows. Place images under `public/assets/screenshots/` using the suggested filenames.

1) Authentication
- Login: ![Login](public/assets/screenshots/login.png)
- Register: ![Register](public/assets/screenshots/register.png)

2) Shopping Flow
- Homepage: ![Homepage](public/assets/screenshots/home.png)
- Products listing: ![Products](public/assets/screenshots/products.png)
- Cart: ![Cart](public/assets/screenshots/cart.png)
- Checkout: ![Checkout](public/assets/screenshots/checkout.png)
- Order history: ![Orders](public/assets/screenshots/order_history.png)

3) Admin Panel
- Products management: ![Admin Products](public/assets/screenshots/admin_products.png)
- Add product: ![Admin Add Product](public/assets/screenshots/admin_add_product.png)

How to Capture Screenshots
- Run the site locally: `http://localhost/supermarket/`
- Use your browser’s screenshot tool to capture the full page for each view.
- Save PNG files to `public/assets/screenshots/` with the exact names above so the README displays them automatically.