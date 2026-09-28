"""
EcoGreen Database Initializer & Seeder Script
Supports PostgreSQL & SQLite databases seamlessly.

Usage:
  python backend/database/init_db.py [--seed]
"""

import sys
import os
import argparse

# Add project root to sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

from server.app import create_app
from server.models import db
from server.seed_demo import seed_demo_data

app = create_app()

def init_database(seed=True):
    print("==================================================")
    print("       EcoGreen Database Setup & Migration        ")
    print("==================================================")
    
    with app.app_context():
        db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
        if 'postgresql' in db_uri or 'postgres' in db_uri:
            print(f"[PostgreSQL] Database Engine Active")
        else:
            print(f"[SQLite] Database Engine Active ({db_uri})")
            
        print("\n1. Creating all database tables...")
        db.create_all()
        print("   [OK] Tables created successfully!")

        if seed:
            print("\n2. Seeding Indian demo data (Farmers, Products, Orders, Transactions)...")
            seed_demo_data()
            print("   [OK] Demo data seeded successfully!")

        print("\n==================================================")
        print("   [SUCCESS] Database initialization complete!")
        print("==================================================")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Initialize EcoGreen Database (PostgreSQL/SQLite)")
    parser.add_argument('--no-seed', action='store_true', help="Skip seeding demo data")
    args = parser.parse_args()

    init_database(seed=not args.no_seed)
