"""
Admin Analytics Blueprint.
Provides financial, operational, farmer, consumer, inventory, and location analytics,
plus Power BI streaming endpoints.
"""

import math
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from sqlalchemy import func, case, and_, or_, distinct

from backend.app.extensions import db
from backend.app.models.user import User
from backend.app.models.product import Product
from backend.app.models.order import Order
from backend.app.models.transaction import Transaction
from backend.app.services.analytics_service import (
    admin_required, get_cached, set_cached, get_date_filters, mask_phone
)

analytics_bp = Blueprint('analytics_bp', __name__, url_prefix='/api/v1/admin/analytics')

@analytics_bp.route('/summary', methods=['GET'])
@admin_required
def get_summary():
    start_date, end_date = get_date_filters()
    cache_key = f"summary_{start_date}_{end_date}"
    cached = get_cached(cache_key)
    if cached:
        return jsonify(cached), 200

    order_query = Order.query
    txn_query = Transaction.query.filter_by(status='Success')

    if start_date and end_date:
        order_query = order_query.filter(Order.transaction_date >= start_date, Order.transaction_date <= end_date)
        txn_query = txn_query.filter(Transaction.transaction_date >= start_date, Transaction.transaction_date <= end_date)

    total_revenue = db.session.query(func.sum(Transaction.amount)).filter(
        Transaction.status == 'Success',
        *( [Transaction.transaction_date >= start_date, Transaction.transaction_date <= end_date] if start_date else [] )
    ).scalar() or 0.0

    total_orders = order_query.count()
    completed_orders = order_query.filter(Order.order_status.in_(['Confirmed', 'Delivered'])).count()
    active_farmers = User.query.filter_by(user_type='farmer', status='Active').count()
    active_consumers = User.query.filter_by(user_type='consumer', status='Active').count()

    response = {
        'status': 'success',
        'summary': {
            'total_revenue': round(total_revenue, 2),
            'total_orders': total_orders,
            'completed_orders': completed_orders,
            'active_farmers': active_farmers,
            'active_consumers': active_consumers,
            'fulfillment_rate': round((completed_orders / total_orders * 100), 1) if total_orders > 0 else 0.0
        }
    }
    set_cached(cache_key, response)
    return jsonify(response), 200


@analytics_bp.route('/orders-over-time', methods=['GET'])
@admin_required
def get_orders_over_time():
    interval = request.args.get('interval', 'day').lower()
    start_date, end_date = get_date_filters()

    query = db.session.query(
        func.date(Order.transaction_date).label('date'),
        func.count(Order.id).label('total_orders'),
        func.sum(Order.amount).label('revenue')
    )
    if start_date and end_date:
        query = query.filter(Order.transaction_date >= start_date, Order.transaction_date <= end_date)

    results = query.group_by(func.date(Order.transaction_date)).order_by('date').all()
    
    data = [{
        'date': r.date or 'Unknown',
        'orders': r.total_orders,
        'revenue': round(r.revenue or 0.0, 2)
    } for r in results]

    return jsonify({'status': 'success', 'data': data}), 200


@analytics_bp.route('/order-status-breakdown', methods=['GET'])
@admin_required
def get_order_status_breakdown():
    results = db.session.query(
        Order.order_status,
        func.count(Order.id).label('count')
    ).group_by(Order.order_status).all()

    data = [{
        'status': r.order_status or 'Pending',
        'count': r.count
    } for r in results]

    return jsonify({'status': 'success', 'data': data}), 200


@analytics_bp.route('/fulfillment-funnel', methods=['GET'])
@admin_required
def get_fulfillment_funnel():
    total = Order.query.count()
    confirmed = Order.query.filter(Order.order_status.in_(['Confirmed', 'Delivered'])).count()
    delivered = Order.query.filter_by(order_status='Delivered').count()
    cancelled = Order.query.filter_by(order_status='Cancelled').count()

    return jsonify({
        'status': 'success',
        'funnel': {
            'total_placed': total,
            'confirmed': confirmed,
            'delivered': delivered,
            'cancelled': cancelled
        }
    }), 200


@analytics_bp.route('/abandoned-orders', methods=['GET'])
@admin_required
def get_abandoned_orders():
    six_hours_ago = datetime.utcnow() - timedelta(hours=6)
    abandoned = Order.query.filter(
        Order.order_status == 'Pending',
        Order.transaction_date <= six_hours_ago
    ).order_by(Order.id.desc()).all()

    return jsonify({
        'status': 'success',
        'count': len(abandoned),
        'orders': [o.to_dict() for o in abandoned]
    }), 200


