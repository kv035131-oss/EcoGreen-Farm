import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from unittest.mock import patch
from flask_jwt_extended import create_access_token

from backend.app import create_app
from backend.app.extensions import db
from backend.app.models.product import Product
from backend.app.models.order import Order
from backend.app.models.user import User
from backend.app.models.moderation_log import ProductModerationLog

@pytest.fixture
def app():
    app = create_app('testing')
    app.config['MODERATION_MODE'] = 'simulate'
    with app.app_context():
        db.create_all()
        yield app

@pytest.fixture
def client(app):
    return app.test_client()


# ==============================================================================
# FEATURE A TEST CASES (Mocking Gemini API / Content Moderation Engine)
# ==============================================================================

def test_feature_a_apple_image_declared_orange_rejected(client, app):
    """
    Case 1: Apple image + declared name 'Orange' -> rejected (422),
    matches_declared_name=False, no Product row created.
    """
    mock_mod_response = {
        'decision': 'rejected',
        'detected_content': 'apple',
        'matches_declared_name': False,
        'matches_declared_category': True,
        'is_prohibited_or_unrelated': False,
        'reason': "The photo shows an apple, which does not match declared product name 'Orange'.",
        'raw_model_output': '{"simulated": true}'
    }

    with app.app_context():
        initial_count = Product.query.count()

    with patch('backend.app.routes.products.moderate_product_image', return_value=mock_mod_response):
        res = client.post('/api/v1/products/create', data={
            'name': 'Orange',
            'category': 'Fruits',
            'price': '50.0',
            'quantity': '20',
            'location': 'Mysuru',
            'image': 'https://example.com/apple.jpg'
        })

        assert res.status_code == 422
        json_data = res.get_json()
        assert json_data['error'] == 'moderation_failed'
        assert json_data['matches_declared_name'] is False
        assert 'apple' in json_data['reason'].lower() or 'apple' in json_data['detected_content'].lower()

    with app.app_context():
        final_count = Product.query.count()
        assert final_count == initial_count


def test_feature_a_laptop_image_prohibited_rejected(client, app):
    """
    Case 2: Laptop image + produce name -> rejected (422),
    is_prohibited_or_unrelated=True, no Product row created.
    """
    mock_mod_response = {
        'decision': 'rejected',
        'detected_content': 'laptop electronic device',
        'matches_declared_name': False,
        'matches_declared_category': False,
        'is_prohibited_or_unrelated': True,
        'reason': "This image doesn't show a valid farm product and cannot be listed.",
        'raw_model_output': '{"simulated": true}'
    }

    with app.app_context():
        initial_count = Product.query.count()

    with patch('backend.app.routes.products.moderate_product_image', return_value=mock_mod_response):
        res = client.post('/api/v1/products/create', data={
            'name': 'Fresh Apples',
            'category': 'Fruits',
            'price': '100.0',
            'quantity': '10',
            'location': 'Farm',
            'image': 'https://example.com/laptop.jpg'
        })

        assert res.status_code == 422
        json_data = res.get_json()
        assert json_data['error'] == 'moderation_failed'
        assert json_data['is_prohibited_or_unrelated'] is True

    with app.app_context():
        assert Product.query.count() == initial_count


def test_feature_a_matching_image_approved(client, app):
    """
    Case 3: Matching image + produce name -> approved (201).
    """
    mock_mod_response = {
        'decision': 'approved',
        'detected_content': 'Fresh Oranges',
        'matches_declared_name': True,
        'matches_declared_category': True,
        'is_prohibited_or_unrelated': False,
        'reason': "Verified produce item 'Fresh Oranges'.",
        'raw_model_output': '{"simulated": true}'
    }

    with patch('backend.app.routes.products.moderate_product_image', return_value=mock_mod_response):
        res = client.post('/api/v1/products/create', data={
            'name': 'Fresh Oranges',
            'category': 'Fruits',
            'price': '60.0',
            'quantity': '30',
            'location': 'Coorg',
            'image': 'https://example.com/orange.jpg'
        })

        assert res.status_code == 201
        json_data = res.get_json()
        assert json_data['moderation_status'] == 'approved'
        assert json_data['product']['name'] == 'Fresh Oranges'


