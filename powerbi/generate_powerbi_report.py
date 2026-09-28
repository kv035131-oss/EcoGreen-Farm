"""
EcoGreen Power BI Executive Dashboard Report Generator
------------------------------------------------------
This script fetches all 6 EcoGreen Admin Analytics REST endpoints and saves them
into CSV files inside 'powerbi/datasets/' which can be imported into Power BI Desktop in 1 click!
"""

import os
import requests
import json
import pandas as pd

BASE_URL = "http://localhost:5000/api/v1/admin/analytics"
AUTH = ("admin", "admin123")

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "datasets")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def fetch(endpoint, params=None):
    try:
        r = requests.get(f"{BASE_URL}/{endpoint}", auth=AUTH, params=params, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if isinstance(data, dict):
                return pd.DataFrame([data])
            elif isinstance(data, list):
                return pd.DataFrame(data)
    except Exception as e:
        print(f"Error fetching {endpoint}: {e}")
    return pd.DataFrame()

print("Fetching analytics data for Power BI Report...")

df_summary = fetch("summary")
df_orders = fetch("orders-over-time", params={"interval": "day"})
df_farmers = fetch("top-farmers", params={"limit": 10})
df_products = fetch("top-products", params={"limit": 10})
df_categories = fetch("category-breakdown")
df_growth = fetch("user-growth", params={"interval": "day"})

df_summary.to_csv(os.path.join(OUTPUT_DIR, "powerbi_summary.csv"), index=False)
df_orders.to_csv(os.path.join(OUTPUT_DIR, "powerbi_orders_over_time.csv"), index=False)
df_farmers.to_csv(os.path.join(OUTPUT_DIR, "powerbi_top_farmers.csv"), index=False)
df_products.to_csv(os.path.join(OUTPUT_DIR, "powerbi_top_products.csv"), index=False)
df_categories.to_csv(os.path.join(OUTPUT_DIR, "powerbi_category_breakdown.csv"), index=False)
df_growth.to_csv(os.path.join(OUTPUT_DIR, "powerbi_user_growth.csv"), index=False)

print(f"Success! All Power BI CSV Datasets created in '{OUTPUT_DIR}'.")
