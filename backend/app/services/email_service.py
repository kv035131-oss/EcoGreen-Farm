"""
EcoGreen Email Notification Service
Handles HTML/Text email rendering, SMTP sending (Brevo, Gmail, custom SMTP),
SIMULATE mode for zero-credential testing, background async execution, and logging.
"""

import os
import smtplib
import logging
import threading
import uuid
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Tuple
from flask import current_app

from backend.app.extensions import db
from backend.app.models.user import User
from backend.app.models.notification import NotificationLog
from backend.app.services.notification_templates import render_message

logger = logging.getLogger('ecogreen.email_service')

SUBJECTS = {
    'order_placed_farmer': '🛒 EcoGreen: New Order Request #{order_id}',
    'payment_success_consumer': '✅ EcoGreen: Payment Confirmed - Order #{order_id}',
    'payment_success_farmer': '💰 EcoGreen: Payment Received for Order #{order_id}',
    'order_accepted_consumer': '✅ EcoGreen: Your Order #{order_id} Has Been Accepted!',
    'order_rejected_consumer': '❌ EcoGreen: Order #{order_id} Update',
    'order_delivered_consumer': '📦 EcoGreen: Order #{order_id} Delivered',
    'farmer_order_reminder': '⏰ EcoGreen Reminder: Pending Order #{order_id}',
    'low_stock_farmer': '⚠️ EcoGreen Alert: Low Stock Notification',
    'welcome_opt_in': '🎉 Welcome to EcoGreen Notifications',
    'test_message': '🧪 EcoGreen Test Email'
}

def get_email_subject(event_type: str, **kwargs) -> str:
    template = SUBJECTS.get(event_type, 'EcoGreen Notification')
    try:
        return template.format(**kwargs)
    except Exception:
        return template

