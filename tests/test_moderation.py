"""
Content Moderation System Test Suite (Gemini Vision / Simulate Engine).
Tests moderation paths: approved, rejected, needs_review, admin overrides, public filtering, and rate limiting.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
import json
from unittest.mock import patch
from datetime import datetime, timedelta

from backend.app import create_app
from backend.app.extensions import db
from backend.app.models.user import User
from backend.app.models.product import Product
from backend.app.models.moderation_log import ProductModerationLog
from backend.app.config import Config
from backend.app.services.moderation_service import moderate_product_image

@pytest.fixture
def app():
    app = create_app('backend.app.config.TestingConfig')
    app.config['MODERATION_MODE'] = 'simulate'
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def test_users(app):
    with app.app_context():
        farmer = User(username='test_farmer', email='farmer@test.com', user_type='farmer', status='Active')
        admin = User(username='admin', email='admin@test.com', user_type='admin', status='Active')
        db.session.add_all([farmer, admin])
        db.session.commit()
        return {'farmer_id': farmer.id, 'admin_id': admin.id}


# ==========================================
# 1. UNIT TESTS: MODERATION SERVICE
# ==========================================

def test_simulate_mode_approve(app):
    """Assert simulate mode approves legitimate farm produce."""
    with app.app_context():
        result = moderate_product_image('https://example.com/tomatoes.jpg', 'Vegetables', 'Fresh Tomatoes')
        assert result['decision'] == 'approved'
        assert result['matches_declared_category'] is True
        assert 'Simulated Check' in result['reason']


def test_simulate_mode_reject_prohibited_keywords(app):
    """Assert simulate mode rejects prohibited non-farm items (laptop, phone, weapon, drug)."""
    with app.app_context():
        for keyword in ['laptop', 'phone', 'weapon', 'drug']:
            result = moderate_product_image('https://example.com/photo.jpg', 'Vegetables', f'Brand New {keyword}')
            assert result['decision'] == 'rejected'
            assert result['matches_declared_category'] is False
            assert 'prohibited' in result['reason'].lower()


def test_moderation_error_defaults_to_needs_review(app):
    """Assert any exception during moderation falls back to 'needs_review' or 'unavailable', NEVER 'approved'."""
    with app.app_context():
        app.config['MODERATION_MODE'] = 'gemini'
        app.config['GEMINI_API_KEY'] = 'test_key_123'
        with patch('google.generativeai.GenerativeModel.generate_content', side_effect=Exception('Quota exceeded / Network Error')):
            result = moderate_product_image('https://example.com/item.jpg', 'Fruits', 'Fresh Apples')
            assert result['decision'] in ['needs_review', 'unavailable']
            assert result['decision'] != 'approved'
            assert 'unavailable' in result['reason'].lower() or 'error' in result['reason'].lower() or 'verify' in result['reason'].lower()





# ==========================================
# 2. PUBLIC MARKETPLACE & SEARCH FILTERING
# ==========================================

def test_public_marketplace_only_shows_approved_products(client, test_users):
    """Assert only moderation_status='approved' products appear in public API endpoints."""
    farmer_id = test_users['farmer_id']
    
    # Create an approved product and a pending/rejected product
    p_approved = Product(user_id=farmer_id, name='Approved Apples', price=10.0, quantity=20, category='Fruits', moderation_status='approved')
    p_rejected = Product(user_id=farmer_id, name='Rejected Laptop', price=500.0, quantity=1, category='Electronics', moderation_status='rejected')
    p_pending = Product(user_id=farmer_id, name='Pending Carrots', price=5.0, quantity=10, category='Vegetables', moderation_status='needs_review')
    
    db.session.add_all([p_approved, p_rejected, p_pending])
    db.session.commit()

    # Public list
    res = client.get('/api/v1/products')
    assert res.status_code == 200
    data = res.get_json()['data']
    names = [item['name'] for item in data]
    assert 'Approved Apples' in names
    assert 'Rejected Laptop' not in names
    assert 'Pending Carrots' not in names

    # Public search
    search_res = client.post('/api/v1/Search', json={'user_id': farmer_id, 'keyword': 'Laptop'})
    assert search_res.status_code == 200
    search_names = [p['name'] for p in search_res.get_json()['data']]
    assert 'Rejected Laptop' not in search_names


# ==========================================
# 3. RATE LIMITING TEST
# ==========================================

def test_product_creation_rate_limit(client, test_users):
    """Assert farmer cannot create more than 20 product listings per hour."""
    farmer_id = test_users['farmer_id']

    # Pre-populate 20 listings in the last 30 minutes
    now = datetime.utcnow()
    for i in range(20):
        p = Product(user_id=farmer_id, name=f'Produce Item {i}', price=10.0, quantity=5, category='Vegetables', created_at=now - timedelta(minutes=10))
        db.session.add(p)
    db.session.commit()

    # Attempt 21st creation
    res = client.post('/api/v1/products/create', data={
        'user_id': farmer_id,
        'name': 'Produce Item 21',
        'price': 12.0,
        'quantity': 5,
        'category': 'Vegetables'
    })

    assert res.status_code == 429
    json_resp = res.get_json()
    assert 'Rate limit exceeded' in json_resp['error']


# ==========================================
# 4. INTEGRATION TEST: END-TO-END WORKFLOW
# ==========================================

def test_moderation_end_to_end_workflow(client, test_users):
    """
    Integration Test:
    1. Farmer creates product with prohibited keyword ('laptop') -> returns HTTP 422 rejected & NO product row.
    2. Farmer creates ambiguous product ('test_review') -> returns HTTP 202 needs_review & saves product row.
    3. Assert pending product is NOT visible in public marketplace.
    4. Assert product appears in admin moderation pending queue.
    5. Admin approves product via POST /api/v1/admin/analytics/moderation/<id>/approve.
    6. Assert product NOW appears publicly in /api/v1/products.
    """
    farmer_id = test_users['farmer_id']

    # 1. Prohibited item submission is blocked synchronously (HTTP 422, error='moderation_failed')
    rej_res = client.post('/api/v1/products/create', data={
        'user_id': farmer_id,
        'name': 'Used Gaming Laptop',
        'price': 450.0,
        'quantity': 1,
        'category': 'Vegetables',
        'description': 'Working laptop photo test'
    })
    assert rej_res.status_code == 422
    assert rej_res.get_json()['error'] == 'moderation_failed'

    # 2. Ambiguous produce submission is accepted pending review (HTTP 202, status='needs_review')
    create_res = client.post('/api/v1/products/create', data={
        'user_id': farmer_id,
        'name': 'Organic Item (test_review)',
        'price': 25.0,
        'quantity': 10,
        'category': 'Vegetables',
        'description': 'Ambiguous produce item'
    })

    assert create_res.status_code == 202
    resp_data = create_res.get_json()
    assert resp_data['moderation_status'] == 'needs_review'
    product_id = resp_data['product']['id']

    # 3. Check public marketplace -> should NOT show pending review product
    pub_res = client.get('/api/v1/products')
    pub_items = [p['id'] for p in pub_res.get_json()['data']]
    assert product_id not in pub_items

    # 4. Check admin moderation pending endpoint
    admin_headers = {'Authorization': 'Basic YWRtaW46YWRtaW4xMjM='}
    pending_res = client.get('/api/v1/admin/analytics/moderation/pending', headers=admin_headers)
    assert pending_res.status_code == 200
    pending_ids = [p['id'] for p in pending_res.get_json()['data']]
    assert product_id in pending_ids

    # 5. Admin overrides decision -> approves product
    approve_res = client.post(f'/api/v1/admin/analytics/moderation/{product_id}/approve', headers=admin_headers)
    assert approve_res.status_code == 200
    assert approve_res.get_json()['status'] == 'success'

    # 6. Check public marketplace again -> product NOW visible
    pub_res_after = client.get('/api/v1/products')
    pub_items_after = [p['id'] for p in pub_res_after.get_json()['data']]
    assert product_id in pub_items_after
