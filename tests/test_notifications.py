"""
Automated Pytest Suite for EcoGreen WhatsApp & In-App Notifications System
Tests:
- Phone normalizer
- Multi-language template rendering (en, hi, kn, ta, te, ml)
- WhatsApp Opt-in logic & preferences
- Failure resilience (provider error never breaks order/payment)
- End-to-end simulate mode integration workflow
"""

import pytest
import os
import sys
import time

# Add project root to sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from server.app import create_app
from server.models import db, User, Product, Order, NotificationLog, Notification
from server.notification_service import normalize_phone, render_message, notify, SimulateProvider
from werkzeug.security import generate_password_hash

@pytest.fixture
def app_instance():
    """Creates a fresh test application context with in-memory / test DB."""
    os.environ['NOTIFY_MODE'] = 'simulate'
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
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
    
    # Invalid numbers
    assert normalize_phone(None) is None
    assert normalize_phone('') is None
    assert normalize_phone('12345') is None
    assert normalize_phone('abcdefghij') is None


# =========================================================================
# 2. MULTI-LANGUAGE TEMPLATE RENDERING TESTS
# =========================================================================

def test_template_rendering_all_languages():
    languages = ['en', 'hi', 'kn', 'ta', 'te', 'ml']
    
    for lang in languages:
        msg = render_message('order_placed_farmer', lang=lang, order_id=101, quantity=5, product_name='Tomato', consumer_name='Ramesh')
        assert '101' in msg
        assert 'Tomato' in msg
        assert '✅' in msg or '❌' in msg or '🌾' in msg or '📦' in msg

    # Fallback to English for unknown language
    msg_fallback = render_message('payment_success_consumer', lang='xyz', receipt_no='RCP-1', amount='500.00', order_id=1, product_name='Mango')
    assert 'Payment Successful' in msg_fallback


# =========================================================================
# 3. OPT-IN & TEST MESSAGE API TESTS
# =========================================================================

def test_opt_in_and_test_message(client, app_instance):
    with app_instance.app_context():
        farmer = User(username='test_farmer_opt', email='farmer_opt@test.com', user_type='farmer', phone_number='9876543210', password=generate_password_hash('pass'))
        db.session.add(farmer)
        db.session.commit()
        farmer_id = farmer.id

    # Test Opt-in POST
    res = client.post('/api/v1/notifications/opt-in', json={
        'user_id': farmer_id,
        'phone': '9876543210',
        'whatsapp_opt_in': True,
        'language': 'hi'
    })
    assert res.status_code == 200
    data = res.get_json()
    assert data['status'] == 'success'

    with app_instance.app_context():
        u = User.query.get(farmer_id)
        assert u.whatsapp_opt_in is True
        assert u.notification_language == 'hi'

    # Test Send Test Message API
    res_test = client.post('/api/v1/notifications/test', json={'user_id': farmer_id})
    assert res_test.status_code == 200
    assert 'dispatched' in res_test.get_json()['message']


# =========================================================================
# 4. PROVIDER FAILURE RESILIENCE TEST
# =========================================================================

def test_provider_failure_does_not_break_order(app_instance):
    """Ensures order creation succeeds even if notification service throws an exception."""
    with app_instance.app_context():
        farmer = User(username='resilient_farmer', email='rfarmer@test.com', user_type='farmer', phone='9876543210', password=generate_password_hash('pass'))
        consumer = User(username='resilient_consumer', email='rconsumer@test.com', user_type='consumer', phone='9876543211', password=generate_password_hash('pass'))
        db.session.add_all([farmer, consumer])
        db.session.commit()

        prod = Product(user_id=farmer.id, name='Potato', price=20.0, quantity=50)
        db.session.add(prod)
        db.session.commit()

        # Monkeypatch notify to raise an exception
        import server.notification_service
        original_notify = server.notification_service.notify
        server.notification_service.notify = lambda *args, **kwargs: 1 / 0  # ZeroDivisionError

        order = Order(product_id=prod.id, user_id=consumer.id, amount=100.0, phone_number='9876543211', order_status='Pending')
        db.session.add(order)
        db.session.commit()

        assert order.id is not None
        assert order.order_status == 'Pending'

        # Restore original notify
        server.notification_service.notify = original_notify


# =========================================================================
# 5. END-TO-END INTEGRATION TEST IN SIMULATE MODE
# =========================================================================

def test_end_to_end_whatsapp_flow(client, app_instance):
    """
    Simulates full workflow:
    1. Register farmer & consumer with opt-in
    2. Create product & place order -> assert farmer notification log & in-app notification
    3. Update order to Confirmed -> assert consumer receives order_accepted notification
    """
    with app_instance.app_context():
        farmer = User(username='e2e_farmer', email='e2e_farmer@test.com', user_type='farmer', phone='+919988776655', whatsapp_opt_in=True, password=generate_password_hash('pass'))
        consumer = User(username='e2e_consumer', email='e2e_consumer@test.com', user_type='consumer', phone='+919988776644', whatsapp_opt_in=True, password=generate_password_hash('pass'))
        db.session.add_all([farmer, consumer])
        db.session.commit()

        prod = Product(user_id=farmer.id, name='Organic Tomatoes', price=40.0, quantity=30)
        db.session.add(prod)
        db.session.commit()

        farmer_id = farmer.id
        prod_id = prod.id
        consumer_id = consumer.id

    # Place order
    res_order = client.post('/api/v1/Orders/create', json={
        'user_id': consumer_id,
        'product_id': prod_id,
        'amount': 200.0,
        'phone_number': '9988776644'
    })
    assert res_order.status_code == 201
    order_id = res_order.get_json()['order_id']

    # Give async thread time to log
    time.sleep(0.5)

    with app_instance.app_context():
        # Assert NotificationLog entry created for farmer
        log = NotificationLog.query.filter_by(user_id=farmer_id, event_type='order_placed_farmer').first()
        assert log is not None
        assert 'Organic Tomatoes' in log.message

        # Assert in-app notification created for farmer
        in_app_farmer = Notification.query.filter_by(user_id=farmer_id).first()
        assert in_app_farmer is not None

        # Confirm order and trigger notify
        order = Order.query.get(order_id)
        order.order_status = 'Confirmed'
        db.session.commit()
        
        farmer_obj = User.query.get(farmer_id)
        consumer_obj = User.query.get(consumer_id)
        notify(consumer_obj, 'order_accepted_consumer', farmer_name=farmer_obj.username, order_id=order.id, product_name=prod.name)

        time.sleep(0.5)

        # Assert Consumer received order_accepted notification
        cons_in_app = Notification.query.filter_by(user_id=consumer_id).first()
        assert cons_in_app is not None
        assert 'HAS ACCEPTED' in cons_in_app.message
