#!/usr/bin/env python3
"""
EcoGreen Brevo SMTP Test Script
Sends a real test email via SMTPEmailProvider and prints exact SMTP status & diagnostics.

Usage:
  python send_test_email.py [recipient_email]

Examples:
  python send_test_email.py farmer_ajay@example.com
"""

import sys
import os
import argparse
from typing import Optional

# Add project directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    parser = argparse.ArgumentParser(description="Send test email via EcoGreen Brevo SMTP configuration.")
    parser.add_argument('email', nargs='?', default=None, help="Recipient email address (defaults to SENDER_EMAIL or farmer ajay's email)")
    args = parser.parse_args()

    from server.app import create_app
    from server.models import db, User
    from server.email_service import SMTPEmailProvider, build_html_email

    app = create_app()
    with app.app_context():
        # Retrieve target email
        target_email = args.email
        if not target_email:
            ajay = User.query.filter((User.username == 'ajay') | (User.username.ilike('%ajay%'))).first()
            if ajay and ajay.email:
                target_email = ajay.email
            else:
                target_email = os.environ.get('SENDER_EMAIL') or os.environ.get('SMTP_USERNAME')

        if not target_email:
            print("❌ Error: No target recipient email provided or found. Pass an email as argument: python send_test_email.py <email>")
            sys.exit(1)

        print("\n" + "="*60)
        print("         ECOGREEN BREVO SMTP TEST DISPATCHER         ")
        print("="*60)
        print(f"SMTP Mode     : {os.environ.get('EMAIL_NOTIFY_MODE', 'simulate')}")
        print(f"SMTP Host     : {os.environ.get('SMTP_SERVER', 'smtp-relay.brevo.com')}:{os.environ.get('SMTP_PORT', '587')}")
        print(f"SMTP Username : {os.environ.get('SMTP_USERNAME', '(Not Set)')}")
        print(f"Sender Email  : {os.environ.get('SENDER_EMAIL', '(Not Set)')}")
        print(f"Recipient     : {target_email}")
        print("="*60 + "\n")

        provider = SMTPEmailProvider()
        subject = "EcoGreen Brevo SMTP Test Email"
        body_text = f"Hello! This is a test email sent from EcoGreen to {target_email} using Brevo SMTP relay."
        body_html = build_html_email(subject, body_text, target_email.split('@')[0])

        print("Attempting SMTP transmission via STARTTLS on port 587...")
        status, msg_id, error = provider.send(target_email, subject, body_text, body_html)

        print("\n" + "-"*60)
        if status == 'sent':
            print(f"[SUCCESS] Test email dispatched cleanly.")
            print(f"   Status     : {status.upper()}")
            print(f"   Message ID : {msg_id}")
            print(f"   Recipient  : {target_email}")
        else:
            print(f"[FAILURE] SMTP transmission encountered an error.")
            print(f"   Status     : {status.upper()}")
            print(f"   Exact Error: {error}")
            print("\nBrevo Troubleshooting Tips:")
            print("  1. Verify SMTP_USERNAME is your Brevo login email.")
            print("  2. Verify SMTP_PASSWORD is your active Brevo SMTP key (from Brevo > SMTP & API).")
            print("  3. Verify SENDER_EMAIL matches an authorized/verified sender in Brevo (Senders & IP).")
        print("-" * 60 + "\n")

if __name__ == '__main__':
    main()
