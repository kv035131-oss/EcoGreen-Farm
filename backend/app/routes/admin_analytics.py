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
from backend.app.models.moderation_log import ProductModerationLog

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
    if start_date and end_date:
        order_query = order_query.filter(Order.transaction_date >= start_date, Order.transaction_date <= end_date)

    total_orders = order_query.count()
    pending_orders = order_query.filter(Order.order_status == 'Pending').count()
    confirmed_orders = order_query.filter(Order.order_status == 'Confirmed').count()
    delivered_orders = order_query.filter(Order.order_status == 'Delivered').count()
    cancelled_orders = order_query.filter(Order.order_status == 'Cancelled').count()
    completed_orders = confirmed_orders + delivered_orders

    total_revenue = db.session.query(func.sum(Order.amount)).filter(
        *( [Order.transaction_date >= start_date, Order.transaction_date <= end_date] if start_date else [] )
    ).scalar() or 0.0

    avg_order_value = round(total_revenue / total_orders, 2) if total_orders > 0 else 0.0

    paid_orders = order_query.filter(Order.payment_status.in_(['Paid', 'Success'])).count()
    unpaid_orders = total_orders - paid_orders

    total_farmers = User.query.filter_by(user_type='farmer').count()
    total_consumers = User.query.filter_by(user_type='consumer').count()

    confirmation_rate_pct = round((completed_orders / total_orders * 100), 1) if total_orders > 0 else 0.0
    cancellation_rate_pct = round((cancelled_orders / total_orders * 100), 1) if total_orders > 0 else 0.0

    consumer_orders = db.session.query(Order.user_id, func.count(Order.id).label('cnt')).group_by(Order.user_id).all()
    repeat_buyers = sum(1 for c in consumer_orders if c.cnt > 1)
    total_buyers = len(consumer_orders)
    repeat_customer_rate_pct = round((repeat_buyers / total_buyers * 100), 1) if total_buyers > 0 else 0.0

    total_txns = Transaction.query.count()
    success_txns = Transaction.query.filter_by(status='Success').count()
    payment_success_rate_pct = round((success_txns / total_txns * 100), 1) if total_txns > 0 else (100.0 if total_orders > 0 else 0.0)

    metrics = {
        'total_revenue': round(total_revenue, 2),
        'total_orders': total_orders,
        'avg_order_value': avg_order_value,
        'pending_orders': pending_orders,
        'confirmed_orders': confirmed_orders,
        'delivered_orders': delivered_orders,
        'completed_orders': completed_orders,
        'cancelled_orders': cancelled_orders,
        'paid_orders': paid_orders,
        'unpaid_orders': unpaid_orders,
        'total_farmers': total_farmers,
        'total_consumers': total_consumers,
        'active_farmers': total_farmers,
        'active_consumers': total_consumers,
        'confirmation_rate_pct': confirmation_rate_pct,
        'cancellation_rate_pct': cancellation_rate_pct,
        'repeat_customer_rate_pct': repeat_customer_rate_pct,
        'payment_success_rate_pct': payment_success_rate_pct,
        'fulfillment_rate': confirmation_rate_pct,
        'orders_growth_pct': 0.0,
        'revenue_growth_pct': 0.0
    }

    response = {
        'status': 'success',
        **metrics,
        'summary': metrics
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
    orders = db.session.query(Order, Product).join(Product, Order.product_id == Product.id).all()
    location_stats = {}

    for order, product in orders:
        district = order.delivery_district or product.district
        state = order.delivery_state or product.state

        if district and state:
            loc_key = f"{district}, {state}"
        elif district:
            loc_key = district
        elif state:
            loc_key = state
        else:
            loc_key = order.delivery_address_text or product.address_text or product.location or 'Local Region'

        if loc_key not in location_stats:
            location_stats[loc_key] = {'orders': 0, 'revenue': 0.0, 'district': district, 'state': state}

        location_stats[loc_key]['orders'] += 1
        location_stats[loc_key]['revenue'] += (order.amount or 0.0)

    data = [{
        'location': loc,
        'district': stats['district'],
        'state': stats['state'],
        'orders': stats['orders'],
        'revenue': round(stats['revenue'], 2)
    } for loc, stats in location_stats.items()]

    data.sort(key=lambda x: x['revenue'], reverse=True)

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


# ==========================================
# CONTENT MODERATION QUEUE ENDPOINTS
# ==========================================

@analytics_bp.route('/moderation/pending', methods=['GET'])
@admin_required
def get_pending_moderation():
    """
    GET /api/v1/admin/moderation/pending
    Returns list of products awaiting admin review or rejected, with farmer info & AI reasons.
    """
    status_filter = request.args.get('status')
    if status_filter:
        query = Product.query.filter(Product.moderation_status == status_filter)
    else:
        query = Product.query.filter(Product.moderation_status.in_(['needs_review', 'pending', 'rejected']))

    products = query.order_by(Product.id.desc()).all()
    
    data = []
    for p in products:
        farmer = User.query.get(p.user_id) if p.user_id else None
        item = p.to_dict()
        item['farmer_name'] = farmer.username if farmer else 'Unknown Farmer'
        item['farmer_email'] = farmer.email if farmer else 'N/A'
        item['farmer_flagged'] = farmer.flagged if farmer else False
        item['farmer_flag_note'] = farmer.flag_note if farmer else None
        data.append(item)

    return jsonify({
        'status': 'success',
        'count': len(data),
        'data': data
    }), 200


@analytics_bp.route('/moderation/count', methods=['GET'])
@admin_required
def get_moderation_count():
    """
    GET /api/v1/admin/moderation/count
    Returns count of products needing admin review.
    """
    pending_count = Product.query.filter(Product.moderation_status.in_(['needs_review', 'pending'])).count()
    rejected_count = Product.query.filter(Product.moderation_status == 'rejected').count()
    return jsonify({
        'status': 'success',
        'pending_count': pending_count,
        'rejected_count': rejected_count
    }), 200


@analytics_bp.route('/moderation/<int:product_id>/approve', methods=['POST'])
@admin_required
def approve_product_moderation(product_id):
    """
    POST /api/v1/admin/moderation/<product_id>/approve
    Admin manual override approval for a product.
    """
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'error': 'Product not found', 'status': 'error'}), 404

    product.moderation_status = 'approved'
    product.moderation_reason = 'Approved by Admin override.'
    product.moderated_at = datetime.utcnow()
    product.moderated_by = 'admin'

    log_entry = ProductModerationLog(
        product_id=product.id,
        decision='approved',
        reason='Approved by Admin override.',
        raw_model_output='Admin Override',
        decided_by='admin',
        created_at=datetime.utcnow()
    )
    db.session.add(log_entry)
    db.session.commit()

    return jsonify({
        'status': 'success',
        'message': f"Product '{product.name}' approved successfully.",
        'product': product.to_dict()
    }), 200


