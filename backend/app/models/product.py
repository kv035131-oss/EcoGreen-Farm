"""
Product Model representing items listed by farmers.
"""

from datetime import datetime
from backend.app.extensions import db

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    name = db.Column(db.String(150), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)
    image = db.Column(db.Text)
    location = db.Column(db.String(150))
    quantity = db.Column(db.Integer, nullable=False)
    category = db.Column(db.String(100), nullable=True, default='Vegetables')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=True)

    # Content Moderation fields (pending / approved / rejected / needs_review)
    moderation_status = db.Column(db.String(50), nullable=False, default='pending')
    moderation_reason = db.Column(db.Text, nullable=True)
    moderated_at = db.Column(db.DateTime, nullable=True)
    moderated_by = db.Column(db.String(100), nullable=True)

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
            'moderation_status': self.moderation_status or 'pending',
            'moderation_reason': self.moderation_reason,
            'moderated_at': self.moderated_at.strftime("%Y-%m-%d %H:%M:%S") if self.moderated_at else None,
            'moderated_by': self.moderated_by,
            'created_at': self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None
        }

