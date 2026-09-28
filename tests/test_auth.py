"""
Automated Pytest Suite for EcoGreen Authentication & User Management.
"""

import pytest
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.app import create_app
from backend.app.extensions import db

@pytest.fixture
def app_instance():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app_instance):
    return app_instance.test_client()


def test_user_registration(client):
    response = client.post('/api/v1/User/create', json={
        'username': 'farmer_john',
        'email': 'john@farm.com',
        'password': 'password123',
        'user_type': 'farmer',
        'phone_number': '9876543210'
    })
    assert response.status_code == 201
    data = response.get_json()
    assert data['user']['username'] == 'farmer_john'
    assert data['user']['user_type'] == 'farmer'


def test_user_login(client):
    client.post('/api/v1/User/create', json={
        'username': 'consumer_alice',
        'email': 'alice@gmail.com',
        'password': 'secretpassword',
        'user_type': 'consumer',
        'phone_number': '9876543211'
    })

    login_res = client.post('/api/v1/Login', json={
        'username': 'consumer_alice',
        'password': 'secretpassword'
    })
    assert login_res.status_code == 200
    token_data = login_res.get_json()
    assert 'access-token' in token_data
    assert token_data['user']['username'] == 'consumer_alice'


def test_invalid_login(client):
    res = client.post('/api/v1/Login', json={
        'username': 'non_existent',
        'password': 'wrongpassword'
    })
    assert res.status_code == 401
