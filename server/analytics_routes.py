import base64
import time
from functools import wraps
from flask import Blueprint, request, jsonify
from sqlalchemy import func, case
from datetime import datetime
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from werkzeug.security import check_password_hash

from server.models import db, User, Product, Order, Transaction

analytics_bp = Blueprint('analytics_bp', __name__, url_prefix='/api/v1/admin/analytics')

# Simple 5-minute (300 seconds) in-memory cache for Power BI polling efficiency
_analytics_cache = {}
CACHE_TTL = 300  # seconds

def get_cached(key):
    if key in _analytics_cache:
        data, timestamp = _analytics_cache[key]
        if time.time() - timestamp < CACHE_TTL:
            return data
    return None

def set_cached(key, data):
    _analytics_cache[key] = (data, time.time())

def admin_required(f):
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

        # If neither auth passed
        response = jsonify({'error': 'Authentication required. Provide Basic Auth (Admin) or JWT Admin token.', 'status': 'error'})
        response.headers['WWW-Authenticate'] = 'Basic realm="EcoGreen Admin Analytics"'
        return response, 401

    return decorated


# -------------------------------------------------------------------------
# a) GET /api/v1/admin/analytics/summary
# -------------------------------------------------------------------------
@analytics_bp.route('/summary', methods=['GET'])
@admin_required
def get_summary():
    cache_key = 'summary'
    cached = get_cached(cache_key)
    if cached is not None:
        return jsonify(cached), 200

    total_orders = db.session.query(func.count(Order.id)).scalar() or 0
    total_farmers = db.session.query(func.count(User.id)).filter(User.user_type == 'farmer').scalar() or 0
    total_consumers = db.session.query(func.count(User.id)).filter(User.user_type == 'consumer').scalar() or 0
    total_products_listed = db.session.query(func.count(Product.id)).scalar() or 0

    total_transactions_success = db.session.query(func.count(Transaction.id)).filter(Transaction.status == 'Success').scalar() or 0
    total_transactions_failed = db.session.query(func.count(Transaction.id)).filter(Transaction.status == 'Failed').scalar() or 0
    total_revenue = float(db.session.query(func.coalesce(func.sum(Transaction.amount), 0.0)).filter(Transaction.status == 'Success').scalar() or 0.0)

    pending_orders = db.session.query(func.count(Order.id)).filter(Order.order_status == 'Pending').scalar() or 0
    confirmed_orders = db.session.query(func.count(Order.id)).filter(Order.order_status == 'Confirmed').scalar() or 0
    paid_orders = db.session.query(func.count(Order.id)).filter(Order.payment_status == 'Paid').scalar() or 0
    unpaid_orders = db.session.query(func.count(Order.id)).filter(Order.payment_status == 'Unpaid').scalar() or 0

    data = {
        "total_orders": total_orders,
        "total_farmers": total_farmers,
        "total_consumers": total_consumers,
        "total_products_listed": total_products_listed,
        "total_transactions_success": total_transactions_success,
        "total_transactions_failed": total_transactions_failed,
        "total_revenue": round(total_revenue, 2),
        "pending_orders": pending_orders,
        "confirmed_orders": confirmed_orders,
        "paid_orders": paid_orders,
        "unpaid_orders": unpaid_orders
    }

    set_cached(cache_key, data)
    return jsonify(data), 200


# -------------------------------------------------------------------------
# b) GET /api/v1/admin/analytics/orders-over-time?interval=day|week|month
# -------------------------------------------------------------------------
@analytics_bp.route('/orders-over-time', methods=['GET'])
@admin_required
def get_orders_over_time():
    interval = request.args.get('interval', 'day').lower()
    cache_key = f'orders_over_time_{interval}'
    cached = get_cached(cache_key)
    if cached is not None:
        return jsonify(cached), 200

    if interval == 'week':
        date_fmt = '%Y-%W'
    elif interval == 'month':
        date_fmt = '%Y-%m'
    else:
        date_fmt = '%Y-%m-%d'

    results = db.session.query(
        func.strftime(date_fmt, Order.transaction_date).label('period'),
        func.count(Order.id).label('order_count'),
        func.coalesce(func.sum(Order.amount), 0.0).label('revenue')
    ).group_by('period').order_by('period').all()

    data = [
        {
            "period": r.period or datetime.utcnow().strftime(date_fmt),
            "order_count": int(r.order_count),
            "revenue": round(float(r.revenue), 2)
        }
        for r in results
    ]

    set_cached(cache_key, data)
    return jsonify(data), 200


