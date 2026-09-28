"""
EcoGreen WhatsApp & In-App Notification Blueprint
Routes:
- POST /api/v1/notifications/whatsapp/webhook (Inbound Webhook Stub)
- POST /api/v1/notifications/opt-in (User Opt-in & Preferences)
- GET  /api/v1/notifications (User In-App Notifications)
- POST /api/v1/notifications/<id>/read & /read-all (Mark notifications read)
- POST /api/v1/notifications/test (Send test WhatsApp message)
- GET  /api/v1/admin/notifications/logs & /stats (Admin Analytics Hub)
"""

import os
import logging
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func

from server.models import db, User, Order, Product, NotificationLog, Notification
from server.notification_service import normalize_phone, notify, get_active_provider

logger = logging.getLogger('ecogreen.notification_routes')
notification_bp = Blueprint('notification_bp', __name__)

# =========================================================================
# 1. INBOUND WHATSAPP WEBHOOK (STUB FOR META CLOUD API)
# =========================================================================

@notification_bp.route('/api/v1/notifications/whatsapp/webhook', methods=['GET', 'POST'])
def whatsapp_webhook():
    """Stub endpoint for incoming WhatsApp webhooks (Meta Cloud API ready)."""
    return jsonify({'status': 'ok'}), 200



# =========================================================================
# 2. USER OPT-IN & PREFERENCES API
# =========================================================================

@notification_bp.route('/api/v1/notifications/opt-in', methods=['POST'])
@jwt_required(optional=True)
def update_notification_opt_in():
    try:
        data = request.json or {}
        current_user_id = get_jwt_identity()

        user_id = data.get('user_id') or current_user_id
        if not user_id:
            return jsonify({'error': 'Authentication or user_id required', 'status': 'error'}), 401

        user = User.query.get(int(user_id))
        if not user:
            return jsonify({'error': 'User not found', 'status': 'error'}), 404

        phone_raw = data.get('phone') or data.get('phone_number') or user.phone or user.phone_number
        normalized = normalize_phone(phone_raw)
        
        if data.get('whatsapp_opt_in', True) and not normalized:
            return jsonify({'error': 'Invalid phone number format. Please provide a valid 10-digit number.', 'status': 'error'}), 400

        user.phone = normalized or phone_raw
        user.phone_number = normalized or phone_raw
        user.whatsapp_opt_in = bool(data.get('whatsapp_opt_in', True))
        user.notification_language = data.get('language') or data.get('notification_language') or 'en'

        notify_mode = os.environ.get('NOTIFY_MODE', 'simulate').strip().lower()
        instruction = "Send 'hi' to the EcoGreen WhatsApp number to activate messages."

        db.session.commit()

        # Send Welcome Notification if opting in
        if user.whatsapp_opt_in:
            notify(user, 'welcome_opt_in', join_instruction=instruction)

        return jsonify({
            'status': 'success',
            'message': 'WhatsApp notification preferences updated.',
            'user': user.to_dict(),
            'sandbox_instruction': instruction,
            'notify_mode': notify_mode
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e), 'status': 'error'}), 500


# =========================================================================
# 3. IN-APP NOTIFICATIONS API
# =========================================================================

@notification_bp.route('/api/v1/notifications', methods=['GET'])
@jwt_required(optional=True)
def get_in_app_notifications():
    try:
        current_user_id = get_jwt_identity()
        user_id = request.args.get('user_id') or current_user_id

        if not user_id:
            return jsonify({'status': 'success', 'data': [], 'unread_count': 0})

        notifications = Notification.query.filter_by(user_id=int(user_id)).order_by(Notification.id.desc()).limit(50).all()
        unread_count = Notification.query.filter_by(user_id=int(user_id), is_read=False).count()

        return jsonify({
            'status': 'success',
            'data': [n.to_dict() for n in notifications],
            'unread_count': unread_count
        }), 200
    except Exception as e:
        return jsonify({'error': str(e), 'status': 'error'}), 500


@notification_bp.route('/api/v1/notifications/<int:notification_id>/read', methods=['POST', 'PUT'])
@jwt_required(optional=True)
def mark_notification_read(notification_id):
    try:
        n = Notification.query.get(notification_id)
        if n:
            n.is_read = True
            db.session.commit()
        return jsonify({'status': 'success', 'message': 'Notification marked as read'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e), 'status': 'error'}), 500


@notification_bp.route('/api/v1/notifications/read-all', methods=['POST', 'PUT'])
@jwt_required(optional=True)
def mark_all_notifications_read():
    try:
        current_user_id = get_jwt_identity()
        data = request.json or {}
        user_id = data.get('user_id') or current_user_id

        if user_id:
            Notification.query.filter_by(user_id=int(user_id), is_read=False).update({Notification.is_read: True})
            db.session.commit()

        return jsonify({'status': 'success', 'message': 'All notifications marked as read'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e), 'status': 'error'}), 500


# =========================================================================
# 4. TEST WHATSAPP MESSAGE API
# =========================================================================

