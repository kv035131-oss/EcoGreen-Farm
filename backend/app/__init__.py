"""
EcoGreen Application Factory Module.
Initializes Flask app, extensions, blueprints, and background jobs.
"""

import os
from flask import Flask

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

    # Initialize Background Scheduler (skipped during testing or if disabled)
    if not app.config.get('TESTING') and not os.environ.get('DISABLE_SCHEDULER'):
        init_scheduler(app)

    return app
