"""
Role-based authorization decorators for Flask-JWT-Extended routes.
"""

from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt_identity
from backend.app.models.user import User

def admin_required(fn):
    """Ensures current authenticated user is an admin."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        current_user_id = get_jwt_identity()
        if not current_user_id:
            return jsonify({'error': 'Authentication required', 'status': 'error'}), 401
            
        user = User.query.get(current_user_id)
        if not user or user.user_type != 'admin':
            return jsonify({'error': 'Admin privileges required', 'status': 'error'}), 403
            
        return fn(*args, **kwargs)
    return wrapper

def farmer_required(fn):
    """Ensures current authenticated user is a farmer."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        current_user_id = get_jwt_identity()
        if not current_user_id:
            return jsonify({'error': 'Authentication required', 'status': 'error'}), 401
            
        user = User.query.get(current_user_id)
        if not user or user.user_type != 'farmer':
            return jsonify({'error': 'Farmer role required', 'status': 'error'}), 403
            
        return fn(*args, **kwargs)
    return wrapper
