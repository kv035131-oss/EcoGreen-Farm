"""
EcoGreen Power BI Data Importer & Exporter Script
------------------------------------------------
This script fetches all Admin Analytics REST endpoints from your local EcoGreen app
and saves them into CSV files inside 'powerbi/datasets/'
or loads them directly into Power BI Desktop using Python Script Data Source.

Usage in Power BI Desktop:
1. Open Power BI Desktop -> Get Data -> Python script.
2. Paste this entire script and click OK.
"""

import os
import requests
import json
import pandas as pd

BASE_URL = "http://localhost:5000/api/v1/admin/analytics"
AUTH = ("admin", "admin123")

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "datasets")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def fetch_endpoint(endpoint_path, params=None):
    url = f"{BASE_URL}/{endpoint_path}"
    try:
        response = requests.get(url, auth=AUTH, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, dict):
                return pd.DataFrame([data])
            elif isinstance(data, list):
                return pd.DataFrame(data)
        else:
            print(f"Error fetching {endpoint_path}: {response.status_code} - {response.text}")
            return pd.DataFrame()
    except Exception as e:
        print(f"Failed to connect to {url}: {e}")
        return pd.DataFrame()

# 1. Platform Summary KPIs
df_summary = fetch_endpoint("summary")

# 2. Orders Over Time
df_orders_over_time = fetch_endpoint("orders-over-time", params={"interval": "day"})

# 3. Top Farmers
df_top_farmers = fetch_endpoint("top-farmers", params={"limit": 10})

# 4. Top Products
df_top_products = fetch_endpoint("top-products", params={"limit": 10})

# 5. Produce Category Breakdown
df_category_breakdown = fetch_endpoint("category-breakdown")

# 6. User Signup Growth
df_user_growth = fetch_endpoint("user-growth", params={"interval": "day"})

if __name__ == "__main__":
    print("--- Exporting EcoGreen Power BI Analytics Datasets ---")
    df_summary.to_csv(os.path.join(OUTPUT_DIR, "powerbi_summary.csv"), index=False)
    df_orders_over_time.to_csv(os.path.join(OUTPUT_DIR, "powerbi_orders_over_time.csv"), index=False)
    df_top_farmers.to_csv(os.path.join(OUTPUT_DIR, "powerbi_top_farmers.csv"), index=False)
    df_top_products.to_csv(os.path.join(OUTPUT_DIR, "powerbi_top_products.csv"), index=False)
    df_category_breakdown.to_csv(os.path.join(OUTPUT_DIR, "powerbi_category_breakdown.csv"), index=False)
    df_user_growth.to_csv(os.path.join(OUTPUT_DIR, "powerbi_user_growth.csv"), index=False)
    print(f"Export complete! CSV files created in '{OUTPUT_DIR}' for Power BI import.")
