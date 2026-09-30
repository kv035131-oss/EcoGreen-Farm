import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from backend.app import create_app
from backend.app.extensions import db
from backend.app.models.product import Product
from backend.app.models.order import Order
from backend.app.models.moderation_log import ProductModerationLog
from backend.app.models.user import User

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


def test_reverse_geocoding_endpoint(client):
    """Tests POST /api/v1/geocode/reverse with valid and invalid inputs."""
    # Test invalid coordinates
    res = client.post('/api/v1/geocode/reverse', json={})
    assert res.status_code == 200
    json_data = res.get_json()
    assert json_data['success'] is False

    # Test valid coordinates (Mysuru, KA)
    res_valid = client.post('/api/v1/geocode/reverse', json={
        'latitude': 12.2958,
        'longitude': 76.6394
    })
    assert res_valid.status_code == 200
    geo_json = res_valid.get_json()
    assert 'success' in geo_json
    if geo_json['success']:
        assert 'address_text' in geo_json
        assert 'district' in geo_json
        assert 'state' in geo_json

    # Test 24-hour cache on identical 3-decimal lat/lng
    res_cached = client.post('/api/v1/geocode/reverse', json={
        'latitude': 12.29581,
        'longitude': 76.63942
    })
    assert res_cached.status_code == 200
    cached_json = res_cached.get_json()
    if cached_json['success']:
        assert cached_json.get('cached') is True


def test_blocking_moderation_rejection_no_product_created(client, app):
    """
    FEATURE B CORE RULE:
    If moderation rejects a product (e.g. prohibited non-farm item),
    server returns HTTP 422 Unprocessable Entity and NO Product row is created in DB.
    """
    with app.app_context():
        initial_product_count = Product.query.count()

    # Attempt to create non-farm prohibited product
    res = client.post('/api/v1/products/create', data={
        'name': 'Prohibited Laptop Computer',
        'price': '499.00',
        'quantity': '1',
        'category': 'Others',
        'description': 'Brand new laptop computer',
        'location': 'Tech Hub',
        'image': 'https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=500'
    })

    assert res.status_code == 422
    json_data = res.get_json()
    assert json_data['status'] == 'rejected'
    assert json_data['moderation_status'] == 'rejected'
    assert 'prohibited' in json_data['reason'].lower() or 'laptop' in json_data['reason'].lower()

    # Verify NO Product row was created in the database!
    with app.app_context():
        final_product_count = Product.query.count()
        assert final_product_count == initial_product_count

        # Verify ProductModerationLog entry was recorded
        log = ProductModerationLog.query.order_by(ProductModerationLog.id.desc()).first()
        assert log is not None
        assert log.product_id is None
        assert log.decision == 'rejected'


def test_blocking_moderation_mismatch_rejection(client, app):
    """Tests name-to-image mismatch rejection returns HTTP 422 and blocks DB row creation."""
    with app.app_context():
        initial_count = Product.query.count()

    # Produce name says Tomatoes, but photo filename says carrots.jpg
    res = client.post('/api/v1/products/create', data={
        'name': 'Fresh Organic Tomatoes',
        'price': '25.00',
        'quantity': '50',
        'category': 'Vegetables',
        'description': 'Fresh tomatoes from farm',
        'location': 'Green Valley Farm',
        'image': 'https://images.unsplash.com/photo-1598170845058-32b9d6a5da37?w=500&carrots.jpg'
    })

    assert res.status_code == 422
    json_data = res.get_json()
    assert json_data['status'] == 'rejected'
    reason_lower = json_data['reason'].lower()
    assert (
        "does not match" in reason_lower
        or "mismatch" in reason_lower
        or "doesn't look like" in reason_lower
        or "doesn\u2019t look like" in reason_lower
    ), f"Unexpected reason: {json_data['reason']!r}"

    # Verify DB product count remained unchanged
    with app.app_context():
        assert Product.query.count() == initial_count


