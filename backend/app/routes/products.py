"""
Product Management Routes Blueprint with Automated Content Moderation.
"""

from functools import wraps
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
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

def get_optional_jwt_identity():
    try:
        verify_jwt_in_request(optional=True)
        return get_jwt_identity()
    except Exception:
        return None

@products_bp.route('/api/v1/products/create', methods=['POST'])
def create_product():
    try:
        data = request.form if (request.form and len(request.form) > 0) else (request.json or {})
        current_user_id = get_optional_jwt_identity()

        user_id_raw = data.get('user_id')
        user_id = None
        if user_id_raw and str(user_id_raw).strip() not in ('', 'null', 'undefined'):
            try:
                user_id = int(user_id_raw)
            except (ValueError, TypeError):
                user_id = None

        if not user_id and current_user_id:
            try:
                user_id = int(current_user_id)
            except (ValueError, TypeError):
                user_id = None

        if user_id:
            user = User.query.get(user_id)
            if user and user.user_type == 'admin':
                return jsonify({'error': 'Admins are not allowed to create products.', 'status': 'error'}), 403

            # Security / Abuse Prevention: Rate limit max 20 listings per farmer per hour
            one_hour_ago = datetime.utcnow() - timedelta(hours=1)
            recent_listings_count = Product.query.filter(
                Product.user_id == user_id,
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

        name = data.get('name', 'Fresh Produce').strip() or 'Fresh Produce'

        price_raw = data.get('price')
        try:
            price = float(price_raw) if (price_raw is not None and str(price_raw).strip() != '') else 10.0
        except (ValueError, TypeError):
            price = 10.0

        quantity_raw = data.get('quantity')
        try:
            quantity = int(quantity_raw) if (quantity_raw is not None and str(quantity_raw).strip() != '') else 1
        except (ValueError, TypeError):
            quantity = 1

        address_text = (data.get('address_text') or data.get('location') or 'Local Farm').strip()
        location = address_text
        
        latitude_raw = data.get('latitude')
        longitude_raw = data.get('longitude')
        try:
            latitude = float(latitude_raw) if (latitude_raw is not None and str(latitude_raw).strip() != '') else None
            longitude = float(longitude_raw) if (longitude_raw is not None and str(longitude_raw).strip() != '') else None
        except (ValueError, TypeError):
            latitude, longitude = None, None

        district = (data.get('district') or '').strip() or None
        state = (data.get('state') or '').strip() or None
        description = (data.get('description') or 'Fresh farm produce.').strip()
        category = (data.get('category') or 'Vegetables').strip()

        # STEP 1: RUN SYNCHRONOUS CONTENT MODERATION ENGINE BEFORE CREATING PRODUCT ROW
        mod_input = image_file if image_file else image_url
        mod_result = moderate_product_image(mod_input, category, name)

        decision = mod_result.get('decision', 'needs_review')
        reason = mod_result.get('reason', '')
        raw_output = mod_result.get('raw_model_output', '')

        # STEP 1.5: IF SERVICE UNAVAILABLE (503) -> DO NOT SILENTLY APPROVE OR SAVE ROW
        if decision == 'unavailable':
            return jsonify({
                'error': 'moderation_unavailable',
                'message': "We couldn't verify your image right now. Please try again."
            }), 503

        # STEP 2: IF REJECTED -> DO NOT CREATE PRODUCT ROW! WRITE LOG & RETURN HTTP 422
        if decision == 'rejected':
            mod_log = ProductModerationLog(
                product_id=None,
                user_id=int(user_id) if user_id else None,
                decision='rejected',
                reason=reason,
                raw_model_output=raw_output,
                decided_by='ai',
                created_at=datetime.utcnow()
            )
            db.session.add(mod_log)

            if user_id:
                seven_days_ago = datetime.utcnow() - timedelta(days=7)
                farmer_rejected_count = db.session.query(ProductModerationLog).filter(
                    ProductModerationLog.user_id == int(user_id),
                    ProductModerationLog.decision == 'rejected',
                    ProductModerationLog.created_at >= seven_days_ago
                ).count()

                if farmer_rejected_count >= 3:
                    farmer = User.query.get(int(user_id))
                    if farmer:
                        farmer.flagged = True
                        farmer.flag_note = f"Flagged automatically: {farmer_rejected_count} rejected product submissions within 7 days (Last: '{name}')."

            db.session.commit()

            return jsonify({
                'error': 'moderation_failed',
                'status': 'rejected',
                'moderation_status': 'rejected',
                'reason': reason,
                'detected_content': mod_result.get('detected_content', ''),
                'matches_declared_name': mod_result.get('matches_declared_name', False),
                'matches_declared_category': mod_result.get('matches_declared_category', False),
                'is_prohibited_or_unrelated': mod_result.get('is_prohibited_or_unrelated', False)
            }), 422

        # STEP 3: IF APPROVED OR NEEDS_REVIEW -> SAVE PRODUCT RECORD TO DATABASE
        product = Product(
            user_id=int(user_id) if user_id else None,
            name=name,
            price=price,
            description=description,
            image=image_url,
            location=location,
            address_text=address_text,
            latitude=latitude,
            longitude=longitude,
            district=district,
            state=state,
            quantity=quantity,
            category=category,
            moderation_status=decision,
            moderation_reason=reason,
            moderated_at=datetime.utcnow(),
            moderated_by='ai',
            created_at=datetime.utcnow()
        )
        db.session.add(product)
        db.session.flush()

        mod_log = ProductModerationLog(
            product_id=product.id,
            user_id=product.user_id,
            decision=decision,
            reason=reason,
            raw_model_output=raw_output,
            decided_by='ai',
            created_at=datetime.utcnow()
        )
        db.session.add(mod_log)
        db.session.commit()

        # Step 4: Low stock notification if applicable
        if product.quantity < 10 and product.user_id:
            farmer = User.query.get(product.user_id)
            if farmer:
                notify(farmer, 'low_stock_farmer', product_name=product.name, quantity=product.quantity)

        status_code = 201 if decision == 'approved' else 202
        msg = "Product created and approved successfully!" if decision == 'approved' else "Your listing is pending admin review."

        return jsonify({
            'message': msg,
            'status': 'success' if decision == 'approved' else 'needs_review',
            'moderation_status': decision,
            'moderation_reason': reason,
            'product': product.to_dict()
        }), status_code

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e), 'status': 'error'}), 400