@analytics_bp.route('/farmer-performance', methods=['GET'])
@admin_required
def get_farmer_performance():
    farmers = User.query.filter_by(user_type='farmer').all()
    performance = []

    for f in farmers:
        farmer_products = Product.query.filter_by(user_id=f.id).all()
        prod_ids = [p.id for p in farmer_products]
        
        if not prod_ids:
            continue

        orders = Order.query.filter(Order.product_id.in_(prod_ids)).all()
        total_orders = len(orders)
        fulfilled = sum(1 for o in orders if o.order_status in ['Confirmed', 'Delivered'])
        revenue = sum(o.amount for o in orders if o.order_status in ['Confirmed', 'Delivered'])

        performance.append({
            'farmer_id': f.id,
            'username': f.username,
            'email': f.email,
            'phone': mask_phone(f.effective_phone),
            'total_orders': total_orders,
            'fulfilled_orders': fulfilled,
            'fulfillment_rate': round((fulfilled / total_orders * 100), 1) if total_orders > 0 else 0.0,
            'total_revenue': round(revenue, 2)
        })

    return jsonify({'status': 'success', 'farmers': performance}), 200


@analytics_bp.route('/farmer-response-time', methods=['GET'])
@admin_required
def get_farmer_response_time():
    orders = Order.query.filter(Order.confirmed_at.isnot(None)).all()
    response_times = []

    for o in orders:
        if o.transaction_date and o.confirmed_at:
            diff_minutes = (o.confirmed_at - o.transaction_date).total_seconds() / 60.0
            response_times.append(diff_minutes)

    avg_minutes = round(sum(response_times) / len(response_times), 1) if response_times else 0.0

    return jsonify({
        'status': 'success',
        'avg_response_time_minutes': avg_minutes,
        'total_analyzed_orders': len(response_times)
    }), 200


@analytics_bp.route('/inactive-farmers', methods=['GET'])
@admin_required
def get_inactive_farmers():
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    farmers = User.query.filter_by(user_type='farmer').all()
    inactive = []

    for f in farmers:
        last_active = f.last_active_at or f.created_at
        if last_active and last_active < thirty_days_ago:
            inactive.append(f.to_dict())

    return jsonify({'status': 'success', 'count': len(inactive), 'farmers': inactive}), 200


@analytics_bp.route('/top-farmers-by-revenue', methods=['GET'])
@admin_required
def get_top_farmers_by_revenue():
    farmers = User.query.filter_by(user_type='farmer').all()
    results = []

    for f in farmers:
        prod_ids = [p.id for p in Product.query.filter_by(user_id=f.id).all()]
        if not prod_ids:
            continue
        revenue = db.session.query(func.sum(Order.amount)).filter(
            Order.product_id.in_(prod_ids),
            Order.order_status.in_(['Confirmed', 'Delivered'])
        ).scalar() or 0.0

        results.append({
            'farmer_id': f.id,
            'username': f.username,
            'revenue': round(revenue, 2)
        })

    results.sort(key=lambda x: x['revenue'], reverse=True)
    return jsonify({'status': 'success', 'top_farmers': results[:10]}), 200


@analytics_bp.route('/top-consumers', methods=['GET'])
@admin_required
def get_top_consumers():
    consumers = User.query.filter_by(user_type='consumer').all()
    results = []

    for c in consumers:
        spend = db.session.query(func.sum(Order.amount)).filter_by(user_id=c.id).scalar() or 0.0
        count = Order.query.filter_by(user_id=c.id).count()

        results.append({
            'consumer_id': c.id,
            'username': c.username,
            'email': c.email,
            'orders_count': count,
            'total_spend': round(spend, 2)
        })

    results.sort(key=lambda x: x['total_spend'], reverse=True)
    return jsonify({'status': 'success', 'top_consumers': results[:10]}), 200


@analytics_bp.route('/new-vs-returning', methods=['GET'])
@admin_required
def get_new_vs_returning():
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    new_users = User.query.filter(User.created_at >= thirty_days_ago).count()
    returning_users = User.query.filter(User.created_at < thirty_days_ago).count()

    return jsonify({
        'status': 'success',
        'new_users': new_users,
        'returning_users': returning_users
    }), 200


@analytics_bp.route('/repeat-purchase', methods=['GET'])
@admin_required
def get_repeat_purchase():
    consumer_orders = db.session.query(
        Order.user_id,
        func.count(Order.id).label('cnt')
    ).group_by(Order.user_id).all()

    single_buyers = sum(1 for c in consumer_orders if c.cnt == 1)
    repeat_buyers = sum(1 for c in consumer_orders if c.cnt > 1)
    total_buyers = len(consumer_orders)

    return jsonify({
        'status': 'success',
        'total_buyers': total_buyers,
        'single_purchase_buyers': single_buyers,
        'repeat_purchase_buyers': repeat_buyers,
        'repeat_rate': round((repeat_buyers / total_buyers * 100), 1) if total_buyers > 0 else 0.0
    }), 200


@analytics_bp.route('/category-breakdown', methods=['GET'])
@admin_required
def get_category_breakdown():
    results = db.session.query(
        Product.category,
        func.count(Order.id).label('order_count'),
        func.sum(Order.amount).label('revenue')
    ).join(Order, Product.id == Order.product_id).group_by(Product.category).all()

    data = [{
        'category': r.category or 'Vegetables',
        'order_count': r.order_count,
        'revenue': round(r.revenue or 0.0, 2)
    } for r in results]

    return jsonify({'status': 'success', 'categories': data}), 200


