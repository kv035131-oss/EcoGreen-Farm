#!/usr/bin/env python3
"""
EcoGreen Farmer Ajay Email Updater
Helper script to update farmer ajay's email address in the database.
"""

import sys
import os
import argparse

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

def main():
    parser = argparse.ArgumentParser(description="Update farmer ajay's email address in EcoGreen database.")
    parser.add_argument('email', nargs='?', default=None, help="New email address for farmer ajay")
    args = parser.parse_args()

    email_input = args.email
    if not email_input:
        print("Usage: python set_farmer_email.py <new_email_address>")
        sys.exit(1)

    from backend.app import create_app
    from backend.app.extensions import db
    from backend.app.models.user import User

    app = create_app()
    with app.app_context():
        farmer = User.query.filter((User.username == 'ajay') | (User.username.ilike('%ajay%'))).first()
        if not farmer:
            from werkzeug.security import generate_password_hash
            farmer = User(
                username='ajay',
                email=email_input,
                password=generate_password_hash('pass123'),
                user_type='farmer',
                status='Active',
                phone_number='9876543210'
            )
            db.session.add(farmer)
            print(f"Created new farmer account 'ajay' with email: {email_input}")
        else:
            old_email = farmer.email
            farmer.email = email_input
            print(f"Updated farmer 'ajay' (ID: {farmer.id}) email: {old_email} -> {email_input}")

        db.session.commit()

if __name__ == '__main__':
    main()
