"""
Order Model representing purchase transactions between consumers and farmers.
"""

from datetime import datetime
from backend.app.extensions import db

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    order_status = db.Column(db.String(50), default='Pending')
    confirmed_at = db.Column(db.DateTime, nullable=True)
    cancelled_at = db.Column(db.DateTime, nullable=True)
    delivered_at = db.Column(db.DateTime, nullable=True)

    product = db.relationship('Product', backref=db.backref('orders', lazy=True))
    user = db.relationship('User', backref=db.backref('orders', lazy=True))

    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'user_id': self.user_id,
            'amount': self.amount,
            'phone_number': self.phone_number,
            'order_status': self.order_status,
            'confirmed_at': self.confirmed_at.strftime("%Y-%m-%d %H:%M:%S") if self.confirmed_at else None,
            'cancelled_at': self.cancelled_at.strftime("%Y-%m-%d %H:%M:%S") if self.cancelled_at else None,
            'delivered_at': self.delivered_at.strftime("%Y-%m-%d %H:%M:%S") if self.delivered_at else None
        }
