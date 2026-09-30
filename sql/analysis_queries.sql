-- analysis_queries.sql
-- Business questions answered with SQL on the e-commerce SQLite database.
-- Revenue is never stored: it is calculated as quantity * unit_price.
-- Tables: customers, products, orders, order_items


-- ==============================================================
-- PART 1: BASICS (SELECT, WHERE, ORDER BY, LIMIT, aggregates)
-- ==============================================================

-- 1. Preview the products table
SELECT *
FROM products
LIMIT 5;

-- 2. Five most expensive Electronics products
SELECT product_name, category, unit_price
FROM products
WHERE category = 'Electronics'
ORDER BY unit_price DESC
LIMIT 5;

-- 3. Total number of orders
SELECT COUNT(*) AS total_orders
FROM orders;

-- 4. Total number of customers
SELECT COUNT(*) AS total_customers
FROM customers;

-- 5. Cheapest, most expensive and average product price
SELECT MIN(unit_price)           AS cheapest,
       MAX(unit_price)           AS most_expensive,
       ROUND(AVG(unit_price), 2) AS average_price
FROM products;

-- 6. KPI summary: revenue, units, orders, average order value
SELECT ROUND(SUM(oi.quantity * p.unit_price), 2) AS total_revenue,
       SUM(oi.quantity)                          AS total_units,
       COUNT(DISTINCT oi.order_id)               AS total_orders,
       ROUND(SUM(oi.quantity * p.unit_price)
             / COUNT(DISTINCT oi.order_id), 2)   AS avg_order_value
FROM order_items AS oi
INNER JOIN products AS p
        ON oi.product_id = p.product_id;

-- 7. Orders placed in 2024
SELECT COUNT(*) AS orders_in_2024
FROM orders
WHERE order_date >= '2024-01-01'
  AND order_date <  '2025-01-01';


-- ==============================================================
-- PART 2: GROUP BY, HAVING and JOINs
-- ==============================================================

-- 8. Revenue and units by product category
SELECT p.category,
       ROUND(SUM(oi.quantity * p.unit_price), 2) AS revenue,
       SUM(oi.quantity)                          AS units_sold
FROM order_items AS oi
INNER JOIN products AS p
        ON oi.product_id = p.product_id
GROUP BY p.category
ORDER BY revenue DESC;

-- 9. Top 10 products by revenue
SELECT p.product_name,
       p.category,
       ROUND(SUM(oi.quantity * p.unit_price), 2) AS revenue,
       SUM(oi.quantity)                          AS units_sold
FROM order_items AS oi
INNER JOIN products AS p
        ON oi.product_id = p.product_id
GROUP BY p.product_id, p.product_name, p.category
ORDER BY revenue DESC
LIMIT 10;

-- 10. Monthly revenue and number of orders
SELECT STRFTIME('%Y-%m', o.order_date)           AS year_month,
       COUNT(DISTINCT o.order_id)                AS orders,
       ROUND(SUM(oi.quantity * p.unit_price), 2) AS revenue
FROM order_items AS oi
INNER JOIN orders   AS o ON oi.order_id   = o.order_id
INNER JOIN products AS p ON oi.product_id = p.product_id
GROUP BY year_month
ORDER BY year_month;

-- 11. Revenue by country (joins four tables)
SELECT c.country,
       COUNT(DISTINCT o.order_id)                AS orders,
       ROUND(SUM(oi.quantity * p.unit_price), 2) AS revenue
FROM order_items AS oi
INNER JOIN orders    AS o ON oi.order_id   = o.order_id
INNER JOIN customers AS c ON o.customer_id = c.customer_id
INNER JOIN products  AS p ON oi.product_id = p.product_id
GROUP BY c.country
ORDER BY revenue DESC;

-- 12. Top 10 customers by revenue
SELECT c.customer_id,
       c.customer_name,
       COUNT(DISTINCT o.order_id)                AS orders,
       ROUND(SUM(oi.quantity * p.unit_price), 2) AS revenue
FROM order_items AS oi
INNER JOIN orders    AS o ON oi.order_id   = o.order_id
INNER JOIN customers AS c ON o.customer_id = c.customer_id
INNER JOIN products  AS p ON oi.product_id = p.product_id
GROUP BY c.customer_id, c.customer_name
ORDER BY revenue DESC
LIMIT 10;

-- 13. Customers with 40 or more orders (HAVING filters the groups)
SELECT c.customer_id,
       c.customer_name,
       COUNT(*) AS orders
FROM orders AS o
INNER JOIN customers AS c
        ON o.customer_id = c.customer_id
GROUP BY c.customer_id, c.customer_name
HAVING COUNT(*) >= 40
ORDER BY orders DESC;


