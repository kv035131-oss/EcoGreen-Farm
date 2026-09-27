from flask import Blueprint, request, jsonify, make_response, current_app, render_template
from server.models import db, Product, Order, User, Reviews, Search, Transaction
import cloudinary
import cloudinary.uploader
import jwt
import hmac
import hashlib
from sqlalchemy import func
from datetime import datetime, timedelta
from flask_jwt_extended import jwt_required, get_jwt_identity, JWTManager, create_access_token
from werkzeug.security import generate_password_hash, check_password_hash
import requests
import base64
from requests.auth import HTTPBasicAuth
from server.razorpay_service import (
    create_razorpay_order,
    verify_payment_signature,
    verify_webhook_signature
)

product_routes = Blueprint('product_routes', __name__)
consumer_key = '0gc0uEwGcFcoxtHXIySEPF5ek4k8uvhf'
consumer_secret = '6UvaqPmZWjdDlbGj'
my_endpoint = 'https://c001-41-80-116-223.ngrok-free.app' #callback url

@product_routes.route('/')
def home():
    return render_template('index.html')

@product_routes.route('/access_token')
def token():
    data = access_token()
    return data

def access_token():
    try:
        mpesa_auth_url='https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'
        res = requests.get(mpesa_auth_url, auth=HTTPBasicAuth(consumer_key, consumer_secret), timeout=5)
        data = res.json()
        return data.get('access_token', '')
    except Exception as e:
        print("Access token error:", e)
        return ''

def serialize_order(order):
    product = Product.query.get(order.product_id)
    user = User.query.get(order.user_id)
    return {
        'id': order.id,
        'product_id': order.product_id,
        'product_name': product.name if product else f"Produce #{order.product_id}",
        'product_image': product.image if product else 'https://images.unsplash.com/photo-1542838132-92c53300491e?w=500',
        'product_farmer_id': product.user_id if product else None,
        'user_id': order.user_id,
        'user_name': user.username if user else 'Customer',
        'amount': order.amount,
        'phone_number': order.phone_number,
        'status': order.order_status or 'Pending',
        'payment_status': getattr(order, 'payment_status', 'Unpaid') or 'Unpaid',
        'orderDate': order.transaction_date.strftime("%Y-%m-%d %H:%M") if order.transaction_date else datetime.utcnow().strftime("%Y-%m-%d %H:%M")
    }

@product_routes.route('/pay', methods=['POST'])
@jwt_required(optional=True)
def pay_order():
    try:
        data = request.json or {}
        current_user_id = get_jwt_identity()

        order_id = data.get('order_id')
        if order_id:
            order = Order.query.get(order_id)
        else:
            product_id = int(data.get('product_id', 1))
            user_id = int(data.get('user_id', current_user_id or 1))
            amount = float(data.get('amount', 10.0))
            phone_number = str(data.get('phone_number', '254700000000'))
            
            order = Order(
                product_id=product_id,
                user_id=user_id,
                amount=amount,
                phone_number=phone_number,
                order_status='Pending',
                payment_status='Unpaid',
                transaction_date=datetime.utcnow()
            )
            db.session.add(order)
            db.session.commit()

        if not order:
            return jsonify({'error': 'Order not found', 'status': 'error'}), 404

        simulate = current_app.config.get('RAZORPAY_SIMULATE', True)
        key_id = current_app.config.get('RAZORPAY_KEY_ID', 'rzp_test_sample')
        key_secret = current_app.config.get('RAZORPAY_KEY_SECRET', 'sample_secret')

        if simulate or key_id == 'rzp_test_sample' or not key_id or not key_secret:
            simulated_payment_id = f"pay_sim_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{order.id}"
            simulated_order_id = f"order_sim_{order.id}"

            txn = Transaction(
                order_id=order.id,
                razorpay_order_id=simulated_order_id,
                razorpay_payment_id=simulated_payment_id,
                razorpay_signature='simulated_signature',
                amount=order.amount,
                currency='INR',
                status='Success'
            )
            order.payment_status = 'Paid'
            db.session.add(txn)
            db.session.commit()

            return jsonify({
                'simulate': True,
                'status': 'success',
                'message': 'Simulated payment successful. Order marked as Paid.',
                'order_id': order.id,
                'order': serialize_order(order),
                'transaction': txn.to_dict()
            }), 200

        rzp_order = create_razorpay_order(order.amount, order.id)
        razorpay_order_id = rzp_order.get('id')

        txn = Transaction(
            order_id=order.id,
            razorpay_order_id=razorpay_order_id,
            amount=order.amount,
            currency=rzp_order.get('currency', 'INR'),
            status='Created'
        )
        db.session.add(txn)
        db.session.commit()

        return jsonify({
            'simulate': False,
            'status': 'success',
            'order_id': order.id,
            'razorpay_order_id': razorpay_order_id,
            'amount': rzp_order.get('amount'),
            'amount_inr': order.amount,
            'currency': rzp_order.get('currency', 'INR'),
            'key_id': key_id
        }), 200

    except Exception as e:
        db.session.rollback()
        print("Payment error:", e)
        return jsonify({'error': str(e), 'status': 'error'}), 500


