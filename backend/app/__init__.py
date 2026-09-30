"""
EcoGreen Application Factory Module.
Initializes Flask app, extensions, blueprints, and background jobs.
"""

import os
from flask import Flask, jsonify
from sqlalchemy import text

from backend.app.config import DevelopmentConfig, ProductionConfig, TestingConfig
from backend.app.extensions import db, migrate, jwt
from backend.app.cli.commands import register_cli_commands
from backend.app.services.scheduler import init_scheduler

# Import Blueprints
from backend.app.routes.pages import pages_bp
from backend.app.routes.auth import auth_bp
from backend.app.routes.products import products_bp
from backend.app.routes.orders import orders_bp
from backend.app.routes.payments import payments_bp
from backend.app.routes.notifications import notification_bp
from backend.app.routes.reviews import reviews_bp
from backend.app.routes.search import search_bp
from backend.app.routes.admin_analytics import analytics_bp


CONFIG_MAP = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig
}


def patch_database_schema(app):
    """Auto-patches missing SQLite columns if migrating legacy database files."""
    with app.app_context():
        try:
            db.create_all()
            statements = [
                'ALTER TABLE user ADD COLUMN phone VARCHAR(50)',
                'ALTER TABLE user ADD COLUMN whatsapp_opt_in BOOLEAN DEFAULT 0',
                'ALTER TABLE user ADD COLUMN last_inbound_whatsapp_at DATETIME',
                "ALTER TABLE user ADD COLUMN notification_language VARCHAR(10) DEFAULT 'en'",
                'ALTER TABLE product ADD COLUMN created_at DATETIME',
                'ALTER TABLE "order" ADD COLUMN confirmed_at DATETIME',
                'ALTER TABLE "order" ADD COLUMN cancelled_at DATETIME',
                'ALTER TABLE "order" ADD COLUMN delivered_at DATETIME',
                'ALTER TABLE "transaction" ADD COLUMN user_id INTEGER',
                'ALTER TABLE "transaction" ADD COLUMN payment_method VARCHAR(50)',
                'ALTER TABLE "transaction" ADD COLUMN transaction_date DATETIME',
                "ALTER TABLE \"transaction\" ADD COLUMN currency VARCHAR(10) DEFAULT 'INR'"
            ]
            for stmt in statements:
                try:
                    db.session.execute(text(stmt))
                    db.session.commit()
                except Exception:
                    db.session.rollback()
        except Exception:
            pass


def create_app(config_name=None):
    """
    Application factory for EcoGreen.
    
    :param config_name: String specifying configuration ('development', 'production', 'testing')
    :return: Configured Flask application instance
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    template_dir = os.path.join(base_dir, 'frontend', 'templates')
    static_dir = os.path.join(base_dir, 'frontend', 'static')

    app = Flask(
        __name__,
        template_folder=template_dir,
        static_folder=static_dir
    )

    # Determine configuration
    if not config_name:
        config_name = os.environ.get('FLASK_ENV', 'development').lower()
    
    config_cls = CONFIG_MAP.get(config_name, DevelopmentConfig)
    app.config.from_object(config_cls)

    # Initialize Extensions
    db.init_app(app)
    jwt.init_app(app)

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({
            'status': 'error',
            'error': 'Token has expired',
            'message': 'Token has expired',
            'msg': 'Token has expired',
            'expired': True
        }), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error_string):
        return jsonify({
            'status': 'error',
            'error': 'Invalid authentication token',
            'message': str(error_string) or 'Invalid authentication token',
            'msg': str(error_string) or 'Invalid authentication token',
            'invalid': True
        }), 401

    migrations_dir = os.path.join(base_dir, 'database', 'migrations')
    migrate.init_app(app, db, directory=migrations_dir)

    # Register Blueprints
    app.register_blueprint(pages_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(orders_bp)
    app.register_blueprint(payments_bp)
    app.register_blueprint(notification_bp)
    app.register_blueprint(reviews_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(analytics_bp)

    # Register CLI commands
    register_cli_commands(app)

    # Auto-patch schema for SQLite compatibility
    if not app.config.get('TESTING'):
        patch_database_schema(app)

    # Initialize Background Scheduler (skipped during testing or if disabled)
    if not app.config.get('TESTING') and not os.environ.get('DISABLE_SCHEDULER'):
        init_scheduler(app)

    return app
