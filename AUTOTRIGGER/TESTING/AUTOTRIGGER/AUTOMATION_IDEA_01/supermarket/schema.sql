CREATE DATABASE IF NOT EXISTS supermarket_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE supermarket_db;

CREATE TABLE IF NOT EXISTS users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  email VARCHAR(190) NOT NULL UNIQUE,
  password VARCHAR(255) NOT NULL
);

CREATE TABLE IF NOT EXISTS products (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(150) NOT NULL,
  category VARCHAR(100) NOT NULL,
  description TEXT,
  price DECIMAL(10,2) NOT NULL,
  stock INT NOT NULL DEFAULT 0,
  image_url VARCHAR(255) NOT NULL
);

CREATE TABLE IF NOT EXISTS cart (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  product_id INT NOT NULL,
  quantity INT NOT NULL DEFAULT 1,
  CONSTRAINT fk_cart_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  CONSTRAINT fk_cart_product FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS orders (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  total_amount DECIMAL(10,2) NOT NULL,
  created_at DATETIME NOT NULL,
  CONSTRAINT fk_orders_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS order_items (
  id INT AUTO_INCREMENT PRIMARY KEY,
  order_id INT NOT NULL,
  product_id INT NOT NULL,
  quantity INT NOT NULL,
  price DECIMAL(10,2) NOT NULL,
  CONSTRAINT fk_order_items_order FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
  CONSTRAINT fk_order_items_product FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

INSERT INTO products (name, category, description, price, stock, image_url) VALUES
('Bananas', 'Fruits', 'Fresh ripe bananas', 1.49, 120, 'https://images.unsplash.com/photo-1573679428415-1edc6df7f11a?q=80&w=600&auto=format&fit=crop'),
('Apples', 'Fruits', 'Crisp red apples', 2.99, 80, 'https://images.unsplash.com/photo-1567306226416-28f0efdc88ce?q=80&w=600&auto=format&fit=crop'),
('Broccoli', 'Vegetables', 'Green broccoli heads', 1.99, 60, 'https://images.unsplash.com/photo-1510627498534-cf7e9002facc?q=80&w=600&auto=format&fit=crop'),
('Chips', 'Snacks', 'Crunchy potato chips', 2.49, 150, 'https://images.unsplash.com/photo-1593446293091-4c0ff1ebb64e?q=80&w=600&auto=format&fit=crop'),
('Cola', 'Beverages', 'Refreshing cola drink', 1.29, 200, 'https://images.unsplash.com/photo-1584269600227-6232b31d25d9?q=80&w=600&auto=format&fit=crop'),
('Milk', 'Essentials', 'Whole milk 1L', 1.59, 100, 'https://images.unsplash.com/photo-1588624807293-4aafdbfd5c1a?q=80&w=600&auto=format&fit=crop'),
('Bread', 'Essentials', 'Whole wheat bread', 1.99, 100, 'https://images.unsplash.com/photo-1604908554021-80f8475baf97?q=80&w=600&auto=format&fit=crop'),
('Orange Juice', 'Beverages', '100% pure orange juice', 3.49, 75, 'https://images.unsplash.com/photo-1540617006-731d07727b58?q=80&w=600&auto=format&fit=crop');