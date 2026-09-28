"""
Automated Pytest Suite for EcoGreen Order Processing & Lifecycle.
"""

import pytest
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.app import create_app
from backend.app.extensions import db
from backend.app.models import User, Product, Order

@pytest.fixture
def app_instance():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        farmer = User(username='farmer_joe', email='joe@farm.com', user_type='farmer', phone_number='9876543213')
        consumer = User(username='consumer_mark', email='mark@gmail.com', user_type='consumer', phone_number='9876543214')
        db.session.add_all([farmer, consumer])
        db.session.commit()

        product = Product(user_id=farmer.id, name='Organic Honey', price=250.0, quantity=20, category='Dairy & Eggs')
        db.session.add(product)
        db.session.commit()

        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app_instance):
    return app_instance.test_client()


def test_order_creation_and_status_update(client, app_instance):
    with app_instance.app_context():
        consumer = User.query.filter_by(username='consumer_mark').first()
        product = Product.query.filter_by(name='Organic Honey').first()
        consumer_id = consumer.id
        product_id = product.id

    res = client.post('/api/v1/Orders/create', json={
        'product_id': product_id,
        'user_id': consumer_id,
        'amount': 250.0,
        'phone_number': '9876543214'
    })
    assert res.status_code == 201
    order_data = res.get_json()
    order_id = order_data['order_id']
    assert order_data['order']['status'] == 'Pending'

    conf_res = client.put(f'/api/v1/Orders/{order_id}/status', json={'status': 'Confirmed'})
    assert conf_res.status_code == 200
    assert conf_res.get_json()['order']['status'] == 'Confirmed'

    deliv_res = client.put(f'/api/v1/Orders/{order_id}/deliver')
    assert deliv_res.status_code == 200
    assert deliv_res.get_json()['order']['status'] == 'Delivered'