def build_html_email(subject: str, message: str, username: str) -> str:
    """Wraps notification text into a sleek, responsive HTML email template."""
    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{subject}</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f8fafc; margin: 0; padding: 0; color: #1e293b; }}
        .container {{ max-width: 600px; margin: 20px auto; background: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); border: 1px solid #e2e8f0; }}
        .header {{ background: linear-gradient(135deg, #059669 0%, #10b981 100%); color: #ffffff; padding: 24px; text-align: center; }}
        .header h1 {{ margin: 0; font-size: 22px; font-weight: 700; letter-spacing: -0.5px; }}
        .content {{ padding: 28px 24px; line-height: 1.6; font-size: 15px; }}
        .greeting {{ font-weight: 600; font-size: 16px; margin-bottom: 16px; color: #0f172a; }}
        .message-card {{ background: #f0fdf4; border-left: 4px solid #059669; padding: 16px; border-radius: 6px; margin: 20px 0; font-size: 15px; color: #14532d; }}
        .footer {{ background: #f1f5f9; padding: 16px 24px; text-align: center; font-size: 12px; color: #64748b; border-top: 1px solid #e2e8f0; }}
        .footer a {{ color: #059669; text-decoration: none; font-weight: 600; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🌱 EcoGreen Marketplace</h1>
        </div>
        <div class="content">
            <div class="greeting">Hello {username},</div>
            <p>You have a new update regarding your EcoGreen activity:</p>
            <div class="message-card">
                {message}
            </div>
            <p>Please log in to your EcoGreen dashboard to view details and manage your orders.</p>
        </div>
        <div class="footer">
            <p>EcoGreen Direct Farmer-to-Consumer Marketplace</p>
            <p>This is an automated notification. Please do not reply directly to this email.</p>
        </div>
    </div>
</body>
</html>"""


# =========================================================================
# EMAIL PROVIDERS
# =========================================================================

class BaseEmailProvider:
    def send(self, to_email: str, subject: str, body_text: str, body_html: str) -> Tuple[str, Optional[str], Optional[str]]:
        raise NotImplementedError

class SimulateEmailProvider(BaseEmailProvider):
    def send(self, to_email: str, subject: str, body_text: str, body_html: str) -> Tuple[str, Optional[str], Optional[str]]:
        msg_id = f"EMAIL_SIM_{uuid.uuid4().hex[:10].upper()}"
        logger.info(f"[SIMULATED EMAIL SENT] To: {to_email} | ID: {msg_id}\nSubject: {subject}\nBody: {body_text}\n" + "-"*50)
        return 'simulated', msg_id, None

class SMTPEmailProvider(BaseEmailProvider):
    def __init__(self):
        self.server_host = os.environ.get('SMTP_SERVER', 'smtp-relay.brevo.com').strip()
        self.server_port = int(os.environ.get('SMTP_PORT', '587').strip())
        self.username = os.environ.get('SMTP_USERNAME', '').strip()
        self.password = os.environ.get('SMTP_PASSWORD', '').strip()
        self.sender_email = os.environ.get('SENDER_EMAIL', self.username or 'noreply@ecogreen.com').strip()

    def send(self, to_email: str, subject: str, body_text: str, body_html: str) -> Tuple[str, Optional[str], Optional[str]]:
        if not self.username or not self.password:
            err_msg = "SMTP credentials missing! Set SMTP_USERNAME and SMTP_PASSWORD in .env"
            logger.warning(f"[SMTP WARNING] {err_msg}")
            return 'failed', None, err_msg

        msg_id = f"SMTP_{uuid.uuid4().hex[:10].upper()}"
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"EcoGreen Marketplace <{self.sender_email}>"
        msg['To'] = to_email

        part1 = MIMEText(body_text, 'plain')
        part2 = MIMEText(body_html, 'html')
        msg.attach(part1)
        msg.attach(part2)

        try:
            if self.server_port == 465:
                with smtplib.SMTP_SSL(self.server_host, self.server_port, timeout=15) as server:
                    server.login(self.username, self.password)
                    server.sendmail(self.sender_email, [to_email], msg.as_string())
            else:
                with smtplib.SMTP(self.server_host, self.server_port, timeout=15) as server:
                    server.ehlo()
                    server.starttls()
                    server.ehlo()
                    server.login(self.username, self.password)
                    server.sendmail(self.sender_email, [to_email], msg.as_string())

            logger.info(f"[SMTP EMAIL SENT SUCCESS] To: {to_email} | ID: {msg_id}")
            return 'sent', msg_id, None
        except smtplib.SMTPAuthenticationError as e:
            err_msg = f"SMTP Authentication Failed (Code {e.smtp_code}): {e.smtp_error.decode('utf-8', errors='ignore') if isinstance(e.smtp_error, bytes) else str(e.smtp_error)}"
            logger.error(f"[SMTP AUTH ERROR] {err_msg}")
            return 'failed', None, err_msg
        except smtplib.SMTPResponseException as e:
            err_msg = f"SMTP Response Error (Code {e.smtp_code}): {e.smtp_error.decode('utf-8', errors='ignore') if isinstance(e.smtp_error, bytes) else str(e.smtp_error)}"
            logger.error(f"[SMTP RESPONSE ERROR] {err_msg}")
            return 'failed', None, err_msg
        except Exception as e:
            err_msg = f"SMTP Transmission Failure: {str(e)}"
            logger.error(f"[SMTP ERROR] {err_msg}")
            return 'failed', None, err_msg


def get_active_email_provider() -> BaseEmailProvider:
    mode = os.environ.get('EMAIL_NOTIFY_MODE', 'simulate').strip().lower()
    if mode == 'smtp':
        return SMTPEmailProvider()
    return SimulateEmailProvider()


def _execute_send_email(app, user_id: int, event_type: str, subject: str, message: str, to_email: str):
    with app.app_context():
        user = User.query.get(user_id)
        if not user:
            return

        provider = get_active_email_provider()
        html_content = build_html_email(subject, message, user.username)

        log_entry = NotificationLog(
            user_id=user.id,
            channel='email',
            event_type=event_type,
            message=message,
            status='queued'
        )
        db.session.add(log_entry)
        db.session.commit()

        status, msg_id, error = provider.send(to_email, subject, message, html_content)
        if status in ('sent', 'simulated'):
            log_entry.status = status
            log_entry.provider_message_id = msg_id
            log_entry.error = None
        else:
            log_entry.status = 'failed'
            log_entry.error = error
        db.session.commit()


def send_email_notification(user: User, event_type: str, message: str, **kwargs):
    """Dispatches email notification asynchronously."""
    if not user or not getattr(user, 'email', None):
        return

    subject = get_email_subject(event_type, **kwargs)
    app_obj = current_app._get_current_object()
    t = threading.Thread(
        target=_execute_send_email,
        args=(app_obj, user.id, event_type, subject, message, user.email),
        daemon=True
    )
    t.start()