@product_routes.route('/api/v1/payments/verify', methods=['POST'])
@jwt_required(optional=True)
def verify_payment():
    try:
        data = request.json or {}
        razorpay_order_id = data.get('razorpay_order_id')
        razorpay_payment_id = data.get('razorpay_payment_id')
        razorpay_signature = data.get('razorpay_signature')

        if not razorpay_order_id or not razorpay_payment_id or not razorpay_signature:
            return jsonify({'error': 'Missing payment verification parameters', 'status': 'error'}), 400

        txn = Transaction.query.filter_by(razorpay_order_id=razorpay_order_id).first()
        if not txn:
            return jsonify({'error': 'Transaction record not found', 'status': 'error'}), 404

        is_valid = verify_payment_signature(razorpay_order_id, razorpay_payment_id, razorpay_signature)

        if is_valid:
            txn.status = 'Success'
            txn.razorpay_payment_id = razorpay_payment_id
            txn.razorpay_signature = razorpay_signature

            order = Order.query.get(txn.order_id)
            if order:
                order.payment_status = 'Paid'

            db.session.commit()
            return jsonify({
                'message': 'Payment verified and order marked as Paid',
                'status': 'success',
                'order_id': txn.order_id,
                'order': serialize_order(order) if order else None
            }), 200
        else:
            txn.status = 'Failed'
            db.session.commit()
            return jsonify({'error': 'Invalid payment signature. Verification failed.', 'status': 'error'}), 400

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e), 'status': 'error'}), 500


@product_routes.route('/api/v1/payments/webhook', methods=['POST'])
def razorpay_webhook():
    try:
        raw_body = request.get_data()
        signature_header = request.headers.get('X-Razorpay-Signature', '')
        webhook_secret = current_app.config.get('RAZORPAY_WEBHOOK_SECRET', '')

        if webhook_secret and webhook_secret != 'sample_webhook_secret':
            expected_sig = hmac.new(
                webhook_secret.encode('utf-8'),
                raw_body,
                hashlib.sha256
            ).hexdigest()

            if not hmac.compare_digest(expected_sig, signature_header):
                print("Razorpay webhook signature mismatch")
                return jsonify({'status': 'error', 'message': 'Invalid signature'}), 400

        payload = request.json or {}
        event = payload.get('event')

        if event in ['payment.captured', 'order.paid']:
            payment_entity = payload.get('payload', {}).get('payment', {}).get('entity', {})
            razorpay_order_id = payment_entity.get('order_id')
            razorpay_payment_id = payment_entity.get('id')

            if razorpay_order_id:
                txn = Transaction.query.filter_by(razorpay_order_id=razorpay_order_id).first()
                if txn:
                    txn.status = 'Success'
                    txn.razorpay_payment_id = razorpay_payment_id
                    order = Order.query.get(txn.order_id)
                    if order:
                        order.payment_status = 'Paid'
                    db.session.commit()

        return jsonify({'status': 'ok'}), 200
    except Exception as e:
        db.session.rollback()
        print("Webhook processing error:", e)
        return jsonify({'status': 'error', 'message': str(e)}), 200