-- ==============================================================
-- PART 3: CASE WHEN, SUBQUERY, LEFT JOIN
-- ==============================================================

-- 14. Revenue by price tier (CASE WHEN)
SELECT CASE WHEN p.unit_price < 30  THEN 'Budget (under 30)'
            WHEN p.unit_price < 100 THEN 'Mid-range (30 to 99.99)'
            ELSE 'Premium (100 and above)'
       END                                       AS price_tier,
       COUNT(DISTINCT p.product_id)              AS products,
       SUM(oi.quantity)                          AS units_sold,
       ROUND(SUM(oi.quantity * p.unit_price), 2) AS revenue
FROM order_items AS oi
INNER JOIN products AS p
        ON oi.product_id = p.product_id
GROUP BY price_tier
ORDER BY revenue DESC;

-- 15. Products priced above the average (subquery)
SELECT product_name, category, unit_price
FROM products
WHERE unit_price > (SELECT AVG(unit_price) FROM products)
ORDER BY unit_price DESC;

-- 16. Customers with no orders in 2024 (LEFT JOIN + IS NULL)
SELECT c.customer_id, c.customer_name, c.country
FROM customers AS c
LEFT JOIN orders AS o
       ON c.customer_id = o.customer_id
      AND o.order_date >= '2024-01-01'
WHERE o.order_id IS NULL
ORDER BY c.customer_id;


-- ==============================================================
-- PART 4: CTEs AND WINDOW FUNCTIONS
-- ==============================================================

-- 17. Average number of units per order (CTE)
WITH order_units AS (
    SELECT order_id, SUM(quantity) AS units
    FROM order_items
    GROUP BY order_id
)
SELECT COUNT(*)              AS orders,
       ROUND(AVG(units), 2)  AS avg_units_per_order,
       MIN(units)            AS min_units,
       MAX(units)            AS max_units
FROM order_units;

-- 18. Customer segments by total revenue and each segment's share of revenue
--     (two CTEs, CASE WHEN, and a window function).
--     The segment limits (10,000 and 3,000) are our own choice.
WITH customer_revenue AS (
    SELECT o.customer_id,
           SUM(oi.quantity * p.unit_price) AS revenue
    FROM order_items AS oi
    INNER JOIN orders   AS o ON oi.order_id   = o.order_id
    INNER JOIN products AS p ON oi.product_id = p.product_id
    GROUP BY o.customer_id
),
segmented AS (
    SELECT customer_id,
           revenue,
           CASE WHEN revenue >= 10000 THEN '1 High (10,000+)'
                WHEN revenue >= 3000  THEN '2 Medium (3,000 to 9,999)'
                ELSE                       '3 Low (under 3,000)'
           END AS segment
    FROM customer_revenue
)
SELECT segment,
       COUNT(*)                                                   AS customers,
       ROUND(SUM(revenue), 2)                                     AS revenue,
       ROUND(100.0 * SUM(revenue) / SUM(SUM(revenue)) OVER (), 1) AS pct_of_revenue
FROM segmented
GROUP BY segment
ORDER BY segment;

-- 19. Products in the top 20 by units sold but in the bottom 20 by revenue
--     (CTE + RANK window function)
WITH product_totals AS (
    SELECT p.product_name,
           p.category,
           SUM(oi.quantity)                          AS units_sold,
           ROUND(SUM(oi.quantity * p.unit_price), 2) AS revenue
    FROM order_items AS oi
    INNER JOIN products AS p
            ON oi.product_id = p.product_id
    GROUP BY p.product_id, p.product_name, p.category
),
ranked AS (
    SELECT product_name,
           category,
           units_sold,
           revenue,
           RANK() OVER (ORDER BY units_sold DESC) AS units_rank,
           RANK() OVER (ORDER BY revenue DESC)    AS revenue_rank
    FROM product_totals
)
SELECT *
FROM ranked
WHERE units_rank <= 20
  AND revenue_rank > 40
ORDER BY units_rank;

-- 20. Monthly revenue and change versus the previous month (LAG window function)
WITH monthly AS (
    SELECT STRFTIME('%Y-%m', o.order_date)           AS year_month,
           ROUND(SUM(oi.quantity * p.unit_price), 2) AS revenue
    FROM order_items AS oi
    INNER JOIN orders   AS o ON oi.order_id   = o.order_id
    INNER JOIN products AS p ON oi.product_id = p.product_id
    GROUP BY year_month
)
SELECT year_month,
       revenue,
       LAG(revenue) OVER (ORDER BY year_month) AS previous_month,
       ROUND(100.0 * (revenue - LAG(revenue) OVER (ORDER BY year_month))
             / LAG(revenue) OVER (ORDER BY year_month), 1) AS change_pct
FROM monthly
ORDER BY year_month;