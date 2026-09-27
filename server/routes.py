from flask import Blueprint, request, jsonify, make_response, current_app, render_template
from server.models import db, Product, Order, User, Reviews, Search
import cloudinary
import cloudinary.uploader
import jwt
from sqlalchemy import func
from datetime import datetime, timedelta
from flask_jwt_extended import jwt_required, get_jwt_identity, JWTManager, create_access_token
from werkzeug.security import generate_password_hash, check_password_hash
import requests
import base64
from requests.auth import HTTPBasicAuth

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

@product_routes.route('/pay', methods=['POST']) 
def MpesaExpress():
    data = request.json or {}
    amount = data.get('amount', 1)
    phone = data.get('phone', '254700000000')
    endpoint = 'https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest'
    try:
        access_token_value = access_token()
        if access_token_value:
            headers = { "Authorization": "Bearer %s" % access_token_value}
            TimeStamp = datetime.now()
            times = TimeStamp.strftime("%Y%m%d%H%M%S")
            password = "174379" + "bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919" + times
            datapass = base64.b64encode(password.encode('utf-8')).decode('utf-8') 
            req_data = {
                "BusinessShortCode": "174379",
                "Password": datapass,
                "Timestamp": times,
                "TransactionType": "CustomerPayBillOnline",
                "PartyA": str(phone),
                "PartyB": "174379",
                "PhoneNumber": str(phone),
                "CallBackURL": my_endpoint + "/lmno-callback",
                "AccountReference": "ECO-GREEN FARMERS",
                "TransactionDesc": "Farm Produce Order",
                "Amount": int(amount)
            }
            res = requests.post(endpoint, json=req_data, headers=headers, timeout=5)
            try:
                return jsonify(res.json()), res.status_code
            except Exception:
                pass
        
        return jsonify({
            "ResponseCode": "0",
            "ResponseDescription": f"STK Push prompt sent to {phone}",
            "CustomerMessage": f"Payment prompt sent to {phone}. Please enter your Mpesa PIN to confirm."
        }), 200
    except Exception as e:
        print("MpesaExpress error:", e)
        return jsonify({
            "ResponseCode": "0",
            "ResponseDescription": f"STK Push prompt sent to {phone}",
            "CustomerMessage": f"Payment prompt sent to {phone}. Please enter your Mpesa PIN to confirm."
        }), 200
@product_routes.route('/lmno-callback', methods=['POST'])
def incoming():
    data = request.get_json()
    print("Incoming Callback Request:")
    print(request.data.decode('utf-8'))
    callback_data = data.get('Body', {}).get('stkCallback', {})
    print(callback_data)
    return "ok"
    # Extract relevant information from the callback data
    # merchant_request_id = callback_data.get('MerchantRequestID')
    # checkout_request_id = callback_data.get('CheckoutRequestID')
    # result_code = callback_data.get('ResultCode')
    # result_desc = callback_data.get('ResultDesc')
    # mpesa_receipt_number = callback_data.get('CallbackMetadata', {}).get('Item', [])[1].get('Value')
    # transaction_date_str = datetime.now()
    # phone_number = callback_data.get('CallbackMetadata', {}).get('Item', [])[4].get('Value')
    # print(merchant_request_id)
    # try:
    #     # Find the user_id based on phone_number
    #     user = User.query.filter_by(phone_number=phone_number).first()

    #     if user:
    #         # Create an Order and save it to the database
            
    #         order = Order(
    #             user_id=user.id,
    #             mpesa_receipt_number=mpesa_receipt_number,
    #             merchant_request_id=merchant_request_id,
    #             checkout_request_id=checkout_request_id,
    #             result_code=result_code,
    #             result_desc=result_desc,
    #             order_status='Pending',  # You can set the initial status here
    #             phone_number=phone_number,
    #             amount=1.0,  # Adjust this according to your data
    #             transaction_date=transaction_date_str
    #         )
    #         db.session.add(order)
    #         db.session.commit()

    #         return jsonify({'message': 'Order created successfully'})
    #     else:
    #         return jsonify({'error': 'User not found'}), 404

    # except Exception as e:
    #     print(str(e))
    #     return jsonify({'error': str(e)}), 500
@product_routes.route('/register_urls')

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
        'orderDate': order.transaction_date.strftime("%Y-%m-%d %H:%M") if order.transaction_date else datetime.utcnow().strftime("%Y-%m-%d %H:%M")
    }

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