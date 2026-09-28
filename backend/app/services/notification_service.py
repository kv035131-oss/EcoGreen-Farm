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

from backend.app.extensions import db
from backend.app.models.user import User
from backend.app.models.notification import NotificationLog, Notification
from backend.app.services.notification_templates import render_message
from backend.app.services.email_service import send_email_notification
from backend.app.utils.validators import normalize_phone

logger = logging.getLogger('ecogreen.notifications')
logging.basicConfig(level=logging.INFO)

# ==========================================
# PROVIDER ABSTRACTION
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
# ASYNCHRONOUS NOTIFIER WITH RETRIES
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