def test_synchronous_moderation_approval(client, app):
    """Tests approved produce creation returns HTTP 201 Created and saves Product row."""
    res = client.post('/api/v1/products/create', data={
        'name': 'Fresh Organic Tomatoes',
        'price': '30.00',
        'quantity': '100',
        'category': 'Vegetables',
        'description': 'Crisp red organic tomatoes',
        'address_text': 'MG Road, Mysuru, Karnataka, 570001',
        'latitude': '12.2958',
        'longitude': '76.6394',
        'district': 'Mysuru',
        'state': 'Karnataka',
        'image': 'https://images.unsplash.com/photo-1592924357228-91a4daadcfea?w=500&tomatoes.jpg'
    })

    assert res.status_code == 201
    json_data = res.get_json()
    assert json_data['status'] == 'success'
    assert json_data['moderation_status'] == 'approved'
    assert 'product' in json_data

    prod_dict = json_data['product']
    assert prod_dict['name'] == 'Fresh Organic Tomatoes'
    assert prod_dict['latitude'] == 12.2958
    assert prod_dict['longitude'] == 76.6394
    assert prod_dict['district'] == 'Mysuru'
    assert prod_dict['state'] == 'Karnataka'


def test_synchronous_moderation_needs_review(client, app):
    """Tests ambiguous produce creation returns HTTP 202 Accepted and saves pending admin review product."""
    res = client.post('/api/v1/products/create', data={
        'name': 'Test Ambiguous Item (test_review)',
        'price': '15.00',
        'quantity': '10',
        'category': 'Others',
        'description': 'Ambiguous quality photo',
        'location': 'Unknown Farm',
        'image': 'https://images.unsplash.com/photo-1542838132-92c53300491e?w=500'
    })

    assert res.status_code == 202
    json_data = res.get_json()
    assert json_data['status'] == 'needs_review'
    assert json_data['moderation_status'] == 'needs_review'


def test_order_location_capture_and_privacy(client, app):
    """
    Tests Feature A Order Location Capture and Privacy Rule (Step A5):
    Consumer delivery lat/lng is visible ONLY to assigned farmer, order consumer, or admin.
    """
    with app.app_context():
        # Setup farmer, consumer, third-party consumer, and product
        farmer = User(username='test_farmer_geo', password='hash', user_type='farmer')
        consumer = User(username='test_consumer_geo', password='hash', user_type='consumer')
        other_user = User(username='test_other_geo', password='hash', user_type='consumer')
        db.session.add_all([farmer, consumer, other_user])
        db.session.commit()

        product = Product(
            user_id=farmer.id,
            name='Geo Apples',
            price=50.0,
            quantity=100,
            category='Fruits',
            moderation_status='approved'
        )
        db.session.add(product)
        db.session.commit()

        farmer_id = farmer.id
        consumer_id = consumer.id
        other_id = other_user.id
        product_id = product.id

    # Place Order with captured location coordinates
    res = client.post('/api/v1/Orders/create', json={
        'product_id': product_id,
        'user_id': consumer_id,
        'amount': 50.0,
        'phone_number': '254700112233',
        'delivery_address_text': 'Church Street, Bengaluru, Karnataka, 560001',
        'delivery_latitude': 12.9716,
        'delivery_longitude': 77.5946,
        'delivery_district': 'Bengaluru',
        'delivery_state': 'Karnataka'
    })

    assert res.status_code == 201
    order_json = res.get_json()
    assert order_json['status'] == 'success'
    order_id = order_json['order_id']

    # Privacy Check 1: Consumer who placed the order CAN see lat/lng
    from backend.app.services.order_service import serialize_order
    with app.app_context():
        order = Order.query.get(order_id)
        
        consumer_view = serialize_order(order, requesting_user_id=consumer_id)
        assert consumer_view['delivery_latitude'] == 12.9716
        assert consumer_view['delivery_longitude'] == 77.5946

        # Privacy Check 2: Assigned Farmer CAN see lat/lng
        farmer_view = serialize_order(order, requesting_user_id=farmer_id)
        assert farmer_view['delivery_latitude'] == 12.9716
        assert farmer_view['delivery_longitude'] == 77.5946

        # Privacy Check 3: Admin CAN see lat/lng
        admin_view = serialize_order(order, requesting_user_role='admin')
        assert admin_view['delivery_latitude'] == 12.9716
        assert admin_view['delivery_longitude'] == 77.5946

        # Privacy Check 4: Third-party consumer CANNOT see lat/lng (sanitized to None)
        other_view = serialize_order(order, requesting_user_id=other_id)
        assert other_view['delivery_address_text'] == 'Church Street, Bengaluru, Karnataka, 560001'
        assert other_view['delivery_latitude'] is None
        assert other_view['delivery_longitude'] is None
