"""
EcoGreen Notification Service
Handles phone normalization, provider abstraction (Simulate vs Meta),
multi-language message rendering, background execution with retries,
and database logging (NotificationLog & Notification models).
"""

import os
import re
import time
import logging
import threading
import uuid
from typing import Optional, Tuple
from flask import current_app

from server.models import db, User, NotificationLog, Notification
from server.notification_templates import render_message

logger = logging.getLogger('ecogreen.notifications')
logging.basicConfig(level=logging.INFO)

# ==========================================
# 1. PHONE NUMBER NORMALIZER
# ==========================================

def normalize_phone(phone_input: Optional[str]) -> Optional[str]:
    """
    Normalizes Indian & international phone numbers into E.164 format (+91XXXXXXXXXX).
    Accepts: '9876543210', '919876543210', '+919876543210', '98765-43210', '+91 98765 43210'
    Returns: '+919876543210' or None if invalid.
    """
    if not phone_input:
        return None
    
    # Strip spaces, dashes, brackets
    cleaned = re.sub(r'[\s\-\(\)]', '', str(phone_input).strip())
    
    if not cleaned:
        return None
        
    # If starting with +, validate digits
    if cleaned.startswith('+'):
        digits = cleaned[1:]
        if digits.isdigit() and 10 <= len(digits) <= 15:
            return cleaned
        return None
        
    # If 10-digit Indian number starting with 6,7,8,9
    if len(cleaned) == 10 and cleaned.isdigit() and cleaned[0] in '6789':
        return f"+91{cleaned}"
        
    # If 12-digit starting with 91
    if len(cleaned) == 12 and cleaned.isdigit() and cleaned.startswith('91'):
        return f"+{cleaned}"
        
    # Standard 10-15 digit fallback
    if cleaned.isdigit() and 10 <= len(cleaned) <= 15:
        return f"+91{cleaned[-10:]}"
        
    return None


# ==========================================
# 2. PROVIDER ABSTRACTION
# ==========================================

class BaseProvider:
    def send(self, to_phone: str, message: str) -> Tuple[str, Optional[str], Optional[str]]:
        raise NotImplementedError

class SimulateProvider(BaseProvider):
    def send(self, to_phone: str, message: str) -> Tuple[str, Optional[str], Optional[str]]:
        sid = f"SIM_{uuid.uuid4().hex[:10].upper()}"
        logger.info(f"[SIMULATED WHATSAPP] To: {to_phone} | ID: {sid}\nBody:\n{message}\n" + "-"*50)
        return 'simulated', sid, None

class MetaWhatsAppProvider(BaseProvider):
    def send(self, to_phone: str, message: str) -> Tuple[str, Optional[str], Optional[str]]:
        sid = f"META_{uuid.uuid4().hex[:10].upper()}"
        logger.info(f"[META WHATSAPP STUB] To: {to_phone} | ID: {sid}\nBody:\n{message}\n" + "-"*50)
        return 'simulated', sid, None


def get_active_provider() -> BaseProvider:
    mode = os.environ.get('NOTIFY_MODE', 'simulate').strip().lower()
    if mode == 'meta':
        return MetaWhatsAppProvider()
    return SimulateProvider()


# ==========================================
# 3. ASYNCHRONOUS NOTIFIER WITH RETRIES
# ==========================================

def _execute_send(app, user_id: int, event_type: str, message: str, to_phone: str):
    """Executes message dispatch in a background thread with retry logic."""
    with app.app_context():
        user = User.query.get(user_id)
        if not user:
            logger.error(f"User {user_id} not found for notification dispatch.")
            return

        provider = get_active_provider()
        log_entry = NotificationLog(
            user_id=user.id,
            channel='whatsapp',
            event_type=event_type,
            message=message,
            status='queued'
        )
        db.session.add(log_entry)
        db.session.commit()

        max_retries = 3
        delay = 1.0

        for attempt in range(1, max_retries + 1):
            status, sid, error = provider.send(to_phone, message)

            if status in ('sent', 'simulated'):
                log_entry.status = status
                log_entry.provider_message_id = sid
                log_entry.error = None
                db.session.commit()
                return
            else:
                log_entry.status = 'failed'
                log_entry.error = f"Attempt {attempt}/{max_retries} failed: {error}"
                db.session.commit()
                
                if attempt < max_retries:
                    time.sleep(delay)
                    delay *= 2.0


from server.email_service import send_email_notification

def notify(user: User, event_type: str, **data) -> Optional[NotificationLog]:
    """
    Main notification dispatcher.
    - Always creates an in-app Notification object.
    - Sends Email Notification to user's registered email address.
    - If user has whatsapp_opt_in=True and valid phone, sends WhatsApp message asynchronously.
    - Completely safe: failure will NEVER throw or break calling business logic.
    """
    if not user:
        return None

    try:
        lang = getattr(user, 'notification_language', 'en') or 'en'
        rendered_msg = render_message(event_type, lang=lang, **data)

        # 1. Always create In-App Notification
        in_app = Notification(
            user_id=user.id,
            message=rendered_msg,
            type=event_type,
            is_read=False
        )
        db.session.add(in_app)
        db.session.commit()

        # 2. Always Send Email Notification
        send_email_notification(user, event_type, rendered_msg, **data)

        # 3. Check WhatsApp Opt-In
        if not getattr(user, 'whatsapp_opt_in', False):
            logger.info(f"User '{user.username}' has not opted into WhatsApp. In-app & Email notifications created.")
            return None

        phone = normalize_phone(getattr(user, 'phone', None) or getattr(user, 'phone_number', None))
        if not phone:
            logger.warning(f"User '{user.username}' opted in but has invalid phone number. Skipping WhatsApp.")
            return None

        # 4. Background Async WhatsApp Send
        app_obj = current_app._get_current_object()
        t = threading.Thread(
            target=_execute_send,
            args=(app_obj, user.id, event_type, rendered_msg, phone),
            daemon=True
        )
        t.start()

    except Exception as e:
        logger.error(f"Error in notify dispatcher for user '{getattr(user, 'username', 'unknown')}': {e}")

    return None