@product_routes.route('/api/v1/products/create', methods=['POST'])
@jwt_required(optional=True)
def create_product():
    try:
        data = request.form if (request.form and len(request.form) > 0) else (request.json or {})
        current_user_id = get_jwt_identity()

        user_id = data.get('user_id')
        if not user_id and current_user_id:
            user_id = int(current_user_id)

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
        return jsonify({'message': 'Product created successfully', 'status': 'success', 'product': product.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e), 'status': 'error'}), 400

@product_routes.route('/api/v1/products', methods=['GET'])
@jwt_required(optional=True)
def view_all_products():
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 50))

    products = Product.query.order_by(Product.id.desc()).paginate(page=page, per_page=per_page, error_out=False)
    
    product_list = []

    for product in products.items:
        avg_rating = db.session.query(func.avg(Reviews.rating)).filter_by(product_id=product.id).scalar()
        comments = Reviews.query.filter_by(product_id=product.id).all()
        comment_list = []

        for comment in comments:
            user = User.query.get(comment.user_id)
            if user:
                comment_list.append({
                    'comment': comment.comment,
                    'user_username': user.username
                })
        
        product_list.append({
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
        })

    return jsonify({
        'status': 'success',
        'data': product_list,
        'pagination': {
            'total': products.total,
            'pages': products.pages,
            'current_page': products.page,
            'per_page': products.per_page
        }
    }), 200


@product_routes.route('/api/v1/products/<int:id>', methods=['GET'])
def view_product(id):
    product = Product.query.get(id)
    
    if not product:
        return jsonify({'message': 'Product not found'}), 404
    
    avg_rating = db.session.query(func.avg(Reviews.rating)).filter_by(product_id=id).scalar()
    comments = Reviews.query.filter_by(product_id=id).all()
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

@product_routes.route('/api/v1/Orders', methods=['GET'])
@jwt_required(optional=True)
def view_all_orders():
    current_user_id = get_jwt_identity()
    if current_user_id:
        return view_my_orders(int(current_user_id))

    return jsonify({'status': 'success', 'data': []})


@product_routes.route('/api/v1/Orders/<int:user_id>', methods=['GET'])
def view_my_orders(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({'status': 'success', 'data': []})

    if user.user_type == 'farmer':
        # Farmers see orders for their farm products + orders placed by themselves
        farmer_product_ids = [p.id for p in Product.query.filter_by(user_id=user_id).all()]
        if farmer_product_ids:
            orders = Order.query.filter(
                (Order.user_id == user_id) | (Order.product_id.in_(farmer_product_ids))
            ).order_by(Order.id.desc()).all()
        else:
            orders = Order.query.filter_by(user_id=user_id).order_by(Order.id.desc()).all()
    else:
        # Consumers only see their own orders
        orders = Order.query.filter_by(user_id=user_id).order_by(Order.id.desc()).all()

    order_list = [serialize_order(o) for o in orders]
    return jsonify({
        'status': 'success',
        'data': order_list
    })

@product_routes.route('/api/v1/Orders/<int:order_id>/status', methods=['PUT', 'POST'])
@jwt_required(optional=True)
def update_order_status(order_id):
    try:
        order = Order.query.get(order_id)
        if not order:
            return jsonify({'error': 'Order not found', 'status': 'error'}), 404

        data = request.json or {}
        new_status = data.get('status', 'Confirmed')

        order.order_status = new_status
        db.session.commit()

        return jsonify({
            'message': f'Order status updated to {new_status}',
            'status': 'success',
            'order': serialize_order(order)
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e), 'status': 'error'}), 400


