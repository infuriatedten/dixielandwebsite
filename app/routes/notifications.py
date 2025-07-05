from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import current_user, login_required
from app import db
from app.models import Notification, User # Added User for messaging service context
from app.services import notification_service, messaging_service # Import your services

notifications_bp = Blueprint('notifications', __name__)

@notifications_bp.route('/')
@login_required
def list_notifications():
    page = request.args.get('page', 1, type=int)
    # The service already sorts by is_read.asc(), created_at.desc()
    notifications_pagination = notification_service.get_user_notifications(current_user.id, page=page, per_page=15)

    return render_template('notifications/list_notifications.html',
                           title='My Notifications',
                           notifications_pagination=notifications_pagination)

@notifications_bp.route('/mark_read/<int:notification_id>', methods=['POST'])
@login_required
def mark_notification_read_route(notification_id): # Renamed to avoid conflict with service
    success = notification_service.mark_notification_as_read(notification_id, current_user.id)
    # No flash message here to keep UI cleaner, link click implies action.
    # Or, flash only on error if desired.
    # if not success:
    #     flash('Could not mark notification as read or you are not authorized.', 'warning')

    # Redirect to the notification's link_url if it exists and is safe, otherwise back to list
    notification = Notification.query.get(notification_id)
    if success and notification and notification.link_url:
        # Basic safety check for local URLs, expand if external links are possible and need validation
        if notification.link_url.startswith('/') or notification.link_url.startswith(request.host_url):
             return redirect(notification.link_url)
    return redirect(request.referrer or url_for('notifications.list_notifications'))


@notifications_bp.route('/mark_all_read', methods=['POST'])
@login_required
def mark_all_notifications_read_route(): # Renamed
    count = notification_service.mark_all_notifications_as_read(current_user.id)
    if count > 0:
        flash(f'{count} notification(s) marked as read.', 'success')
    else:
        flash('No new notifications to mark as read.', 'info')
    return redirect(url_for('notifications.list_notifications'))


# Context processor to make unread counts available to base template
# This should ideally be in the main app factory or a shared utility if used by multiple blueprints' templates
# For now, keeping it here for this blueprint's context.
@notifications_bp.app_context_processor
def inject_notification_unread_count():
    if current_user.is_authenticated:
        unread_count = notification_service.get_unread_notifications_count(current_user.id)
        return dict(unread_notification_count=unread_count)
    return dict(unread_notification_count=0)

# It's better to have separate context processors or a single one in __init__.py
# This one is for messaging, should be in messaging_bp or __init__.py
# The inject_message_unread_count function was removed from here.
# It will be added to app/routes/messaging.py as a context processor for messaging_bp.

# To make both available, they should be registered with the app or their respective blueprints.
# For now, I'll assume the base.html will get unread_notification_count.
# The unread_message_count will be handled in messaging_bp or a global context processor.
