"""
Automated Pytest Suite for EcoGreen Product Management & Search.
"""

import pytest
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.app import create_app
from backend.app.extensions import db
from backend.app.models import User, Product

@pytest.fixture
def app_instance():
    app = create_app('testing')
    app.config['MODERATION_MODE'] = 'simulate'
    with app.app_context():
        db.create_all()
        farmer = User(
            username='farmer_bob',
            email='bob@farm.com',
            user_type='farmer',
            phone_number='9876543212'
        )
        db.session.add(farmer)
        db.session.commit()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app_instance):
    return app_instance.test_client()


def test_create_and_get_products(client, app_instance):
    with app_instance.app_context():
        farmer = User.query.filter_by(username='farmer_bob').first()
        farmer_id = farmer.id

    res = client.post('/api/v1/products/create', json={
        'user_id': farmer_id,
        'name': 'Organic Tomatoes',
        'price': 40.0,
        'description': 'Fresh red tomatoes',
        'location': 'Nashik',
        'quantity': 100,
        'category': 'Vegetables'
    })
    assert res.status_code == 201
    res_data = res.get_json()
    assert res_data['status'] == 'success'
    assert res_data['product']['name'] == 'Organic Tomatoes'

    get_res = client.get('/api/v1/products')
    assert get_res.status_code == 200
    prods_payload = get_res.get_json()
    assert prods_payload['status'] == 'success'
    assert len(prods_payload['data']) == 1
    assert prods_payload['data'][0]['name'] == 'Organic Tomatoes'


def test_search_products(client, app_instance):
    with app_instance.app_context():
        farmer = User.query.filter_by(username='farmer_bob').first()
        p1 = Product(user_id=farmer.id, name='Shimla Apples', price=120.0, quantity=50, category='Fruits', moderation_status='approved')
        p2 = Product(user_id=farmer.id, name='Fresh Carrots', price=30.0, quantity=30, category='Vegetables', moderation_status='approved')
        db.session.add_all([p1, p2])
        db.session.commit()
        farmer_id = farmer.id

    search_res = client.post('/api/v1/Search', json={'user_id': farmer_id, 'keyword': 'Apples'})
    assert search_res.status_code == 200
    payload = search_res.get_json()
    assert payload['status'] == 'success'
    assert len(payload['data']) == 1
    assert payload['data'][0]['name'] == 'Shimla Apples'