@products_bp.route('/api/v1/products', methods=['GET'])
def view_all_products():
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 50))
    category = request.args.get('category')

    query = Product.query.filter(Product.moderation_status == 'approved', Product.is_deleted.is_(False))
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
def view_farmer_products():
    current_user_id = get_optional_jwt_identity()
    user_id = request.args.get('user_id') or current_user_id

    if not user_id:
        return jsonify({'error': 'User ID required', 'status': 'error'}), 400

    products = Product.query.filter(Product.user_id == int(user_id), Product.is_deleted.is_(False)).order_by(Product.id.desc()).all()
    product_list = [product.to_dict() for product in products]

    return jsonify({
        'status': 'success',
        'data': product_list
    }), 200


@products_bp.route('/api/v1/products/<int:id>', methods=['GET'])
def view_product(id):
    product = Product.query.get(id)
    if not product or product.is_deleted:
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


@products_bp.route('/api/v1/products/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_product(id):
    current_user_id = get_jwt_identity()
    product = Product.query.get(id)
    if not product or product.is_deleted:
        return jsonify({'error': 'Product not found', 'status': 'error'}), 404

    try:
        user_id_int = int(current_user_id)
    except (TypeError, ValueError):
        user_id_int = None

    user = User.query.get(user_id_int) if user_id_int else None
    if not user:
        return jsonify({'error': 'User not found', 'status': 'error'}), 401

    if product.user_id != user.id and user.user_type != 'admin':
        return jsonify({'error': 'Permission denied. You can only delete your own products.', 'status': 'error'}), 403

    from backend.app.models.order import Order
    order_count = Order.query.filter_by(product_id=id).count()

    if order_count > 0:
        product.is_deleted = True
        product.deleted_at = datetime.utcnow()
        db.session.commit()
        return jsonify({
            'status': 'success',
            'message': f"Product '{product.name}' archived (soft-deleted) as it has existing orders.",
            'deletion_type': 'soft'
        }), 200
    else:
        prod_name = product.name
        ProductModerationLog.query.filter_by(product_id=id).delete()
        Reviews.query.filter_by(product_id=id).delete()
        db.session.delete(product)
        db.session.commit()
        return jsonify({
            'status': 'success',
            'message': f"Product '{prod_name}' permanently deleted.",
            'deletion_type': 'hard'
        }), 200



@products_bp.route('/api/v1/products/<int:id>', methods=['PUT', 'POST'])
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
