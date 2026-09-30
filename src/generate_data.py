"""
generate_data.py
Creates a synthetic (made-up) e-commerce dataset and saves it as a CSV file.

Output: data/raw/ecommerce_raw.csv
Run from the project root:  python src/generate_data.py
"""

from pathlib import Path

import numpy as np
import pandas as pd

# A "seed" makes the random numbers repeatable: everyone gets the same data.
rng = np.random.default_rng(42)

# Find the project folder, so the script works from any terminal location.
BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"

# ---------------------------------------------------------------
# 1. PRODUCTS: 5 categories x 12 products = 60 products
# ---------------------------------------------------------------
# For each category: (lowest price, highest price, list of product names)
categories = {
    "Electronics": (40, 400, [
        "Wireless Earbuds", "Bluetooth Speaker", "Smart Watch", "Power Bank",
        "USB-C Charger", "Webcam HD", "Gaming Mouse", "Mechanical Keyboard",
        "Portable SSD", "Phone Stand", "LED Desk Lamp", "Fitness Tracker"]),
    "Home & Kitchen": (10, 120, [
        "Coffee Maker", "Air Fryer", "Non-Stick Pan", "Knife Set",
        "Blender", "Electric Kettle", "Storage Containers", "Bath Towel Set",
        "Table Lamp", "Cutting Board", "Water Bottle", "Toaster"]),
    "Clothing": (8, 90, [
        "Cotton T-Shirt", "Denim Jeans", "Hoodie", "Running Shorts",
        "Winter Jacket", "Wool Socks", "Baseball Cap", "Leather Belt",
        "Polo Shirt", "Rain Coat", "Scarf", "Sneakers"]),
    "Books": (5, 35, [
        "Python Programming Guide", "Data Science Handbook", "Business Strategy",
        "World History", "Cooking Basics", "Personal Finance", "Science Fiction Novel",
        "Mystery Novel", "Self-Improvement", "Travel Guide", "Art of Design",
        "Children's Stories"]),
    "Sports & Outdoors": (12, 150, [
        "Yoga Mat", "Dumbbell Set", "Camping Tent", "Hiking Backpack",
        "Football", "Cycling Helmet", "Resistance Bands", "Jump Rope",
        "Sleeping Bag", "Trekking Poles", "Sports Water Bottle", "Badminton Set"]),
}

product_rows = []
product_number = 1
for category, (low_price, high_price, names) in categories.items():
    for name in names:
        product_rows.append({
            "ProductID": f"P{product_number:03d}",       # P001, P002, ...
            "ProductName": name,
            "Category": category,
            "UnitPrice": round(rng.uniform(low_price, high_price), 2),
        })
        product_number += 1

products = pd.DataFrame(product_rows)

# Some products are more popular than others.
product_popularity = rng.uniform(0.3, 3.0, size=len(products))
product_popularity = product_popularity / product_popularity.sum()

# ---------------------------------------------------------------
# 2. CUSTOMERS: 500 customers
# ---------------------------------------------------------------
first_names = ["Ali", "Sara", "John", "Emma", "Omar", "Lina", "David", "Aisha",
               "Michael", "Fatima", "Daniel", "Zara", "Ahmed", "Sophie", "Hassan",
               "Olivia", "Bilal", "Laura", "Usman", "Hannah"]
last_names = ["Khan", "Smith", "Ahmed", "Brown", "Malik", "Johnson", "Hussain",
              "Miller", "Raza", "Wilson", "Sheikh", "Taylor", "Iqbal", "Davis",
              "Butt", "Clark", "Qureshi", "Lewis", "Siddiqui", "Walker"]
countries = ["United Kingdom", "United States", "Germany", "France",
             "Pakistan", "Canada", "Australia", "United Arab Emirates"]
country_probs = [0.28, 0.22, 0.14, 0.10, 0.09, 0.07, 0.05, 0.05]   # adds up to 1.0

n_customers = 500
customers = pd.DataFrame({
    "CustomerID": [f"C{i:04d}" for i in range(1, n_customers + 1)],
    "CustomerName": [
        f"{rng.choice(first_names)} {rng.choice(last_names)}" for _ in range(n_customers)
    ],
    "Country": rng.choice(countries, size=n_customers, p=country_probs),
})

# Some customers buy far more often than others (like real shops).
customer_activity = rng.gamma(shape=0.8, scale=1.0, size=n_customers)
customer_activity = customer_activity / customer_activity.sum()

# ---------------------------------------------------------------
# 3. ORDER DATES: 2023-01-01 to 2024-12-31
# ---------------------------------------------------------------
all_days = pd.date_range("2023-01-01", "2024-12-31")
day_weights = np.ones(len(all_days))
day_weights[all_days.month.isin([11, 12])] *= 1.6     # busier in Nov and Dec
day_weights = day_weights * np.linspace(1.0, 1.3, len(all_days))  # slow growth
day_weights = day_weights / day_weights.sum()

# ---------------------------------------------------------------
# 4. ORDERS AND ORDER LINES
# ---------------------------------------------------------------
n_orders = 4500
customer_list = customers.to_dict("records")
product_list = products.to_dict("records")

order_customer_positions = rng.choice(n_customers, size=n_orders, p=customer_activity)
order_day_positions = rng.choice(len(all_days), size=n_orders, p=day_weights)

rows = []
for i in range(n_orders):
    order_id = 10001 + i
    customer = customer_list[order_customer_positions[i]]
    order_date = all_days[order_day_positions[i]].strftime("%Y-%m-%d")

    # Each order has 1 to 5 different products.
    n_items = rng.choice([1, 2, 3, 4, 5], p=[0.15, 0.25, 0.30, 0.20, 0.10])
    chosen = rng.choice(len(products), size=n_items, replace=False, p=product_popularity)

    for position in chosen:
        product = product_list[position]
        rows.append({
            "OrderID": order_id,
            "OrderDate": order_date,
            "CustomerID": customer["CustomerID"],
            "CustomerName": customer["CustomerName"],
            "Country": customer["Country"],
            "ProductID": product["ProductID"],
            "ProductName": product["ProductName"],
            "Category": product["Category"],
            "Quantity": int(rng.choice([1, 2, 3, 4, 5, 10],
                                       p=[0.40, 0.25, 0.15, 0.10, 0.07, 0.03])),
            "UnitPrice": product["UnitPrice"],
        })

df = pd.DataFrame(rows)

# ---------------------------------------------------------------
# 5. A FEW REAL-WORLD STYLE ERRORS (small, and documented in the README)
# ---------------------------------------------------------------
n_rows = len(df)
bad_quantity = rng.choice(n_rows, size=20, replace=False)
df.loc[bad_quantity, "Quantity"] = rng.choice([-2, -1, 0], size=20)

bad_price = rng.choice(n_rows, size=10, replace=False)
df.loc[bad_price, "UnitPrice"] = 0.0

missing_country = rng.choice(n_rows, size=40, replace=False)
df.loc[missing_country, "Country"] = np.nan

duplicates = df.sample(n=60, random_state=42)
df = pd.concat([df, duplicates], ignore_index=True)
df = df.sort_values("OrderID", kind="stable").reset_index(drop=True)

# ---------------------------------------------------------------
# 6. SAVE
# ---------------------------------------------------------------
RAW_DIR.mkdir(parents=True, exist_ok=True)
output_path = RAW_DIR / "ecommerce_raw.csv"
df.to_csv(output_path, index=False)

print(f"Saved {len(df)} rows and {df.shape[1]} columns to {output_path}")