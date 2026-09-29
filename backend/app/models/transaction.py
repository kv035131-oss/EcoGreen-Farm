"""
Transaction Model for payment gateway records.
"""

from datetime import datetime
from backend.app.extensions import db

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    razorpay_payment_id = db.Column(db.String(100), nullable=True)
    razorpay_order_id = db.Column(db.String(100), nullable=True)
    razorpay_signature = db.Column(db.String(200), nullable=True)
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(10), nullable=False, default='INR')
    status = db.Column(db.String(50), nullable=False, default='Created')
    payment_method = db.Column(db.String(50), nullable=True, default='Razorpay')
    transaction_date = db.Column(db.DateTime, default=datetime.utcnow)

    order = db.relationship('Order', backref=db.backref('transactions', lazy=True))
    user = db.relationship('User', backref=db.backref('transactions', lazy=True))

    def to_dict(self):
        return {
            'id': self.id,
            'order_id': self.order_id,
            'user_id': self.user_id,
            'razorpay_payment_id': self.razorpay_payment_id,
            'razorpay_order_id': self.razorpay_order_id,
            'amount': self.amount,
            'currency': self.currency or 'INR',
            'status': self.status,
            'payment_method': self.payment_method or 'Razorpay',
            'transaction_date': self.transaction_date.strftime("%Y-%m-%d %H:%M:%S") if self.transaction_date else None
        }
