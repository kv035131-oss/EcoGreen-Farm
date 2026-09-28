"""
Product Management Routes Blueprint.
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func
import cloudinary
import cloudinary.uploader

from backend.app.extensions import db
from backend.app.models.user import User
from backend.app.models.product import Product
from backend.app.models.reviews import Reviews
from backend.app.services.notification_service import notify

products_bp = Blueprint('products_bp', __name__)

@products_bp.route('/api/v1/products/create', methods=['POST'])
@jwt_required(optional=True)
def create_product():
    try:
        data = request.form if (request.form and len(request.form) > 0) else (request.json or {})
        current_user_id = get_jwt_identity()

        user_id = data.get('user_id')
        if not user_id and current_user_id:
            user_id = int(current_user_id)

        if user_id:
            user = User.query.get(int(user_id))
            if user and user.user_type == 'admin':
                return jsonify({'error': 'Admins are not allowed to create products.', 'status': 'error'}), 403

        image = request.files.get('image') if request.files else None
        if image:
            try:
                result = cloudinary.uploader.upload(image)
                image_url = result.get('secure_url')
            except Exception:
                image_url = data.get('image', 'https://images.unsplash.com/photo-1542838132-92c53300491e?w=500')
        else:
            image_url = data.get('image', 'https://images.unsplash.com/photo-1542838132-92c53300491e?w=500')

        if not image_url or image_url.strip() == '':
            image_url = 'https://images.unsplash.com/photo-1542838132-92c53300491e?w=500'

        name = data.get('name', 'Fresh Produce').strip()
        price = float(data.get('price', 10.0))
        quantity = int(data.get('quantity', 1))
        location = data.get('location', 'Local Farm').strip()
        description = data.get('description', 'Fresh farm produce.').strip()

        product = Product(
            user_id=int(user_id) if user_id else None,
            name=name,
            price=price,
            description=description,
            image=image_url,
            location=location,
            quantity=quantity
        )
        db.session.add(product)
        db.session.commit()

        if product.quantity < 10 and product.user_id:
            farmer = User.query.get(product.user_id)
            if farmer:
                notify(farmer, 'low_stock_farmer', product_name=product.name, quantity=product.quantity)
        return jsonify({'message': 'Product created successfully', 'status': 'success', 'product': product.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e), 'status': 'error'}), 400


@products_bp.route('/api/v1/products', methods=['GET'])
@jwt_required(optional=True)
def view_all_products():
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 50))

    products_page = Product.query.order_by(Product.id.desc()).paginate(page=page, per_page=per_page, error_out=False)
    
    product_list = []
    for product in products_page.items:
        product_list.append(product.to_dict())

    return jsonify({
        'status': 'success',
        'data': product_list,
        'pages': products_page.pages
    }), 200


@products_bp.route('/api/v1/products/<int:id>', methods=['GET'])
def view_product(id):
    product = Product.query.get(id)
    if not product:
        return jsonify({'error': 'Product not found'}), 404
        
    comments = Reviews.query.filter_by(product_id=id).all()
    avg_rating = db.session.query(func.avg(Reviews.rating)).filter(Reviews.product_id == id).scalar()
    
    comment_list = []
    for comment in comments:
        user = User.query.get(comment.user_id)
        if user:
            comment_list.append({
                'comment': comment.comment,
                'user_username': user.username
            })
    
    return jsonify({
        'id': product.id,
        'user_id': product.user_id,
        'name': product.name,
        'price': product.price,
        'description': product.description,
        'image': product.image,
        'location': product.location,
        'quantity': product.quantity,
        'avg_rating': round(avg_rating, 1) if avg_rating else 5.0,
        'comments': comment_list
    }), 200
