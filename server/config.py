import os
from dotenv import load_dotenv
import cloudinary

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'ecogreen_secret_key_2026')
    SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI', 'sqlite:///app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    cloudinary.config(
        cloud_name=os.environ.get('CLOUDINARY_CLOUD_NAME', 'dlgspxpwr'),
        api_key=os.environ.get('CLOUDINARY_API_KEY', '162229873424843'),
        api_secret=os.environ.get('CLOUDINARY_API_SECRET', 'PK64yfEbGdYzy7syywRCAhLOYGc')
    )

    JWT_TOKEN_LOCATION = ['headers']
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'VDpbyCMPTKsrvSEm1Dlp11FCEPx2rpIa3jlqLGi70zY')
    JWT_HEADER_NAME = 'Authorization'
    JWT_HEADER_TYPE = "Bearer"

    # Razorpay Credentials
    RAZORPAY_KEY_ID = os.environ.get('RAZORPAY_KEY_ID', 'rzp_test_sample')
    RAZORPAY_KEY_SECRET = os.environ.get('RAZORPAY_KEY_SECRET', 'sample_secret')
    RAZORPAY_WEBHOOK_SECRET = os.environ.get('RAZORPAY_WEBHOOK_SECRET', 'sample_webhook_secret')
    RAZORPAY_SIMULATE = os.environ.get('RAZORPAY_SIMULATE', 'true').lower() in ['true', '1', 'yes']