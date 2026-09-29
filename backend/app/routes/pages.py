"""
HTML Page Routes Blueprint.
Serves index marketplace, admin dashboard, and legacy endpoints.
"""

import requests
from requests.auth import HTTPBasicAuth
from flask import Blueprint, render_template

pages_bp = Blueprint('pages_bp', __name__)

consumer_key = '0gc0uEwGcFcoxtHXIySEPF5ek4k8uvhf'
consumer_secret = '6UvaqPmZWjdDlbGj'

@pages_bp.route('/')
def home():
    return render_template('index.html')

@pages_bp.route('/admin/dashboard')
def admin_dashboard():
    return render_template('admin_dashboard.html')

@pages_bp.route('/admin/notifications')
def admin_notifications():
    return render_template('admin_dashboard.html')

@pages_bp.route('/admin/moderation')
def admin_moderation():
    return render_template('admin_dashboard.html')


@pages_bp.route('/access_token')
def token():
    try:
        mpesa_auth_url = 'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'
        res = requests.get(mpesa_auth_url, auth=HTTPBasicAuth(consumer_key, consumer_secret), timeout=5)
        return res.json()
    except Exception as e:
        print("Access token error:", e)
        return {'access_token': ''}
