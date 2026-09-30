"""
Authentication and User Management Routes Blueprint.
"""

from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token
from werkzeug.security import generate_password_hash, check_password_hash

from backend.app.extensions import db
from backend.app.models.user import User

auth_bp = Blueprint('auth_bp', __name__)

def generate_token(user: User) -> str:
    return create_access_token(identity=str(user.id), additional_claims={
        'user_id': user.id,
        'username': user.username,
        'email': user.email,
        'user_type': user.user_type
    })

@auth_bp.route('/api/v1/Login', methods=['POST'])
def login():
    data = request.json or {}
    username = data.get("username")
    password = data.get("password")
    user = User.query.filter_by(username=username).first()
    if user and check_password_hash(user.password, password):
        user.last_active_at = datetime.utcnow()
        db.session.commit()
        access_token = generate_token(user)
        return jsonify({
            "access-token": access_token,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "user_type": user.user_type,
                "phone_number": user.phone_number,
                "status": user.status
            }
        }), 200
    else:
        return jsonify({
            'error': "Invalid credentials",
        }), 401


@auth_bp.route('/api/v1/user/profile', methods=['GET'])
@jwt_required(optional=True)
def get_user_profile():
    try:
        current_user_id = get_jwt_identity()
        if not current_user_id:
            return jsonify({'error': 'Not logged in'}), 401
        user = User.query.get(current_user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        return jsonify({
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'user_type': user.user_type,
                'phone_number': user.phone_number,
                'status': user.status
            }
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/api/v1/User/create', methods=['POST'])
def create_user():
    data = request.json or {}

    username = data.get('username')
    phone_number = data.get('phone_number', 0)
    password = data.get('password')
    email = data.get('email', f"{username.lower().replace(' ', '')}@example.com" if username else "user@example.com")                    
    user_type = data.get('user_type', 'consumer')
    status = 'Active'
    
    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Username already exists'}), 409
    if email and User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email already exists'}), 409

    password_harsh = generate_password_hash(password)
    user = User(username=username, email=email, password=password_harsh, 
                user_type=user_type, status=status, phone_number=phone_number)

    db.session.add(user)
    db.session.commit()
    
    access_token = generate_token(user)
    return jsonify({
        'message': 'User created successfully',
        'access-token': access_token,
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'user_type': user.user_type,
            'phone_number': user.phone_number,
            'status': user.status
        }
    }), 201


@auth_bp.route('/api/v1/User', methods=['GET'])
def view_all_user():
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))

    user_page = User.query.paginate(page=page, per_page=per_page, error_out=False)
    user_list = []
    for user in user_page.items:
        user_data = {
            'id': user.id,
            'username': user.username,
            'phone number': user.phone_number,
            'email': user.email,
            'user_type': user.user_type,
            'status': user.status
        }
        user_list.append(user_data)

    return jsonify({
        'status': 'success',
        'data': user_list
    })

