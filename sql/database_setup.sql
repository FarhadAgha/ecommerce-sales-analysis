-- database_setup.sql
-- Creates the 4 tables of the e-commerce database (SQLite).
-- Run order matters: we delete "child" tables first, then "parent" tables.

DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS customers;

-- One row per customer
CREATE TABLE customers (
    customer_id    TEXT PRIMARY KEY,
    customer_name  TEXT NOT NULL,
    country        TEXT NOT NULL
);

-- One row per product
CREATE TABLE products (
    product_id     TEXT PRIMARY KEY,
    product_name   TEXT NOT NULL,
    category       TEXT NOT NULL,
    unit_price     REAL NOT NULL CHECK (unit_price > 0)
);

-- One row per order (who bought, and when)
CREATE TABLE orders (
    order_id       INTEGER PRIMARY KEY,
    customer_id    TEXT NOT NULL,
    order_date     TEXT NOT NULL,          -- stored as text: 'YYYY-MM-DD'
    FOREIGN KEY (customer_id) REFERENCES customers (customer_id)
);

-- One row per product inside an order
CREATE TABLE order_items (
    order_id       INTEGER NOT NULL,
    product_id     TEXT NOT NULL,
    quantity       INTEGER NOT NULL CHECK (quantity > 0),
    PRIMARY KEY (order_id, product_id),
    FOREIGN KEY (order_id)   REFERENCES orders (order_id),
    FOREIGN KEY (product_id) REFERENCES products (product_id)
);