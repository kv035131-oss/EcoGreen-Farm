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
            "ALTER TABLE \"transaction\" ADD COLUMN currency VARCHAR(10) DEFAULT 'INR'",
            'ALTER TABLE "transaction" ADD COLUMN payment_method VARCHAR(50)',
            'ALTER TABLE "transaction" ADD COLUMN transaction_date DATETIME',
            "ALTER TABLE product ADD COLUMN moderation_status VARCHAR(50) DEFAULT 'approved'",
            'ALTER TABLE product ADD COLUMN moderation_reason TEXT',
            'ALTER TABLE product ADD COLUMN moderated_at DATETIME',
            'ALTER TABLE product ADD COLUMN moderated_by VARCHAR(100)',
            'ALTER TABLE product ADD COLUMN address_text TEXT',
            'ALTER TABLE product ADD COLUMN latitude FLOAT',
            'ALTER TABLE product ADD COLUMN longitude FLOAT',
            'ALTER TABLE product ADD COLUMN district VARCHAR(100)',
            'ALTER TABLE product ADD COLUMN state VARCHAR(100)',
            'ALTER TABLE "order" ADD COLUMN delivery_address_text TEXT',
            'ALTER TABLE "order" ADD COLUMN delivery_latitude FLOAT',
            'ALTER TABLE "order" ADD COLUMN delivery_longitude FLOAT',
            'ALTER TABLE "order" ADD COLUMN delivery_district VARCHAR(100)',
            'ALTER TABLE "order" ADD COLUMN delivery_state VARCHAR(100)',
            'ALTER TABLE user ADD COLUMN flagged BOOLEAN DEFAULT 0',
            'ALTER TABLE user ADD COLUMN flag_note TEXT',
            'ALTER TABLE product_moderation_log ADD COLUMN user_id INTEGER',
            'ALTER TABLE product ADD COLUMN is_deleted BOOLEAN DEFAULT 0',
            'ALTER TABLE product ADD COLUMN deleted_at DATETIME'
        ]

        for stmt in statements:
            try:
                db.session.execute(text(stmt))
                db.session.commit()
                print(f"[Schema Patch Success] {stmt}")
            except Exception as e:
                db.session.rollback()
                print(f"[Schema Patch Note] Column already exists or skipped: {e}")

        # Ensure existing null moderation_status products are set to 'approved'
        try:
            db.session.execute(text("UPDATE product SET moderation_status = 'approved' WHERE moderation_status IS NULL OR moderation_status = 'pending'"))
            db.session.commit()
        except Exception:
            db.session.rollback()


if __name__ == '__main__':
    patch_database_schema()