@analytics_bp.route('/top-products', methods=['GET'])
@admin_required
def get_top_products():
    results = db.session.query(
        Product.name,
        func.count(Order.id).label('sales_count'),
        func.sum(Order.amount).label('total_revenue')
    ).join(Order, Product.id == Order.product_id).group_by(Product.id).order_by(func.count(Order.id).desc()).limit(10).all()

    data = [{
        'name': r.name,
        'sales_count': r.sales_count,
        'revenue': round(r.total_revenue or 0.0, 2)
    } for r in results]

    return jsonify({'status': 'success', 'top_products': data}), 200


@analytics_bp.route('/supply-vs-demand', methods=['GET'])
@admin_required
def get_supply_vs_demand():
    total_stock = db.session.query(func.sum(Product.quantity)).scalar() or 0
    total_ordered = Order.query.count()

    return jsonify({
        'status': 'success',
        'total_supply_quantity': total_stock,
        'total_demand_orders': total_ordered
    }), 200


@analytics_bp.route('/low-stock', methods=['GET'])
@admin_required
def get_low_stock():
    products = Product.query.filter(Product.quantity < 10).all()
    return jsonify({'status': 'success', 'count': len(products), 'products': [p.to_dict() for p in products]}), 200


@analytics_bp.route('/dead-stock', methods=['GET'])
@admin_required
def get_dead_stock():
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_product_ids = [r[0] for r in db.session.query(Order.product_id).filter(Order.transaction_date >= thirty_days_ago).distinct().all()]

    dead_products = Product.query.filter(~Product.id.in_(recent_product_ids)).all() if recent_product_ids else Product.query.all()

    return jsonify({'status': 'success', 'count': len(dead_products), 'products': [p.to_dict() for p in dead_products]}), 200


@analytics_bp.route('/sales-by-location', methods=['GET'])
@admin_required
def get_sales_by_location():
    results = db.session.query(
        Product.location,
        func.count(Order.id).label('orders'),
        func.sum(Order.amount).label('revenue')
    ).join(Order, Product.id == Order.product_id).group_by(Product.location).all()

    data = [{
        'location': r.location or 'Unknown',
        'orders': r.orders,
        'revenue': round(r.revenue or 0.0, 2)
    } for r in results]

    return jsonify({'status': 'success', 'locations': data}), 200


@analytics_bp.route('/orders-by-weekday', methods=['GET'])
@admin_required
def get_orders_by_weekday():
    orders = Order.query.all()
    weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    counts = {w: 0 for w in weekdays}

    for o in orders:
        if o.transaction_date:
            day_name = weekdays[o.transaction_date.weekday()]
            counts[day_name] += 1

    data = [{'day': w, 'count': counts[w]} for w in weekdays]
    return jsonify({'status': 'success', 'weekdays': data}), 200


@analytics_bp.route('/orders-by-hour', methods=['GET'])
@admin_required
def get_orders_by_hour():
    orders = Order.query.all()
    hours = {i: 0 for i in range(24)}

    for o in orders:
        if o.transaction_date:
            hours[o.transaction_date.hour] += 1

    data = [{'hour': f"{h:02d}:00", 'count': hours[h]} for h in range(24)]
    return jsonify({'status': 'success', 'hours': data}), 200


@analytics_bp.route('/orders-heatmap', methods=['GET'])
@admin_required
def get_orders_heatmap():
    orders = Order.query.all()
    weekdays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    matrix = [[0 for _ in range(24)] for _ in range(7)]

    for o in orders:
        if o.transaction_date:
            w = o.transaction_date.weekday()
            h = o.transaction_date.hour
            matrix[w][h] += 1

    return jsonify({'status': 'success', 'weekdays': weekdays, 'matrix': matrix}), 200


@analytics_bp.route('/user-growth', methods=['GET'])
@admin_required
def get_user_growth():
    results = db.session.query(
        func.date(User.created_at).label('date'),
        func.sum(case((User.user_type == 'consumer', 1), else_=0)).label('new_consumers'),
        func.sum(case((User.user_type == 'farmer', 1), else_=0)).label('new_farmers')
    ).group_by(func.date(User.created_at)).order_by('date').all()

    data = [{
        'period': r.date or 'Unknown',
        'new_consumers': r.new_consumers or 0,
        'new_farmers': r.new_farmers or 0
    } for r in results]

    return jsonify(data), 200


@analytics_bp.route('/payments-breakdown', methods=['GET'])
@admin_required
def get_payments_breakdown():
    results = db.session.query(
        Transaction.status,
        func.count(Transaction.id).label('count'),
        func.sum(Transaction.amount).label('total_amount')
    ).group_by(Transaction.status).all()

    data = [{
        'status': r.status,
        'count': r.count,
        'total_amount': round(r.total_amount or 0.0, 2)
    } for r in results]

    return jsonify({'status': 'success', 'data': data}), 200


@analytics_bp.route('/payment-methods', methods=['GET'])
@admin_required
def get_payment_methods():
    results = db.session.query(
        Transaction.payment_method,
        func.count(Transaction.id).label('count')
    ).group_by(Transaction.payment_method).all()

    data = [{
        'method': r.payment_method or 'Razorpay',
        'count': r.count
    } for r in results]

    return jsonify({'status': 'success', 'data': data}), 200
