"""
load_data.py
Loads the cleaned CSV into a SQLite database with 4 related tables.

Input : data/processed/ecommerce_clean.csv
        sql/database_setup.sql
Output: data/processed/ecommerce.db
Run from the project root:  python src/load_data.py
"""

import sqlite3
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
CLEAN_CSV = BASE_DIR / "data" / "processed" / "ecommerce_clean.csv"
SCHEMA_FILE = BASE_DIR / "sql" / "database_setup.sql"
DB_FILE = BASE_DIR / "data" / "processed" / "ecommerce.db"

# ---------------------------------------------------------------
# 1. Read the cleaned data
# ---------------------------------------------------------------
df = pd.read_csv(CLEAN_CSV)
print("Cleaned rows loaded:", len(df))

# ---------------------------------------------------------------
# 2. Split the one big table into 4 smaller tables
# ---------------------------------------------------------------
customers = (
    df[["CustomerID", "CustomerName", "Country"]]
    .drop_duplicates(subset="CustomerID")
    .rename(columns={"CustomerID": "customer_id",
                     "CustomerName": "customer_name",
                     "Country": "country"})
)

products = (
    df[["ProductID", "ProductName", "Category", "UnitPrice"]]
    .drop_duplicates(subset="ProductID")
    .rename(columns={"ProductID": "product_id",
                     "ProductName": "product_name",
                     "Category": "category",
                     "UnitPrice": "unit_price"})
)

orders = (
    df[["OrderID", "CustomerID", "OrderDate"]]
    .drop_duplicates(subset="OrderID")
    .rename(columns={"OrderID": "order_id",
                     "CustomerID": "customer_id",
                     "OrderDate": "order_date"})
)

order_items = df[["OrderID", "ProductID", "Quantity"]].rename(
    columns={"OrderID": "order_id",
             "ProductID": "product_id",
             "Quantity": "quantity"})

# Safety checks: each ID must describe exactly ONE customer / product.
assert df.groupby("CustomerID")[["CustomerName", "Country"]].nunique().max().max() == 1
assert df.groupby("ProductID")[["ProductName", "Category", "UnitPrice"]].nunique().max().max() == 1

# ---------------------------------------------------------------
# 3. Create the database and the empty tables
# ---------------------------------------------------------------
connection = sqlite3.connect(DB_FILE)
connection.execute("PRAGMA foreign_keys = ON")   # make SQLite enforce foreign keys

connection.executescript(SCHEMA_FILE.read_text(encoding="utf-8"))

# ---------------------------------------------------------------
# 4. Fill the tables (parents first, children last)
# ---------------------------------------------------------------
customers.to_sql("customers", connection, if_exists="append", index=False)
products.to_sql("products", connection, if_exists="append", index=False)
orders.to_sql("orders", connection, if_exists="append", index=False)
order_items.to_sql("order_items", connection, if_exists="append", index=False)
connection.commit()

# ---------------------------------------------------------------
# 5. Check: do the row counts and total revenue match?
# ---------------------------------------------------------------
print("\nRows in each table:")
for table in ["customers", "products", "orders", "order_items"]:
    count = connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    print(f"  {table:<12} {count}")

sql_revenue = connection.execute(
    """
    SELECT ROUND(SUM(oi.quantity * p.unit_price), 2)
    FROM order_items AS oi
    INNER JOIN products AS p ON oi.product_id = p.product_id
    """
).fetchone()[0]
pandas_revenue = round((df["Quantity"] * df["UnitPrice"]).sum(), 2)

print("\nTotal revenue from SQL   :", sql_revenue)
print("Total revenue from Pandas:", pandas_revenue)

connection.close()
print("\nDatabase saved to:", DB_FILE)