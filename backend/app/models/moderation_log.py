"""
Product Moderation Log Model.
Tracks AI and Admin moderation decisions for product listings.
"""

from datetime import datetime
from backend.app.extensions import db

class ProductModerationLog(db.Model):
    __tablename__ = 'product_moderation_log'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    decision = db.Column(db.String(50), nullable=False) # approved, rejected, needs_review
    reason = db.Column(db.Text, nullable=True)
    raw_model_output = db.Column(db.Text, nullable=True)
    decided_by = db.Column(db.String(100), nullable=False) # 'ai' or user_id
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    product = db.relationship('Product', backref=db.backref('moderation_logs', lazy=True))

    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'user_id': self.user_id,
            'decision': self.decision,
            'reason': self.reason,
            'raw_model_output': self.raw_model_output,
            'decided_by': self.decided_by,
            'created_at': self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None
        }
