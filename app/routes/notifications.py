from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import current_user, login_required
from app import db
from app.models import Notification
from app.services import notification_service

notifications_bp = Blueprint('notifications', __name__)

@notifications_bp.route('/')
@login_required
def list_notifications():
    page = request.args.get('page', 1, type=int)
    notifications_pagination = notification_service.get_user_notifications(
        current_user.id, page=page, per_page=15
    )
    return render_template(
        'notifications/list_notifications.html',
        title='My Notifications',
        notifications_pagination=notifications_pagination
    )

@notifications_bp.route('/mark_read/<int:notification_id>', methods=['POST'])
@login_required
def mark_notification_read_route(notification_id):
    success = notification_service.mark_notification_as_read(notification_id, current_user.id)

    notification = Notification.query.get(notification_id)
    if success and notification and notification.link_url:
        if notification.link_url.startswith('/') or notification.link_url.startswith(request.host_url):
            return redirect(notification.link_url)
    return redirect(request.referrer or url_for('notifications.list_notifications'))

@notifications_bp.route('/mark_all_read', methods=['POST'])
@login_required
def mark_all_notifications_read_route():
    count = notification_service.mark_all_notifications_as_read(current_user.id)
    if count > 0:
        flash(f'{count} notification(s) marked as read.', 'success')
    else:
        flash('No new notifications to mark as read.', 'info')
    return redirect(url_for('notifications.list_notifications'))

# Context processor to inject unread notification count for templates
@notifications_bp.app_context_processor
def inject_notification_unread_count():
    if current_user.is_authenticated:
        unread_count = notification_service.get_unread_notifications_count(current_user.id)
        return dict(unread_notification_count=unread_count)
    return dict(unread_notification_count=0)
