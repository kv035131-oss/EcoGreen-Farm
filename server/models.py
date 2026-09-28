from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float,ForeignKey
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate()

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    name = db.Column(db.String(150), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)
    image = db.Column(db.Text)  # Image URL or public_id
    location = db.Column(db.String(150))
    quantity = db.Column(db.Integer, nullable=False)
    category = db.Column(db.String(100), nullable=True, default='Vegetables')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=True)

    user = db.relationship('User', backref=db.backref('products', lazy=True))

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'price': self.price,
            'description': self.description,
            'image': self.image,
            'location': self.location,
            'quantity': self.quantity,
            'category': self.category or 'Vegetables',
            'created_at': self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None
        }

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    phone_number = db.Column(db.String(50), nullable=True)
    password = db.Column(db.String(200))
    email = db.Column(db.String(200), unique=True)
    user_type = db.Column(db.String(50)) # farmer, consumer, admin
    status = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_active_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=True)

    # WhatsApp & Notification preferences
    phone = db.Column(db.String(50), nullable=True)
    whatsapp_opt_in = db.Column(db.Boolean, default=False, nullable=False)
    last_inbound_whatsapp_at = db.Column(db.DateTime, nullable=True)
    notification_language = db.Column(db.String(10), default='en', nullable=False)

    @property
    def effective_phone(self):
        return self.phone or self.phone_number

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'user_type': self.user_type,
            'status': self.status,
            'phone': self.effective_phone,
            'phone_number': self.phone_number,
            'whatsapp_opt_in': self.whatsapp_opt_in or False,
            'last_inbound_whatsapp_at': self.last_inbound_whatsapp_at.strftime("%Y-%m-%d %H:%M:%S") if self.last_inbound_whatsapp_at else None,
            'notification_language': self.notification_language or 'en',
            'created_at': self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None
        }

    def repr(self):
        return f'<User {self.id}>'
    


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    mpesa_receipt_number = db.Column(db.String(255), nullable=True, default='N/A')
    merchant_request_id = db.Column(db.String(255), nullable=True, default='N/A')
    checkout_request_id = db.Column(db.String(255), nullable=True, default='N/A')
    result_code = db.Column(db.Integer, nullable=True, default=0)
    result_desc = db.Column(db.String(255), nullable=True, default='Pending')
    order_status = db.Column(db.String(50), nullable=False, default='Pending')
    payment_status = db.Column(db.String(50), nullable=False, default='Unpaid')
    phone_number = db.Column(db.String(50), nullable=False)
    transaction_date = db.Column(db.DateTime, default=datetime.utcnow)
    confirmed_at = db.Column(db.DateTime, nullable=True)
    cancelled_at = db.Column(db.DateTime, nullable=True)
    delivered_at = db.Column(db.DateTime, nullable=True)

    product = db.relationship('Product', backref=db.backref('orders', lazy=True))
    user = db.relationship('User', backref=db.backref('orders', lazy=True))
    
    def repr(self):
        return f'<Order {self.id}>'

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    razorpay_order_id = db.Column(db.String(255), nullable=True)
    razorpay_payment_id = db.Column(db.String(255), nullable=True)
    razorpay_signature = db.Column(db.String(255), nullable=True)
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(10), nullable=False, default='INR')
    status = db.Column(db.String(50), nullable=False, default='Created')  # Created, Success, Failed
    payment_method = db.Column(db.String(50), nullable=True, default='upi')  # upi, card, netbanking, wallet
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    order = db.relationship('Order', backref=db.backref('transactions', lazy=True))

    def to_dict(self):
        return {
            'id': self.id,
            'order_id': self.order_id,
            'razorpay_order_id': self.razorpay_order_id,
            'razorpay_payment_id': self.razorpay_payment_id,
            'razorpay_signature': self.razorpay_signature,
            'amount': self.amount,
            'currency': self.currency,
            'status': self.status,
            'created_at': self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None,
            'updated_at': self.updated_at.strftime("%Y-%m-%d %H:%M:%S") if self.updated_at else None
        }

    def repr(self):
        return f'<Transaction {self.id} Order {self.order_id} - {self.status}>'

class Reviews(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable= False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable= False)
    comment= db.Column(db.String())
    rating = db.Column(db.Integer())
    product=db.relationship('Product', backref= db.backref('reviews', lazy=True))
    user=db.relationship('User', backref= db.backref('reviews', lazy=True))


    def repr(self):
        return f'<Review {self.id}>'


class Search(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    keyword = db.Column(db.String(100), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('searches', lazy=True))

    def repr(self):
        return f'<Search {self.id}>'


class NotificationLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    channel = db.Column(db.String(50), default='whatsapp')
    event_type = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(50), default='queued') # queued, sent, failed, simulated, received
    provider_message_id = db.Column(db.String(255), nullable=True)
    error = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('notification_logs', lazy=True))

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.user.username if self.user else 'Unknown',
            'channel': self.channel,
            'event_type': self.event_type,
            'message': self.message,
            'status': self.status,
            'provider_message_id': self.provider_message_id,
            'error': self.error,
            'created_at': self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None
        }

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(50), default='info')
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('in_app_notifications', lazy=True))

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'message': self.message,
            'type': self.type,
            'is_read': self.is_read,
            'created_at': self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None
        }