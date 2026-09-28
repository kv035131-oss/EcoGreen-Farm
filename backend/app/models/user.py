"""
User Model representing Farmers, Consumers, and Admins.
"""

from datetime import datetime
from backend.app.extensions import db

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

    # Notification preferences
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
