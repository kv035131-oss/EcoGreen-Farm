"""
Automated Pytest Suite for EcoGreen WhatsApp & In-App Notifications System
"""

import pytest
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.app import create_app
from backend.app.extensions import db
from backend.app.models import User, NotificationLog, Notification
from backend.app.utils.validators import normalize_phone
from backend.app.services.notification_templates import render_message
from backend.app.services.notification_service import notify
from werkzeug.security import generate_password_hash

@pytest.fixture
def app_instance():
    os.environ['NOTIFY_MODE'] = 'simulate'
    app = create_app('testing')
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app_instance):
    return app_instance.test_client()


# =========================================================================
# 1. PHONE NORMALIZER TESTS
# =========================================================================

def test_phone_normalizer():
    assert normalize_phone('9876543210') == '+919876543210'
    assert normalize_phone('919876543210') == '+919876543210'
    assert normalize_phone('+919876543210') == '+919876543210'
    assert normalize_phone('+91 98765-43210') == '+919876543210'
    assert normalize_phone(' 87654 32109 ') == '+918765432109'
    
    assert normalize_phone(None) is None
    assert normalize_phone('') is None
    assert normalize_phone('12345') is None
    assert normalize_phone('abcdefghij') is None


# =========================================================================
# 2. TEMPLATE RENDERING TESTS
# =========================================================================

def test_template_rendering_languages():
    msg_en = render_message('order_placed_farmer', 'en', order_id=101, quantity=10, product_name='Tomatoes', consumer_name='Aarav')
    assert "New Order #101" in msg_en

    msg_hi = render_message('order_placed_farmer', 'hi', order_id=102, quantity=5, product_name='आलू', consumer_name='Aarav')
    assert "नया ऑर्डर #102" in msg_hi or "ऑर्डर" in msg_hi


# =========================================================================
# 3. NOTIFICATION DISPATCH & LOGGING TESTS
# =========================================================================

def test_notification_logging(app_instance):
    with app_instance.app_context():
        user = User(
            username='test_user_notif',
            email='testnotif@ecogreen.com',
            phone_number='9876543210',
            password=generate_password_hash('pass123'),
            user_type='consumer',
            whatsapp_opt_in=True
        )
        db.session.add(user)
        db.session.commit()

        notify(user, 'payment_success_consumer', order_id=501, amount=1200.0, product_name='Mangoes', receipt_no='RZP-1234')
        
        # In-app notification creation assertion
        in_app = Notification.query.filter_by(user_id=user.id).first()
        assert in_app is not None
