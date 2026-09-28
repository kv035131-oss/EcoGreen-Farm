"""
EcoGreen Background Task Scheduler (APScheduler)
Handles periodic background jobs such as:
- Farmer 6-hour order reminder for pending orders.
"""

import logging
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger('ecogreen.scheduler')

scheduler = None

def check_pending_order_reminders(app):
    """Job running every 15 minutes to remind farmers of orders pending for 6+ hours."""
    with app.app_context():
        try:
            from backend.app.models import db, Order, Product, User, NotificationLog
            from backend.app.services.notification_service import notify

            six_hours_ago = datetime.utcnow() - timedelta(hours=6)

            pending_orders = Order.query.filter(
                Order.order_status == 'Pending',
                Order.confirmed_at.is_(None),
                Order.cancelled_at.is_(None),
                Order.transaction_date <= six_hours_ago
            ).all()

            for order in pending_orders:
                # Check if reminder already sent for this order
                already_reminded = NotificationLog.query.filter(
                    NotificationLog.event_type == 'farmer_order_reminder',
                    NotificationLog.message.like(f"%#{order.id}%")
                ).first()

                if already_reminded:
                    continue

                product = Product.query.get(order.product_id)
                if not product or not product.user_id:
                    continue

                farmer = User.query.get(product.user_id)
                consumer = User.query.get(order.user_id)

                if farmer:
                    notify(
                        farmer,
                        'farmer_order_reminder',
                        order_id=order.id,
                        quantity=getattr(product, 'quantity', 1),
                        product_name=product.name if product else 'Produce',
                        consumer_name=consumer.username if consumer else 'Customer'
                    )
                    logger.info(f"Sent 6-hour reminder to Farmer {farmer.username} for Order #{order.id}.")

        except Exception as e:
            logger.error(f"Error in check_pending_order_reminders job: {e}")


def init_scheduler(app):
    global scheduler
    if scheduler is None or not scheduler.running:
        scheduler = BackgroundScheduler(daemon=True)
        scheduler.add_job(
            func=check_pending_order_reminders,
            args=[app],
            trigger=IntervalTrigger(minutes=15),
            id='farmer_6hr_reminder_job',
            name='Check 6-hour pending order reminders',
            replace_existing=True
        )
        scheduler.start()
        logger.info("APScheduler initialized: 6-hour farmer order reminder job running every 15 mins.")
