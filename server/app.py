#!/usr/bin/env python3

import click
from flask import Flask
from flask_cors import CORS
from server.models import db, migrate, User
from server.routes import product_routes
from server.analytics_routes import analytics_bp
from server.config import Config
from flask_jwt_extended import JWTManager

def seed_data():
    from server.models import Product, User, Reviews
    from werkzeug.security import generate_password_hash

    try:
        if not User.query.filter_by(username='admin').first():
            admin_user = User(
                username='admin',
                email='admin@ecogreen.com',
                password=generate_password_hash('admin123'),
                user_type='admin',
                status='Active',
                phone_number='1234567890'
            )
            db.session.add(admin_user)

        if User.query.filter_by(username='john_farmer').first() is None and User.query.count() <= 1:
            farmer1 = User(username='john_farmer', email='john@farm.com', password=generate_password_hash('pass123'), user_type='farmer', status='Active', phone_number=254712345678)
            consumer1 = User(username='mary_consumer', email='mary@gmail.com', password=generate_password_hash('pass123'), user_type='consumer', status='Active', phone_number=254798765432)
            db.session.add_all([farmer1, consumer1])

        db.session.commit()

        if Product.query.count() == 0:
            p1 = Product(user_id=1, name='Fresh Organic Tomatoes (10kg)', price=15.99, description='Farm fresh vine-ripened organic tomatoes grown without synthetic pesticides.', image='https://images.unsplash.com/photo-1592924357228-91a4daadcfea?w=500', location='Green Valley Farm, Nakuru', quantity=50, category='Vegetables')
            p2 = Product(user_id=1, name='Organic Crisp Carrots (5kg)', price=8.50, description='Crisp sweet orange carrots harvested daily.', image='https://images.unsplash.com/photo-1598170845058-32b9d6a5da37?w=500', location='Highland Organics, Eldoret', quantity=30, category='Vegetables')
            p3 = Product(user_id=1, name='Raw Pure Honey (1 Litre)', price=12.00, description='100% pure raw unprocessed wildflower honey direct from hives.', image='https://images.unsplash.com/photo-1587049352846-4a222e784d38?w=500', location='Bee Haven Apiary, Nyeri', quantity=20, category='Dairy & Eggs')
            p4 = Product(user_id=1, name='Farm Fresh Free-Range Eggs (Tray of 30)', price=6.99, description='Pasture raised free-range organic eggs with rich golden yolks.', image='https://images.unsplash.com/photo-1516467508483-a7212febe31a?w=500', location='Sunny Hill Poultry, Naivasha', quantity=40, category='Dairy & Eggs')
            p5 = Product(user_id=1, name='Fresh Organic Spinach (Bunch)', price=3.50, description='Nutrient-rich dark green fresh organic spinach leaves.', image='https://images.unsplash.com/photo-1576045057995-568f588f82fb?w=500', location='Riverside Gardens, Kiambu', quantity=60, category='Vegetables')
            p6 = Product(user_id=1, name='Premium Hass Avocados (5 Pack)', price=9.99, description='Creamy rich Hass avocados grown naturally in volcanic soil.', image='https://images.unsplash.com/photo-1523049673857-eb18f1d7b578?w=500', location='Mount Kenya Orchards, Meru', quantity=45, category='Fruits')
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
    app.register_blueprint(analytics_bp)

    @app.cli.command('create-admin')
    @click.option('--username', default='admin', help='Admin username')
    @click.option('--email', default='admin@ecogreen.com', help='Admin email')
    @click.option('--password', default='admin123', help='Admin password')
    def create_admin_cmd(username, email, password):
        """CLI command to create an admin user for analytics & Power BI."""
        from werkzeug.security import generate_password_hash
        user = User.query.filter((User.username == username) | (User.email == email)).first()
        if user:
            user.user_type = 'admin'
            user.password = generate_password_hash(password)
            db.session.commit()
            click.echo(f"Updated existing user '{username}' to Admin role.")
        else:
            admin_user = User(
                username=username,
                email=email,
                password=generate_password_hash(password),
                user_type='admin',
                status='Active'
            )
            db.session.add(admin_user)
            db.session.commit()
            click.echo(f"Created new Admin user '{username}' ({email}).")

    return app

