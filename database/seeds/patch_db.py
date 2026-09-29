"""
Database Schema Auto-Patcher
Ensures all required columns exist in the database without destroying data.
"""

import sys
import os
from sqlalchemy import text

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.app import create_app
from backend.app.extensions import db

def patch_database_schema():
    app = create_app()
    with app.app_context():
        db.create_all()

        statements = [
            'ALTER TABLE user ADD COLUMN phone VARCHAR(50)',
            'ALTER TABLE user ADD COLUMN whatsapp_opt_in BOOLEAN DEFAULT 0',
            'ALTER TABLE user ADD COLUMN last_inbound_whatsapp_at DATETIME',
            "ALTER TABLE user ADD COLUMN notification_language VARCHAR(10) DEFAULT 'en'",
            'ALTER TABLE product ADD COLUMN created_at DATETIME',
            'ALTER TABLE "order" ADD COLUMN confirmed_at DATETIME',
            'ALTER TABLE "order" ADD COLUMN cancelled_at DATETIME',
            'ALTER TABLE "order" ADD COLUMN delivered_at DATETIME',
            'ALTER TABLE "transaction" ADD COLUMN user_id INTEGER',
            'ALTER TABLE "transaction" ADD COLUMN payment_method VARCHAR(50)',
            'ALTER TABLE "transaction" ADD COLUMN transaction_date DATETIME'
        ]

        for stmt in statements:
            try:
                db.session.execute(text(stmt))
                db.session.commit()
                print(f"[Schema Patch Success] {stmt}")
            except Exception as e:
                db.session.rollback()
                print(f"[Schema Patch Note] Column already exists or skipped: {e}")

if __name__ == '__main__':
    patch_database_schema()