@notification_bp.route('/api/v1/notifications/test', methods=['POST'])
@jwt_required(optional=True)
def send_test_notification():
    try:
        data = request.json or {}
        current_user_id = get_jwt_identity()

        user_id = data.get('user_id') or current_user_id
        if not user_id:
            return jsonify({'error': 'Authentication or user_id required', 'status': 'error'}), 401

        user = User.query.get(int(user_id))
        if not user:
            return jsonify({'error': 'User not found', 'status': 'error'}), 404

        # Force opt-in for test if phone exists
        phone_input = data.get('phone') or user.effective_phone
        normalized = normalize_phone(phone_input)
        
        if not normalized:
            return jsonify({'error': 'Valid phone number is required to send test message.', 'status': 'error'}), 400

        user.phone = normalized
        user.whatsapp_opt_in = True
        db.session.commit()

        notify(user, 'test_message')

        notify_mode = os.environ.get('NOTIFY_MODE', 'simulate').strip().lower()
        return jsonify({
            'status': 'success',
            'message': f'Test WhatsApp notification dispatched to {normalized}!',
            'notify_mode': notify_mode
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e), 'status': 'error'}), 500


# =========================================================================
# 5. ADMIN NOTIFICATION LOGS & STATS HUB
# =========================================================================

@notification_bp.route('/api/v1/admin/notifications/logs', methods=['GET'])
@jwt_required(optional=True)
def get_admin_notification_logs():
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))
        status_filter = request.args.get('status')
        event_filter = request.args.get('event_type')

        query = NotificationLog.query

        if status_filter:
            query = query.filter_by(status=status_filter)
        if event_filter:
            query = query.filter_by(event_type=event_filter)

        logs_page = query.order_by(NotificationLog.id.desc()).paginate(page=page, per_page=per_page, error_out=False)

        return jsonify({
            'status': 'success',
            'data': [l.to_dict() for l in logs_page.items],
            'pagination': {
                'total': logs_page.total,
                'pages': logs_page.pages,
                'current_page': logs_page.page,
                'per_page': logs_page.per_page
            }
        }), 200
    except Exception as e:
        return jsonify({'error': str(e), 'status': 'error'}), 500


@notification_bp.route('/api/v1/admin/notifications/stats', methods=['GET'])
@jwt_required(optional=True)
def get_admin_notification_stats():
    try:
        total_count = NotificationLog.query.count()
        sent_count = NotificationLog.query.filter_by(status='sent').count()
        failed_count = NotificationLog.query.filter_by(status='failed').count()
        simulated_count = NotificationLog.query.filter_by(status='simulated').count()
        received_count = NotificationLog.query.filter_by(status='received').count()

        delivered_total = sent_count + simulated_count
        attempts = delivered_total + failed_count
        success_rate = round((delivered_total / attempts) * 100, 1) if attempts > 0 else 100.0

        # Daily notification trend (last 7 days)
        today = datetime.utcnow().date()
        daily_chart = []
        for i in range(6, -1, -1):
            day_date = today - timedelta(days=i)
            day_str = day_date.strftime("%Y-%m-%d")
            
            day_start = datetime.combine(day_date, datetime.min.time())
            day_end = datetime.combine(day_date, datetime.max.time())
            
            cnt = NotificationLog.query.filter(
                NotificationLog.created_at >= day_start,
                NotificationLog.created_at <= day_end
            ).count()

            daily_chart.append({'date': day_str, 'count': cnt})

        return jsonify({
            'status': 'success',
            'stats': {
                'total': total_count,
                'sent': sent_count,
                'failed': failed_count,
                'simulated': simulated_count,
                'received': received_count,
                'success_rate': success_rate
            },
            'daily_chart': daily_chart
        }), 200

    except Exception as e:
        return jsonify({'error': str(e), 'status': 'error'}), 500


@notification_bp.route('/api/v1/admin/notifications/test-email', methods=['POST'])
@jwt_required(optional=True)
def admin_send_test_email():
    """Admin endpoint to test real Brevo SMTP email delivery and view detailed SMTP error codes."""
    from server.email_service import get_active_email_provider, build_html_email
    try:
        data = request.json or {}
        target_email = data.get('email')

        if not target_email:
            ajay = User.query.filter((User.username == 'ajay') | (User.username.ilike('%ajay%'))).first()
            if ajay and ajay.email:
                target_email = ajay.email
            else:
                target_email = os.environ.get('SENDER_EMAIL') or os.environ.get('SMTP_USERNAME')

        if not target_email:
            return jsonify({'status': 'error', 'error': 'No target recipient email specified.'}), 400

        subject = "🧪 EcoGreen Brevo SMTP Test Email"
        body_text = f"Hello! This is an automated test email sent from EcoGreen to {target_email} using Brevo SMTP relay."
        body_html = build_html_email(subject, body_text, target_email.split('@')[0])

        provider = get_active_email_provider()
        status, msg_id, error_text = provider.send(target_email, subject, body_text, body_html)

        # Log entry in NotificationLog
        log_entry = NotificationLog(
            user_id=None,
            channel='email',
            event_type='test_message',
            message=body_text,
            status=status,
            provider_message_id=msg_id,
            error=error_text
        )
        db.session.add(log_entry)
        db.session.commit()

        if status in ('sent', 'simulated'):
            return jsonify({
                'status': 'success',
                'message': f"Test email sent successfully to {target_email}!",
                'msg_id': msg_id,
                'provider_status': status,
                'log_id': log_entry.id
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'error': error_text,
                'provider_status': 'failed',
                'log_id': log_entry.id
            }), 400

    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'error': f"Internal Server Error: {str(e)}"}), 500