@product_routes.route('/api/v1/Reviews', methods=['GET'])
def view_all_reviews():
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))

    # Query the products using pagination
    reviews = Reviews.query.paginate(page=page, per_page=per_page, error_out=False)
    review_list= []
    for review in reviews.items:
        review_data= {
                'id': review.id,
                'product_id': review.product_id,
                'user_id': review.user_id,
                'comment': review.comment,
                'rating' : review.rating
            }
        review_list.append(review_data)

    return jsonify({
        'status': 'success',
        'data': review_list,
        'pages': reviews.pages
    })
@product_routes.route('/api/v1/User', methods=['GET'])
def view_all_user():
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))

    # Query the products using pagination
    user = User.query.paginate(page=page, per_page=per_page, error_out=False)
    user_list= []
    for user in user.items:
        user_data= {
                'id': user.id,
                'username': user.username,
                'phone number': user.phone_number,
                'email': user.email,
                'user_type' : user.user_type,
                'status': user.status,
                'password': user.password
            }
        user_list.append(user_data)

    return jsonify({
        'status': 'success',
        'data': user_list
    })


@product_routes.route('/api/v1/User/create', methods=['POST'])
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

@product_routes.route('/api/v1/Orders/create', methods=['POST'])
@jwt_required(optional=True)
def create_order():
    try:
        data = request.json or {}

        user_id = int(data.get('user_id', 1))
        product_id = int(data.get('product_id', 1))
        amount = float(data.get('amount', 10.0))
        phone_number = str(data.get('phone_number', '254700000000'))
        status = data.get('status', 'Pending')

        order = Order(
            product_id=product_id,
            user_id=user_id,
            amount=amount,
            mpesa_receipt_number=data.get('mpesa_receipt_number', f"MP-{datetime.now().strftime('%M%S%f')[:8]}"),
            merchant_request_id=data.get('merchant_request_id', 'REQ-001'),
            checkout_request_id=data.get('checkout_request_id', 'CHK-001'),
            result_code=0,
            result_desc='Payment Initiated',
            order_status=status,
            phone_number=phone_number,
            transaction_date=datetime.utcnow()
        )
        db.session.add(order)
        db.session.commit()
        return jsonify({
            'message': 'Order created successfully',
            'status': 'success',
            'order_id': order.id,
            'order': serialize_order(order)
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e), 'status': 'error'}), 400

@product_routes.route('/api/v1/Reviews/create', methods=['POST'])
def create_review():
    data = request.json

    review =Reviews(
        product_id=data['product_id'],
        user_id=data['user_id'],
        comment=data['comment'],                      
        rating=data['rating']                     
          )
    db.session.add(review)
    db.session.commit()
    return jsonify({'message': 'Reviews have been greatly appreciated'}), 201



@product_routes.route('/api/v1/Search', methods=['POST'])
def search():
    data = request.json
    user_id = data.get('user_id')
    keyword = data.get('keyword')
    
    if not user_id or not keyword:
        return jsonify({'error': 'Invalid request data'}), 400

    try:
        # Create a new Search record in the database
        search = Search(user_id=user_id, keyword=keyword)
        db.session.add(search)
        db.session.commit()
        
        products = Product.query.filter(Product.name.ilike(f'%{keyword}%')).all()
        product_list = []
        for product in products:
            product_data = {
                'id': product.id,
                'name': product.name,
                'price': product.price,
                'description': product.description,
                'image': product.image,
                'location': product.location,
                'quantity': product.quantity
            }
            product_list.append(product_data)

        return jsonify({
            'status': 'success',
            'data': product_list
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@product_routes.route('/api/v1/Login', methods=['POST'])
def login():
    data = request.json or {}
    username = data.get("username")
    password = data.get("password")
    user = User.query.filter_by(username=username).first()
    if user and check_password_hash(user.password, password):
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

@product_routes.route('/api/v1/user/profile', methods=['GET'])
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


def generate_token(user):
    return create_access_token(identity=str(user.id), additional_claims={
        'user_id': user.id,
        'username': user.username,
        'email': user.email,
        'user_type': user.user_type
    })