"""
EcoGreen Analytics Service Layer.
Contains complex aggregation queries for financial metrics, user growth,
order fulfillment funnels, farmer performance, and supply vs demand.
"""

import time
import math
import base64
from functools import wraps
from datetime import datetime, timedelta
from flask import request, jsonify, current_app
from sqlalchemy import func, case, and_, or_, distinct
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from werkzeug.security import check_password_hash

from backend.app.models.user import User
from backend.app.models.product import Product
from backend.app.models.order import Order
from backend.app.models.transaction import Transaction
from backend.app.extensions import db

# In-memory cache
_analytics_cache = {}
CACHE_TTL = 5  # 5 seconds for real-time updates

def get_cached(key):
    if key in _analytics_cache:
        data, timestamp = _analytics_cache[key]
        if time.time() - timestamp < CACHE_TTL:
            return data
    return None

def set_cached(key, data):
    _analytics_cache[key] = (data, time.time())

def mask_phone(phone):
    if not phone:
        return ""
    p = str(phone).strip()
    if len(p) <= 4:
        return "****"
    return p[:2] + "****" + p[-4:]

def admin_required(f):
    """Admin authorization decorator supporting Basic Auth and JWT Bearer token."""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')

        # 1. Support Basic Auth for Power BI Desktop Web connector
        if auth_header and auth_header.startswith('Basic '):
            try:
                encoded_credentials = auth_header.split(' ')[1]
                decoded = base64.b64decode(encoded_credentials).decode('utf-8')
                if ':' in decoded:
                    username_or_email, password = decoded.split(':', 1)
                    cfg_user = current_app.config.get('POWERBI_USER', 'admin')
                    cfg_pass = current_app.config.get('POWERBI_PASSWORD', 'admin123')
                    
                    if username_or_email == cfg_user and password == cfg_pass:
                        return f(*args, **kwargs)
                        
                    user = User.query.filter(
                        (User.username == username_or_email) | (User.email == username_or_email)
                    ).first()

                    if user and user.password and check_password_hash(user.password, password) and user.user_type == 'admin':
                        return f(*args, **kwargs)
                    else:
                        return jsonify({'error': 'Forbidden: Admin access required or invalid credentials', 'status': 'error'}), 403
            except Exception as e:
                return jsonify({'error': f'Invalid Basic Auth format: {str(e)}', 'status': 'error'}), 401

        # 2. Support JWT Bearer token
        try:
            verify_jwt_in_request(optional=True)
            current_user_id = get_jwt_identity()
            if current_user_id:
                user = User.query.get(int(current_user_id))
                if user and user.user_type == 'admin':
                    return f(*args, **kwargs)
                return jsonify({'error': 'Forbidden: Admin access required', 'status': 'error'}), 403
        except Exception:
            pass

        return jsonify({'error': 'Authentication required. Provide Basic Auth (Admin) or JWT Admin token.', 'status': 'error'}), 401

    return decorated

def get_date_filters():
    from_date_str = request.args.get('from')
    to_date_str = request.args.get('to')
    range_str = request.args.get('range', '').lower()

    now = datetime.utcnow()
    start_date = None
    end_date = None

    if from_date_str and to_date_str:
        try:
            start_date = datetime.strptime(from_date_str, '%Y-%m-%d')
            end_date = datetime.strptime(to_date_str, '%Y-%m-%d') + timedelta(days=1) - timedelta(seconds=1)
        except Exception:
            pass
    elif range_str:
        if range_str == '7d':
            start_date = now - timedelta(days=7)
        elif range_str == '30d':
            start_date = now - timedelta(days=30)
        elif range_str == '90d':
            start_date = now - timedelta(days=90)
        elif range_str == '1y':
            start_date = now - timedelta(days=365)
        end_date = now

    return start_date, end_date