def test_feature_a_blurry_ambiguous_image_needs_review(client, app):
    """
    Case 4: Blurry / ambiguous mock response -> needs_review (202).
    """
    mock_mod_response = {
        'decision': 'needs_review',
        'detected_content': 'Blurry item',
        'matches_declared_name': False,
        'matches_declared_category': False,
        'is_prohibited_or_unrelated': False,
        'reason': 'Image is too blurry to identify clearly. Queued for manual admin review.',
        'raw_model_output': '{"simulated": true}'
    }

    with patch('backend.app.routes.products.moderate_product_image', return_value=mock_mod_response):
        res = client.post('/api/v1/products/create', data={
            'name': 'Unknown Berry',
            'category': 'Fruits',
            'price': '80.0',
            'quantity': '5',
            'location': 'Farm',
            'image': 'https://example.com/blurry.jpg'
        })

        assert res.status_code == 202
        json_data = res.get_json()
        assert json_data['moderation_status'] == 'needs_review'
        assert json_data['product']['moderation_status'] == 'needs_review'


def test_feature_a_gemini_api_exception_returns_503(client, app):
    """
    Case 5: Gemini API raises exception / timeout -> returns 503, no Product row created.
    """
    mock_mod_response = {
        'decision': 'unavailable',
        'detected_content': 'AI Service Error',
        'matches_declared_name': False,
        'matches_declared_category': False,
        'is_prohibited_or_unrelated': False,
        'reason': "We couldn't verify your image right now. Please try again.",
        'raw_model_output': 'Error'
    }

    with app.app_context():
        initial_count = Product.query.count()

    with patch('backend.app.routes.products.moderate_product_image', return_value=mock_mod_response):
        res = client.post('/api/v1/products/create', data={
            'name': 'Golden Honey',
            'category': 'Honey',
            'price': '250.0',
            'quantity': '10',
            'location': 'Apiary',
            'image': 'https://example.com/honey.jpg'
        })

        assert res.status_code == 503
        json_data = res.get_json()
        assert json_data['error'] == 'moderation_unavailable'

    with app.app_context():
        assert Product.query.count() == initial_count


# ==============================================================================
# FEATURE B TEST CASES (Farmer Product Deletion & Hard/Soft Delete Behavior)
# ==============================================================================

def test_feature_b_farmer_a_cannot_delete_farmer_b_product(client, app):
    """Farmer A cannot delete Farmer B's product (HTTP 403)."""
    with app.app_context():
        farmer_a = User(username='farmer_a_del', password='hash', user_type='farmer')
        farmer_b = User(username='farmer_b_del', password='hash', user_type='farmer')
        db.session.add_all([farmer_a, farmer_b])
        db.session.commit()

        prod_b = Product(user_id=farmer_b.id, name='Farmer B Apples', price=40.0, quantity=10, moderation_status='approved')
        db.session.add(prod_b)
        db.session.commit()

        farmer_a_id = farmer_a.id
        prod_b_id = prod_b.id
        token_a = create_access_token(identity=str(farmer_a_id))

    headers = {'Authorization': f'Bearer {token_a}'}
    res = client.delete(f'/api/v1/products/{prod_b_id}', headers=headers)
    assert res.status_code == 403
    json_data = res.get_json()
    assert 'permission denied' in json_data['error'].lower()


def test_feature_b_farmer_delete_product_zero_orders_hard_deleted(client, app):
    """Farmer deletes own product with 0 orders -> Hard deleted, removed from DB."""
    with app.app_context():
        farmer = User(username='farmer_hard_del', password='hash', user_type='farmer')
        db.session.add(farmer)
        db.session.commit()

        prod = Product(user_id=farmer.id, name='Unsold Tomatoes', price=20.0, quantity=50, moderation_status='approved')
        db.session.add(prod)
        db.session.commit()

        farmer_id = farmer.id
        prod_id = prod.id
        token = create_access_token(identity=str(farmer_id))

    headers = {'Authorization': f'Bearer {token}'}
    res = client.delete(f'/api/v1/products/{prod_id}', headers=headers)
    assert res.status_code == 200
    json_data = res.get_json()
    assert json_data['deletion_type'] == 'hard'

    with app.app_context():
        assert Product.query.get(prod_id) is None