@analytics_bp.route('/moderation/<int:product_id>/reject', methods=['POST'])
@admin_required
def reject_product_moderation(product_id):
    """
    POST /api/v1/admin/moderation/<product_id>/reject
    Admin manual override rejection for a product with custom reason.
    """
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'error': 'Product not found', 'status': 'error'}), 404

    req_data = request.json or {}
    reason = req_data.get('reason', 'Rejected by Admin review').strip()

    product.moderation_status = 'rejected'
    product.moderation_reason = reason
    product.moderated_at = datetime.utcnow()
    product.moderated_by = 'admin'

    log_entry = ProductModerationLog(
        product_id=product.id,
        decision='rejected',
        reason=reason,
        raw_model_output='Admin Override',
        decided_by='admin',
        created_at=datetime.utcnow()
    )
    db.session.add(log_entry)

    # Check farmer abuse prevention (3+ rejections in 7 days -> flag account)
    if product.user_id:
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        farmer_rejections = db.session.query(ProductModerationLog).join(Product).filter(
            Product.user_id == product.user_id,
            ProductModerationLog.decision == 'rejected',
            ProductModerationLog.created_at >= seven_days_ago
        ).count()

        if farmer_rejections >= 3:
            farmer = User.query.get(product.user_id)
            if farmer:
                farmer.flagged = True
                farmer.flag_note = f"Flagged automatically: {farmer_rejections} rejected product listings within 7 days (Last: '{product.name}')."

    db.session.commit()

    return jsonify({
        'status': 'success',
        'message': f"Product '{product.name}' rejected.",
        'product': product.to_dict()
    }), 200

