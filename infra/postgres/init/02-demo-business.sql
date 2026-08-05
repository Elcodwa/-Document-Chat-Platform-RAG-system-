-- Creates a SEPARATE database (not the app's own database) with a small,
-- realistic e-commerce schema and sample rows. This is what the "Demo
-- Postgres" connection created by scripts/seed_demo_data.py points at -
-- it stands in for "a customer's live production database" so you have
-- something real to ask Text-to-SQL questions about immediately.
CREATE DATABASE demo_business;

\connect demo_business

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE customers (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    country TEXT NOT NULL,
    signup_date DATE NOT NULL DEFAULT CURRENT_DATE
);

CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    price NUMERIC(10, 2) NOT NULL
);

CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    customer_id INT NOT NULL REFERENCES customers(id),
    order_date DATE NOT NULL DEFAULT CURRENT_DATE,
    status TEXT NOT NULL DEFAULT 'completed',
    total NUMERIC(10, 2) NOT NULL
);

CREATE TABLE order_items (
    id SERIAL PRIMARY KEY,
    order_id INT NOT NULL REFERENCES orders(id),
    product_id INT NOT NULL REFERENCES products(id),
    quantity INT NOT NULL,
    unit_price NUMERIC(10, 2) NOT NULL
);

INSERT INTO customers (name, email, country, signup_date) VALUES
    ('Amr Hassan', 'amr.hassan@example.com', 'EG', '2024-01-15'),
    ('Salma Ibrahim', 'salma.ibrahim@example.com', 'EG', '2024-02-20'),
    ('Jane Doe', 'jane.doe@example.com', 'US', '2024-01-05'),
    ('John Smith', 'john.smith@example.com', 'US', '2024-03-01'),
    ('Fatima Noor', 'fatima.noor@example.com', 'AE', '2024-02-10'),
    ('Omar Khaled', 'omar.khaled@example.com', 'EG', '2024-04-18'),
    ('Lucas Martin', 'lucas.martin@example.com', 'FR', '2024-03-22'),
    ('Chen Wei', 'chen.wei@example.com', 'CN', '2024-05-02');

INSERT INTO products (name, category, price) VALUES
    ('Wireless Mouse', 'Electronics', 19.99),
    ('Mechanical Keyboard', 'Electronics', 79.99),
    ('USB-C Hub', 'Electronics', 34.50),
    ('Standing Desk', 'Furniture', 349.00),
    ('Office Chair', 'Furniture', 199.00),
    ('Notebook Set', 'Stationery', 9.99),
    ('Desk Lamp', 'Furniture', 45.00),
    ('Noise-Cancelling Headphones', 'Electronics', 149.99);

INSERT INTO orders (customer_id, order_date, status, total) VALUES
    (1, '2024-02-01', 'completed', 99.98),
    (1, '2024-03-14', 'completed', 349.00),
    (2, '2024-02-25', 'completed', 45.00),
    (3, '2024-01-20', 'completed', 79.99),
    (3, '2024-04-02', 'refunded', 19.99),
    (4, '2024-03-10', 'completed', 199.00),
    (5, '2024-02-15', 'completed', 34.50),
    (6, '2024-04-20', 'completed', 149.99),
    (6, '2024-05-01', 'completed', 9.99),
    (7, '2024-03-25', 'completed', 79.99),
    (8, '2024-05-05', 'pending', 199.00);

INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES
    (1, 1, 1, 19.99), (1, 2, 1, 79.99),
    (2, 4, 1, 349.00),
    (3, 7, 1, 45.00),
    (4, 2, 1, 79.99),
    (5, 1, 1, 19.99),
    (6, 5, 1, 199.00),
    (7, 3, 1, 34.50),
    (8, 8, 1, 149.99),
    (9, 6, 1, 9.99),
    (10, 2, 1, 79.99),
    (11, 5, 1, 199.00);
