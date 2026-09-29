"""
Product Management Routes Blueprint with Automated Content Moderation.
"""

from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func
import cloudinary
import cloudinary.uploader

from backend.app.extensions import db
from backend.app.models.user import User
from backend.app.models.product import Product
from backend.app.models.reviews import Reviews
from backend.app.models.moderation_log import ProductModerationLog
from backend.app.services.notification_service import notify
from backend.app.services.moderation_service import moderate_product_image

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

            # Security / Abuse Prevention: Rate limit max 20 listings per farmer per hour
            one_hour_ago = datetime.utcnow() - timedelta(hours=1)
            recent_listings_count = Product.query.filter(
                Product.user_id == int(user_id),
                Product.created_at >= one_hour_ago
            ).count()

            if recent_listings_count >= 20:
                return jsonify({
                    'error': 'Rate limit exceeded. Maximum 20 product listings per hour.',
                    'status': 'error'
                }), 429

        image_file = request.files.get('image') if request.files else None
        if image_file:
            try:
                result = cloudinary.uploader.upload(image_file)
                image_url = result.get('secure_url')
            except Exception:
                import base64
                image_bytes = image_file.read()
                image_file.seek(0)
                b64 = base64.b64encode(image_bytes).decode('utf-8')
                mime = image_file.mimetype or 'image/jpeg'
                image_url = f"data:{mime};base64,{b64}"
        else:
            image_url = data.get('image', 'https://images.unsplash.com/photo-1542838132-92c53300491e?w=500')

        if not image_url or image_url.strip() == '':
            image_url = 'https://images.unsplash.com/photo-1542838132-92c53300491e?w=500'

        name = data.get('name', 'Fresh Produce').strip()
        price = float(data.get('price', 10.0))
        quantity = int(data.get('quantity', 1))
        location = data.get('location', 'Local Farm').strip()
        description = data.get('description', 'Fresh farm produce.').strip()
        category = data.get('category', 'Vegetables').strip()

        # Step 1: Save product with initial pending status
        product = Product(
            user_id=int(user_id) if user_id else None,
            name=name,
            price=price,
            description=description,
            image=image_url,
            location=location,
            quantity=quantity,
            category=category,
            moderation_status='pending',
            created_at=datetime.utcnow()
        )
        db.session.add(product)
        db.session.flush()

        # Step 2: Run Content Moderation Engine
        mod_input = image_file if image_file else image_url
        mod_result = moderate_product_image(mod_input, category, name)

        decision = mod_result.get('decision', 'needs_review')
        reason = mod_result.get('reason', '')
        raw_output = mod_result.get('raw_model_output', '')

        product.moderation_status = decision
        product.moderation_reason = reason
        product.moderated_at = datetime.utcnow()
        product.moderated_by = 'ai'

        # Step 3: Write Moderation Log
        mod_log = ProductModerationLog(
            product_id=product.id,
            decision=decision,
            reason=reason,
            raw_model_output=raw_output,
            decided_by='ai',
            created_at=datetime.utcnow()
        )
        db.session.add(mod_log)

        # Step 4: Abuse Prevention Check for Farmer (3+ rejections in 7 days -> flag account)
        if decision == 'rejected' and product.user_id:
            seven_days_ago = datetime.utcnow() - timedelta(days=7)
            farmer_rejected_count = db.session.query(ProductModerationLog).join(Product).filter(
                Product.user_id == product.user_id,
                ProductModerationLog.decision == 'rejected',
                ProductModerationLog.created_at >= seven_days_ago
            ).count()

            if farmer_rejected_count >= 3:
                farmer = User.query.get(product.user_id)
                if farmer:
                    farmer.flagged = True
                    farmer.flag_note = f"Flagged automatically: {farmer_rejected_count} rejected product listings within 7 days (Last: '{product.name}')."

        db.session.commit()

        # Step 5: Notify low stock if applicable
        if product.quantity < 10 and product.user_id:
            farmer = User.query.get(product.user_id)
            if farmer:
                notify(farmer, 'low_stock_farmer', product_name=product.name, quantity=product.quantity)

        # Prepare user-facing response message
        if decision == 'approved':
            msg = "Product created and approved successfully!"
        elif decision == 'rejected':
            msg = f"Your listing for '{product.name}' was not approved: {reason}. Please upload a real, clear photo of your produce."
        else:
            msg = "Your listing is pending admin review."

        return jsonify({
            'message': msg,
            'status': 'success' if decision == 'approved' else decision,
            'moderation_status': decision,
            'moderation_reason': reason,
            'product': product.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e), 'status': 'error'}), 400


@products_bp.route('/api/v1/products', methods=['GET'])
@jwt_required(optional=True)
def view_all_products():
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 50))
    category = request.args.get('category')

    query = Product.query.filter(Product.moderation_status == 'approved')
    if category and category != 'All':
        query = query.filter(Product.category == category)

    products_page = query.order_by(Product.id.desc()).paginate(page=page, per_page=per_page, error_out=False)
    
    product_list = [product.to_dict() for product in products_page.items]

    return jsonify({
        'status': 'success',
        'data': product_list,
        'pages': products_page.pages
    }), 200


@products_bp.route('/api/v1/farmer/products', methods=['GET'])
@jwt_required(optional=True)
def view_farmer_products():
    current_user_id = get_jwt_identity()
    user_id = request.args.get('user_id') or current_user_id

    if not user_id:
        return jsonify({'error': 'User ID required', 'status': 'error'}), 400

    products = Product.query.filter(Product.user_id == int(user_id)).order_by(Product.id.desc()).all()
    product_list = [product.to_dict() for product in products]

    return jsonify({
        'status': 'success',
        'data': product_list
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
    
    data = product.to_dict()
    data['avg_rating'] = round(avg_rating, 1) if avg_rating else 5.0
    data['comments'] = comment_list
    return jsonify(data), 200


@products_bp.route('/api/v1/products/<int:id>', methods=['PUT', 'POST'])
@jwt_required(optional=True)
def update_product(id):
    product = Product.query.get(id)
    if not product:
        return jsonify({'error': 'Product not found'}), 404

    data = request.form if (request.form and len(request.form) > 0) else (request.json or {})
    
    if 'name' in data:
        product.name = data['name'].strip()
    if 'price' in data:
        product.price = float(data['price'])
    if 'quantity' in data:
        product.quantity = int(data['quantity'])
    if 'category' in data:
        product.category = data['category'].strip()
    if 'description' in data:
        product.description = data['description'].strip()

    image_file = request.files.get('image') if request.files else None
    if image_file:
        try:
            result = cloudinary.uploader.upload(image_file)
            product.image = result.get('secure_url')
        except Exception:
            if data.get('image'):
                product.image = data.get('image')

    # Re-run content moderation on update
    mod_input = image_file if image_file else product.image
    mod_result = moderate_product_image(mod_input, product.category, product.name)

    decision = mod_result.get('decision', 'needs_review')
    reason = mod_result.get('reason', '')
    raw_output = mod_result.get('raw_model_output', '')

    product.moderation_status = decision
    product.moderation_reason = reason
    product.moderated_at = datetime.utcnow()
    product.moderated_by = 'ai'

    mod_log = ProductModerationLog(
        product_id=product.id,
        decision=decision,
        reason=reason,
        raw_model_output=raw_output,
        decided_by='ai',
        created_at=datetime.utcnow()
    )
    db.session.add(mod_log)
    db.session.commit()

    return jsonify({
        'message': 'Product updated and re-moderated successfully.',
        'status': 'success',
        'moderation_status': decision,
        'moderation_reason': reason,
        'product': product.to_dict()
    }), 200
