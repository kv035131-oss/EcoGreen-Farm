"""
Payment Gateway Integration Routes Blueprint.
"""

import hmac
import hashlib
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity

from backend.app.extensions import db
from backend.app.models.order import Order
from backend.app.models.transaction import Transaction
from backend.app.services.payment_service import create_razorpay_order, verify_payment_signature
from backend.app.services.order_service import trigger_order_notifications, serialize_order

payments_bp = Blueprint('payments_bp', __name__)

@payments_bp.route('/pay', methods=['POST'])
@jwt_required(optional=True)
def pay_order():
    try:
        data = request.json or {}
        current_user_id = get_jwt_identity()

        order_id = data.get('order_id')
        if order_id:
            order = Order.query.get(order_id)
        else:
            product_id = int(data.get('product_id', 1))
            user_id = int(data.get('user_id', current_user_id or 1))
            amount = float(data.get('amount', 10.0))
            phone_number = str(data.get('phone_number', '254700000000'))
            
            order = Order(
                product_id=product_id,
                user_id=user_id,
                amount=amount,
                phone_number=phone_number,
                order_status='Pending'
            )
            db.session.add(order)
            db.session.commit()
            trigger_order_notifications(order, 'order_placed')

        if not order:
            return jsonify({'error': 'Order not found', 'status': 'error'}), 404

        simulate = current_app.config.get('RAZORPAY_SIMULATE', True)
        key_id = current_app.config.get('RAZORPAY_KEY_ID', 'rzp_test_sample')
        key_secret = current_app.config.get('RAZORPAY_KEY_SECRET', 'sample_secret')

        if simulate or key_id == 'rzp_test_sample' or not key_id or not key_secret:
            simulated_payment_id = f"pay_sim_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{order.id}"
            simulated_order_id = f"order_sim_{order.id}"

            txn = Transaction(
                order_id=order.id,
                user_id=order.user_id,
                razorpay_order_id=simulated_order_id,
                razorpay_payment_id=simulated_payment_id,
                razorpay_signature='simulated_signature',
                amount=order.amount,
                status='Success'
            )
            db.session.add(txn)
            db.session.commit()
            trigger_order_notifications(order, 'payment_success')

            return jsonify({
                'simulate': True,
                'status': 'success',
                'message': 'Simulated payment successful. Order marked as Paid.',
                'order_id': order.id,
                'order': serialize_order(order),
                'transaction': txn.to_dict()
            }), 200

        rzp_order = create_razorpay_order(order.amount, order.id)
        razorpay_order_id = rzp_order.get('id')

        txn = Transaction(
            order_id=order.id,
            user_id=order.user_id,
            razorpay_order_id=razorpay_order_id,
            amount=order.amount,
            status='Created'
        )
        db.session.add(txn)
        db.session.commit()

        return jsonify({
            'simulate': False,
            'status': 'success',
            'order_id': order.id,
            'razorpay_order_id': razorpay_order_id,
            'amount': rzp_order.get('amount'),
            'amount_inr': order.amount,
            'currency': rzp_order.get('currency', 'INR'),
            'key_id': key_id
        }), 200

    except Exception as e:
        db.session.rollback()
        print("Payment error:", e)
        return jsonify({'error': str(e), 'status': 'error'}), 500


@payments_bp.route('/api/v1/payments/verify', methods=['POST'])
@jwt_required(optional=True)
def verify_payment():
    try:
        data = request.json or {}
        razorpay_order_id = data.get('razorpay_order_id')
        razorpay_payment_id = data.get('razorpay_payment_id')
        razorpay_signature = data.get('razorpay_signature')

        if not razorpay_order_id or not razorpay_payment_id or not razorpay_signature:
            return jsonify({'error': 'Missing payment verification parameters', 'status': 'error'}), 400

        txn = Transaction.query.filter_by(razorpay_order_id=razorpay_order_id).first()
        if not txn:
            return jsonify({'error': 'Transaction record not found', 'status': 'error'}), 404

        is_valid = verify_payment_signature(razorpay_order_id, razorpay_payment_id, razorpay_signature)

        if is_valid:
            txn.status = 'Success'
            txn.razorpay_payment_id = razorpay_payment_id
            txn.razorpay_signature = razorpay_signature

            order = Order.query.get(txn.order_id)
            if order:
                trigger_order_notifications(order, 'payment_success')

            db.session.commit()
            return jsonify({
                'message': 'Payment verified and order marked as Paid',
                'status': 'success',
                'order_id': txn.order_id,
                'order': serialize_order(order) if order else None
            }), 200
        else:
            txn.status = 'Failed'
            db.session.commit()
            return jsonify({'error': 'Invalid payment signature. Verification failed.', 'status': 'error'}), 400

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e), 'status': 'error'}), 500


@payments_bp.route('/api/v1/payments/webhook', methods=['POST'])
def razorpay_webhook():
    try:
        raw_body = request.get_data()
        signature_header = request.headers.get('X-Razorpay-Signature', '')
        webhook_secret = current_app.config.get('RAZORPAY_WEBHOOK_SECRET', '')

        if webhook_secret and webhook_secret != 'sample_webhook_secret':
            expected_sig = hmac.new(
                webhook_secret.encode('utf-8'),
                raw_body,
                hashlib.sha256
            ).hexdigest()

            if not hmac.compare_digest(expected_sig, signature_header):
                print("Razorpay webhook signature mismatch")
                return jsonify({'status': 'error', 'message': 'Invalid signature'}), 400

        payload = request.json or {}
        event = payload.get('event')

        if event in ['payment.captured', 'order.paid']:
            payment_entity = payload.get('payload', {}).get('payment', {}).get('entity', {})
            razorpay_order_id = payment_entity.get('order_id')
            razorpay_payment_id = payment_entity.get('id')

            if razorpay_order_id:
                txn = Transaction.query.filter_by(razorpay_order_id=razorpay_order_id).first()
                if txn:
                    txn.status = 'Success'
                    txn.razorpay_payment_id = razorpay_payment_id
                    db.session.commit()

        return jsonify({'status': 'ok'}), 200
    except Exception as e:
        db.session.rollback()
        print("Webhook processing error:", e)
        return jsonify({'status': 'error', 'message': str(e)}), 200
