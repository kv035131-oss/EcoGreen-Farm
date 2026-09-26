#!/usr/bin/env python3

from flask import Flask
from flask_cors import CORS
from server.models import db, migrate
from server.routes import product_routes
from server.config import Config
from flask_jwt_extended import JWTManager

def seed_data():
    from server.models import Product, User, Reviews
    from werkzeug.security import generate_password_hash

    try:
        if User.query.count() == 0:
            farmer1 = User(username='john_farmer', email='john@farm.com', password=generate_password_hash('pass123'), user_type='farmer', status='Active', phone_number=254712345678)
            consumer1 = User(username='mary_consumer', email='mary@gmail.com', password=generate_password_hash('pass123'), user_type='consumer', status='Active', phone_number=254798765432)
            db.session.add_all([farmer1, consumer1])
            db.session.commit()

        if Product.query.count() == 0:
            p1 = Product(name='Fresh Organic Tomatoes (10kg)', price=15.99, description='Farm fresh vine-ripened organic tomatoes grown without synthetic pesticides.', image='https://images.unsplash.com/photo-1592924357228-91a4daadcfea?w=500', location='Green Valley Farm, Nakuru', quantity=50)
            p2 = Product(name='Organic Crisp Carrots (5kg)', price=8.50, description='Crisp sweet orange carrots harvested daily.', image='https://images.unsplash.com/photo-1598170845058-32b9d6a5da37?w=500', location='Highland Organics, Eldoret', quantity=30)
            p3 = Product(name='Raw Pure Honey (1 Litre)', price=12.00, description='100% pure raw unprocessed wildflower honey direct from hives.', image='https://images.unsplash.com/photo-1587049352846-4a222e784d38?w=500', location='Bee Haven Apiary, Nyeri', quantity=20)
            p4 = Product(name='Farm Fresh Free-Range Eggs (Tray of 30)', price=6.99, description='Pasture raised free-range organic eggs with rich golden yolks.', image='https://images.unsplash.com/photo-1516467508483-a7212febe31a?w=500', location='Sunny Hill Poultry, Naivasha', quantity=40)
            p5 = Product(name='Fresh Organic Spinach (Bunch)', price=3.50, description='Nutrient-rich dark green fresh organic spinach leaves.', image='https://images.unsplash.com/photo-1576045057995-568f588f82fb?w=500', location='Riverside Gardens, Kiambu', quantity=60)
            p6 = Product(name='Premium Hass Avocados (5 Pack)', price=9.99, description='Creamy rich Hass avocados grown naturally in volcanic soil.', image='https://images.unsplash.com/photo-1523049673857-eb18f1d7b578?w=500', location='Mount Kenya Orchards, Meru', quantity=45)
            db.session.add_all([p1, p2, p3, p4, p5, p6])
            db.session.commit()

            r1 = Reviews(product_id=p1.id, user_id=2, comment='Extremely fresh tomatoes! Perfect for salads and cooking.', rating=5)
            r2 = Reviews(product_id=p3.id, user_id=2, comment='Best natural honey I have ever ordered. Highly recommended.', rating=5)
            db.session.add_all([r1, r2])
            db.session.commit()
    except Exception as e:
        db.session.rollback()
        print('Seed error:', e)

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    CORS(app)

    db.init_app(app)
    migrate.init_app(app, db)
    jwt = JWTManager(app)

    with app.app_context():
        db.create_all()
        seed_data()

    app.register_blueprint(product_routes)

    return app
