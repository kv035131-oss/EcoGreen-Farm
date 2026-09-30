"""
Order Service Layer handling order notifications and order state transitions.
"""

from datetime import datetime
from backend.app.extensions import db
from backend.app.models.order import Order
from backend.app.models.product import Product
from backend.app.models.user import User
from backend.app.services.notification_service import notify

def trigger_order_notifications(order: Order, event_type: str):
    """Triggers notifications for order state updates."""
    try:
        product = Product.query.get(order.product_id)
        consumer = User.query.get(order.user_id)
        farmer = User.query.get(product.user_id) if product else None

        prod_name = product.name if product else 'Produce'
        cons_name = consumer.username if consumer else 'Customer'
        farmer_name = farmer.username if farmer else 'Farmer'
        qty = getattr(product, 'quantity', 1)

        if event_type == 'order_placed' and farmer:
            notify(farmer, 'order_placed_farmer', order_id=order.id, quantity=qty, product_name=prod_name, consumer_name=cons_name)

        elif event_type == 'payment_success':
            if consumer:
                notify(consumer, 'payment_success_consumer', receipt_no=f"RCP-{order.id}", amount=f"{order.amount:,.2f}", order_id=order.id, product_name=prod_name)
            if farmer:
                notify(farmer, 'payment_success_farmer', amount=f"{order.amount:,.2f}", order_id=order.id, product_name=prod_name, consumer_name=cons_name)

        elif event_type == 'order_accepted' and consumer:
            notify(consumer, 'order_accepted_consumer', farmer_name=farmer_name, order_id=order.id, product_name=prod_name)

        elif event_type == 'order_rejected' and consumer:
            notify(consumer, 'order_rejected_consumer', farmer_name=farmer_name, order_id=order.id, product_name=prod_name)

        elif event_type == 'order_delivered' and consumer:
            notify(consumer, 'order_delivered_consumer', order_id=order.id, product_name=prod_name)

    except Exception as e:
        print("Notification trigger error (swallowed):", e)


def serialize_order(order: Order, requesting_user_id: int = None, requesting_user_role: str = None) -> dict:
    """
    Serializes Order model into frontend JSON dictionary format.
    Enforces Privacy Rule (Step A5): Consumer delivery lat/lng is visible ONLY to assigned farmer,
    order consumer, or admin.
    """
    product = Product.query.get(order.product_id)
    user = User.query.get(order.user_id)

    show_coordinates = False
    if requesting_user_role == 'admin':
        show_coordinates = True
    elif requesting_user_id:
        try:
            req_id = int(requesting_user_id)
            if req_id == order.user_id or (product and req_id == product.user_id):
                show_coordinates = True
        except (ValueError, TypeError):
            show_coordinates = False

    return {
        'id': order.id,
        'product_id': order.product_id,
        'product_name': product.name if product else f"Produce #{order.product_id}",
        'product_image': product.image if product else 'https://images.unsplash.com/photo-1542838132-92c53300491e?w=500',
        'product_farmer_id': product.user_id if product else None,
        'user_id': order.user_id,
        'user_name': user.username if user else 'Customer',
        'amount': order.amount,
        'phone_number': order.phone_number,
        'delivery_address_text': order.delivery_address_text or 'Customer Location',
        'delivery_district': order.delivery_district,
        'delivery_state': order.delivery_state,
        'delivery_latitude': order.delivery_latitude if show_coordinates else None,
        'delivery_longitude': order.delivery_longitude if show_coordinates else None,
        'status': order.order_status or 'Pending',
        'payment_status': getattr(order, 'payment_status', 'Unpaid') or 'Unpaid',
        'orderDate': getattr(order, 'transaction_date', order.confirmed_at or datetime.utcnow()).strftime("%Y-%m-%d %H:%M") if getattr(order, 'transaction_date', None) else datetime.utcnow().strftime("%Y-%m-%d %H:%M")
    }