def test_feature_b_farmer_delete_product_with_orders_soft_deleted(client, app):
    """Farmer deletes product WITH orders -> Soft deleted (is_deleted=True), hidden from marketplace."""
    with app.app_context():
        farmer = User(username='farmer_soft_del', password='hash', user_type='farmer')
        consumer = User(username='consumer_soft_del', password='hash', user_type='consumer')
        db.session.add_all([farmer, consumer])
        db.session.commit()

        prod = Product(user_id=farmer.id, name='Sold Out Carrots', price=30.0, quantity=5, moderation_status='approved')
        db.session.add(prod)
        db.session.commit()

        order = Order(user_id=consumer.id, product_id=prod.id, amount=30.0, phone_number='254700000000', order_status='Confirmed')
        db.session.add(order)
        db.session.commit()

        farmer_id = farmer.id
        prod_id = prod.id
        token = create_access_token(identity=str(farmer_id))

    headers = {'Authorization': f'Bearer {token}'}
    res = client.delete(f'/api/v1/products/{prod_id}', headers=headers)
    assert res.status_code == 200
    json_data = res.get_json()
    assert json_data['deletion_type'] == 'soft'

    with app.app_context():
        deleted_prod = Product.query.get(prod_id)
        assert deleted_prod is not None
        assert deleted_prod.is_deleted is True

    # Verify hidden from public marketplace endpoint
    res_mkt = client.get('/api/v1/products')
    assert res_mkt.status_code == 200
    mkt_items = res_mkt.get_json()['data']
    assert not any(p['id'] == prod_id for p in mkt_items)


def test_feature_b_admin_can_delete_any_product(client, app):
    """Admin can delete any product listing regardless of owner."""
    with app.app_context():
        admin = User(username='admin_del', password='hash', user_type='admin')
        farmer = User(username='farmer_admin_del', password='hash', user_type='farmer')
        db.session.add_all([admin, farmer])
        db.session.commit()

        prod = Product(user_id=farmer.id, name='Admin Cleanup Item', price=15.0, quantity=10, moderation_status='approved')
        db.session.add(prod)
        db.session.commit()

        admin_id = admin.id
        prod_id = prod.id
        admin_token = create_access_token(identity=str(admin_id))

    headers = {'Authorization': f'Bearer {admin_token}'}
    res = client.delete(f'/api/v1/products/{prod_id}', headers=headers)
    assert res.status_code == 200


def test_integration_orange_with_apple_photo_blocked_at_upload_time(client, app):
    """
    Integration Test reproducing original bug scenario:
    Farmer submits 'orange' produce name with an apple photo.
    Confirms HTTP 422 returned and zero Product row created.
    """
    mock_mod_response = {
        'decision': 'rejected',
        'detected_content': 'apple',
        'matches_declared_name': False,
        'matches_declared_category': True,
        'is_prohibited_or_unrelated': False,
        'reason': "The photo doesn't look like 'orange' — it looks like apple. Please upload a matching photo or correct the product name.",
        'raw_model_output': '{"simulated": true}'
    }

    with app.app_context():
        count_before = Product.query.count()

    with patch('backend.app.routes.products.moderate_product_image', return_value=mock_mod_response):
        res = client.post('/api/v1/products/create', data={
            'name': 'orange',
            'category': 'Fruits',
            'price': '45.0',
            'quantity': '15',
            'location': 'Farm Orchard',
            'image': 'https://example.com/apple_photo.png'
        })

        assert res.status_code == 422
        json_data = res.get_json()
        assert json_data['error'] == 'moderation_failed'
        assert json_data['matches_declared_name'] is False

    with app.app_context():
        count_after = Product.query.count()
        assert count_after == count_before
