"""
Search Model for recording search queries and analytics.
"""

from backend.app.extensions import db

class Search(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    query = db.Column(db.String(100), nullable=False)

    user = db.relationship('User', backref=db.backref('searches', lazy=True))

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'query': self.query
        }