# -------------------------------------------------------------------------
# c) GET /api/v1/admin/analytics/top-farmers?limit=10
# -------------------------------------------------------------------------
@analytics_bp.route('/top-farmers', methods=['GET'])
@admin_required
def get_top_farmers():
    limit = int(request.args.get('limit', 10))
    cache_key = f'top_farmers_{limit}'
    cached = get_cached(cache_key)
    if cached is not None:
        return jsonify(cached), 200

    results = db.session.query(
        User.id.label('farmer_id'),
        User.username.label('farmer_name'),
        func.count(Order.id).label('total_orders'),
        func.coalesce(func.sum(Order.amount), 0.0).label('total_revenue')
    ).join(Product, Product.user_id == User.id)\
     .join(Order, Order.product_id == Product.id)\
     .filter(User.user_type == 'farmer')\
     .group_by(User.id, User.username)\
     .order_by(func.sum(Order.amount).desc())\
     .limit(limit).all()

    data = [
        {
            "farmer_id": r.farmer_id,
            "farmer_name": r.farmer_name,
            "total_orders": int(r.total_orders),
            "total_revenue": round(float(r.total_revenue), 2)
        }
        for r in results
    ]

    set_cached(cache_key, data)
    return jsonify(data), 200


# -------------------------------------------------------------------------
# d) GET /api/v1/admin/analytics/top-products?limit=10
# -------------------------------------------------------------------------
@analytics_bp.route('/top-products', methods=['GET'])
@admin_required
def get_top_products():
    limit = int(request.args.get('limit', 10))
    cache_key = f'top_products_{limit}'
    cached = get_cached(cache_key)
    if cached is not None:
        return jsonify(cached), 200

    results = db.session.query(
        Product.id.label('product_id'),
        Product.name.label('product_name'),
        func.coalesce(Product.category, 'Vegetables').label('category'),
        func.count(Order.id).label('units_sold'),
        func.coalesce(func.sum(Order.amount), 0.0).label('revenue')
    ).join(Order, Order.product_id == Product.id)\
     .group_by(Product.id, Product.name, Product.category)\
     .order_by(func.sum(Order.amount).desc())\
     .limit(limit).all()

    data = [
        {
            "product_id": r.product_id,
            "product_name": r.product_name,
            "category": r.category or 'Vegetables',
            "units_sold": int(r.units_sold),
            "revenue": round(float(r.revenue), 2)
        }
        for r in results
    ]

    set_cached(cache_key, data)
    return jsonify(data), 200


# -------------------------------------------------------------------------
# e) GET /api/v1/admin/analytics/category-breakdown
# -------------------------------------------------------------------------
@analytics_bp.route('/category-breakdown', methods=['GET'])
@admin_required
def get_category_breakdown():
    cache_key = 'category_breakdown'
    cached = get_cached(cache_key)
    if cached is not None:
        return jsonify(cached), 200

    results = db.session.query(
        func.coalesce(Product.category, 'Vegetables').label('category'),
        func.count(Order.id).label('order_count'),
        func.coalesce(func.sum(Order.amount), 0.0).label('revenue')
    ).join(Order, Order.product_id == Product.id)\
     .group_by(Product.category)\
     .order_by(func.sum(Order.amount).desc()).all()

    data = [
        {
            "category": r.category or 'Vegetables',
            "order_count": int(r.order_count),
            "revenue": round(float(r.revenue), 2)
        }
        for r in results
    ]

    set_cached(cache_key, data)
    return jsonify(data), 200


# -------------------------------------------------------------------------
# f) GET /api/v1/admin/analytics/user-growth?interval=day|week|month
# -------------------------------------------------------------------------
@analytics_bp.route('/user-growth', methods=['GET'])
@admin_required
def get_user_growth():
    interval = request.args.get('interval', 'day').lower()
    cache_key = f'user_growth_{interval}'
    cached = get_cached(cache_key)
    if cached is not None:
        return jsonify(cached), 200

    if interval == 'week':
        date_fmt = '%Y-%W'
    elif interval == 'month':
        date_fmt = '%Y-%m'
    else:
        date_fmt = '%Y-%m-%d'

    results = db.session.query(
        func.strftime(date_fmt, User.created_at).label('period'),
        func.sum(case((User.user_type == 'farmer', 1), else_=0)).label('new_farmers'),
        func.sum(case((User.user_type == 'consumer', 1), else_=0)).label('new_consumers')
    ).filter(User.created_at.isnot(None))\
     .group_by('period').order_by('period').all()

    data = [
        {
            "period": r.period or datetime.utcnow().strftime(date_fmt),
            "new_farmers": int(r.new_farmers or 0),
            "new_consumers": int(r.new_consumers or 0)
        }
        for r in results
    ]

    set_cached(cache_key, data)
    return jsonify(data), 200
