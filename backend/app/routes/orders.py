"""
Order Management Routes Blueprint.
"""

from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from backend.app.extensions import db
from backend.app.models.order import Order
from backend.app.models.product import Product
from backend.app.models.user import User
from backend.app.services.order_service import trigger_order_notifications, serialize_order

orders_bp = Blueprint('orders_bp', __name__)

@orders_bp.route('/api/v1/Orders', methods=['GET'])
@jwt_required(optional=True)
def view_all_orders():
    current_user_id = get_jwt_identity()
    if current_user_id:
        return view_my_orders(int(current_user_id))

    return jsonify({'status': 'success', 'data': []})


@orders_bp.route('/api/v1/Orders/<int:user_id>', methods=['GET'])
def view_my_orders(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({'status': 'success', 'data': []})

    if user.user_type == 'farmer':
        farmer_product_ids = [p.id for p in Product.query.filter_by(user_id=user_id).all()]
        if farmer_product_ids:
            orders = Order.query.filter(
                (Order.user_id == user_id) | (Order.product_id.in_(farmer_product_ids))
            ).order_by(Order.id.desc()).all()
        else:
            orders = Order.query.filter_by(user_id=user_id).order_by(Order.id.desc()).all()
    else:
        orders = Order.query.filter_by(user_id=user_id).order_by(Order.id.desc()).all()

    order_list = [serialize_order(o) for o in orders]
    return jsonify({
        'status': 'success',
        'data': order_list
    })


@orders_bp.route('/api/v1/Orders/create', methods=['POST'])
@jwt_required(optional=True)
def create_order():
    try:
        data = request.json or {}

        user_id = int(data.get('user_id', 1))
        current_user_id = get_jwt_identity()
        if current_user_id:
            user_id = int(current_user_id)

        user = User.query.get(user_id)
        if user and user.user_type == 'admin':
            return jsonify({'error': 'Admins are not allowed to place orders.', 'status': 'error'}), 403

        product_id = int(data.get('product_id', 1))
        amount = float(data.get('amount', 10.0))
        phone_number = str(data.get('phone_number', '254700000000'))
        status = data.get('status', 'Pending')

        order = Order(
            product_id=product_id,
            user_id=user_id,
            amount=amount,
            order_status=status,
            payment_status='Unpaid',
            phone_number=phone_number
        )
        db.session.add(order)
        db.session.commit()
        trigger_order_notifications(order, 'order_placed')
        return jsonify({
            'message': 'Order created successfully',
            'status': 'success',
            'order_id': order.id,
            'order': serialize_order(order)
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e), 'status': 'error'}), 400


@orders_bp.route('/api/v1/Orders/<int:order_id>/status', methods=['PUT', 'POST'])
@jwt_required(optional=True)
def update_order_status(order_id):
    try:
        order = Order.query.get(order_id)
        if not order:
            return jsonify({'error': 'Order not found', 'status': 'error'}), 404

        data = request.json or {}
        new_status = data.get('status', 'Confirmed')

        order.order_status = new_status
        now = datetime.utcnow()
        if new_status == 'Confirmed' and not order.confirmed_at:
            order.confirmed_at = now
            trigger_order_notifications(order, 'order_accepted')
        elif new_status in ['Rejected', 'Cancelled'] and not order.cancelled_at:
            order.cancelled_at = now
            trigger_order_notifications(order, 'order_rejected')
        elif new_status == 'Delivered' and not order.delivered_at:
            order.delivered_at = now
            if not order.confirmed_at:
                order.confirmed_at = now
            trigger_order_notifications(order, 'order_delivered')

        db.session.commit()

        return jsonify({
            'message': f'Order status updated to {new_status}',
            'status': 'success',
            'order': serialize_order(order)
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e), 'status': 'error'}), 400


@orders_bp.route('/api/v1/Orders/<int:order_id>/deliver', methods=['PUT', 'POST'])
@jwt_required(optional=True)
def mark_order_delivered(order_id):
    try:
        order = Order.query.get(order_id)
        if not order:
            return jsonify({'error': 'Order not found', 'status': 'error'}), 404

        order.order_status = 'Delivered'
        now = datetime.utcnow()
        order.delivered_at = now
        if not order.confirmed_at:
            order.confirmed_at = now
        db.session.commit()
        trigger_order_notifications(order, 'order_delivered')

        return jsonify({
            'message': 'Order marked as Delivered',
            'status': 'success',
            'order': serialize_order(order)
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e), 'status': 'error'}), 400
