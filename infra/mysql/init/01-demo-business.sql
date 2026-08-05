-- Runs automatically the first time the mysql container starts (empty
-- data directory only). A second, independent sample dataset (distinct
-- from the Postgres one) so the demo shows the platform genuinely
-- querying two different database engines, not just two copies of the
-- same data.
CREATE DATABASE IF NOT EXISTS demo_business;
USE demo_business;

CREATE TABLE suppliers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    country VARCHAR(100) NOT NULL,
    rating DECIMAL(3, 2) NOT NULL DEFAULT 0
);

CREATE TABLE catalog_products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    supplier_id INT NOT NULL,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100) NOT NULL,
    unit_cost DECIMAL(10, 2) NOT NULL,
    FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
);

CREATE TABLE stock_levels (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    warehouse VARCHAR(100) NOT NULL,
    quantity_on_hand INT NOT NULL DEFAULT 0,
    FOREIGN KEY (product_id) REFERENCES catalog_products(id)
);

INSERT INTO suppliers (name, country, rating) VALUES
    ('Nile Hardware Co.', 'EG', 4.50),
    ('Pacific Components Ltd.', 'CN', 4.10),
    ('Atlas Furniture Works', 'US', 4.80),
    ('Gulf Electronics Trading', 'AE', 4.30);

INSERT INTO catalog_products (supplier_id, name, category, unit_cost) VALUES
    (1, 'Widget A2', 'Hardware', 4.25),
    (1, 'Widget B7', 'Hardware', 6.10),
    (2, 'Bluetooth Module X1', 'Electronics', 12.75),
    (2, 'LCD Panel 7-inch', 'Electronics', 28.40),
    (3, 'Oak Table Leg Set', 'Furniture', 45.00),
    (3, 'Adjustable Chair Base', 'Furniture', 32.50),
    (4, 'Power Adapter 65W', 'Electronics', 9.90),
    (4, 'USB-C Cable 2m', 'Electronics', 3.15);

INSERT INTO stock_levels (product_id, warehouse, quantity_on_hand) VALUES
    (1, 'Cairo-1', 320), (1, 'Alexandria-1', 150),
    (2, 'Cairo-1', 210),
    (3, 'Shenzhen-1', 980),
    (4, 'Shenzhen-1', 410),
    (5, 'Austin-1', 75),
    (6, 'Austin-1', 60),
    (7, 'Dubai-1', 500),
    (8, 'Dubai-1', 1200);
