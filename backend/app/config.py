"""
EcoGreen Configuration Module
Loads application configuration from environment variables.
"""

import os
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(os.path.join(BASE_DIR, '.env'))

class Config:
    """Base Configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'ecogreen_secret_key_2026')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'default_jwt_secret_key_2026')
    
    # Database
    DEFAULT_DB_PATH = os.path.join(BASE_DIR, 'database', 'instance', 'app.db')
    os.makedirs(os.path.dirname(DEFAULT_DB_PATH), exist_ok=True)
    SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI', f"sqlite:///{DEFAULT_DB_PATH}")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Razorpay
    RAZORPAY_KEY_ID = os.environ.get('RAZORPAY_KEY_ID', '')
    RAZORPAY_KEY_SECRET = os.environ.get('RAZORPAY_KEY_SECRET', '')
    RAZORPAY_WEBHOOK_SECRET = os.environ.get('RAZORPAY_WEBHOOK_SECRET', '')
    RAZORPAY_SIMULATE = os.environ.get('RAZORPAY_SIMULATE', 'true').strip().lower() == 'true'

    # Power BI Auth
    POWERBI_USER = os.environ.get('POWERBI_USER', 'admin')
    POWERBI_PASSWORD = os.environ.get('POWERBI_PASSWORD', 'admin123')

    # WhatsApp Notifications
    NOTIFY_MODE = os.environ.get('NOTIFY_MODE', 'simulate').strip().lower()
    PUBLIC_BASE_URL = os.environ.get('PUBLIC_BASE_URL', '').strip()

    # Email Notifications
    EMAIL_NOTIFY_MODE = os.environ.get('EMAIL_NOTIFY_MODE', 'simulate').strip().lower()
    SMTP_SERVER = os.environ.get('SMTP_SERVER', 'smtp-relay.brevo.com').strip()
    SMTP_PORT = int(os.environ.get('SMTP_PORT', '587').strip())
    SMTP_USERNAME = os.environ.get('SMTP_USERNAME', '').strip()
    SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '').strip()
    SENDER_EMAIL = os.environ.get('SENDER_EMAIL', '').strip()

    # Content Moderation (Gemini Vision)
    MODERATION_MODE = os.environ.get('MODERATION_MODE', 'simulate').strip().lower()
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '').strip()
    GEMINI_MODEL = os.environ.get('GEMINI_MODEL', 'gemini-2.5-flash').strip()

    if MODERATION_MODE == 'gemini' and not GEMINI_API_KEY:
        import logging
        logging.warning("MODERATION_MODE is set to 'gemini' but GEMINI_API_KEY is missing. Falling back to 'simulate' mode.")
        MODERATION_MODE = 'simulate'


class DevelopmentConfig(Config):
    """Development Environment Configuration."""
    DEBUG = True


class ProductionConfig(Config):
    """Production Environment Configuration."""
    DEBUG = False


class TestingConfig(Config):
    """Testing Environment Configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
