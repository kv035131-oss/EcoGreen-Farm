"""
Razorpay Payment Gateway Service
Handles order creation, signature verification, and webhook signature verification.
"""

import os
import razorpay
from flask import current_app

def get_razorpay_client():
    key_id = current_app.config.get('RAZORPAY_KEY_ID', os.environ.get('RAZORPAY_KEY_ID', 'rzp_test_sample'))
    key_secret = current_app.config.get('RAZORPAY_KEY_SECRET', os.environ.get('RAZORPAY_KEY_SECRET', 'sample_secret'))
    return razorpay.Client(auth=(key_id, key_secret))

def create_razorpay_order(amount, receipt_id):
    """
    Creates a Razorpay order.
    amount: float/int amount in INR.
    receipt_id: ID or reference for the order.
    Returns Razorpay order dictionary.
    """
    client = get_razorpay_client()
    paise_amount = int(round(float(amount) * 100))
    order_data = {
        'amount': paise_amount,
        'currency': 'INR',
        'receipt': str(receipt_id),
        'payment_capture': 1
    }
    return client.order.create(data=order_data)

def verify_payment_signature(razorpay_order_id, razorpay_payment_id, razorpay_signature):
    """
    Verifies Razorpay payment signature received from frontend checkout.js callback.
    Returns True if signature is valid, False otherwise.
    """
    client = get_razorpay_client()
    params_dict = {
        'razorpay_order_id': razorpay_order_id,
        'razorpay_payment_id': razorpay_payment_id,
        'razorpay_signature': razorpay_signature
    }
    try:
        client.utility.verify_payment_signature(params_dict)
        return True
    except Exception as e:
        print("Razorpay signature verification failed:", e)
        return False

def verify_webhook_signature(body_bytes, signature_header, webhook_secret):
    """
    Verifies Razorpay webhook signature from request body and header.
    Returns True if valid, False otherwise.
    """
    client = get_razorpay_client()
    try:
        client.utility.verify_webhook_signature(
            body_bytes.decode('utf-8') if isinstance(body_bytes, bytes) else str(body_bytes),
            signature_header,
            webhook_secret
        )
        return True
    except Exception as e:
        print("Razorpay webhook signature verification failed:", e)
        return False
