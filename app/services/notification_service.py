from app import db
from app.models import Notification, User, NotificationType
from datetime import datetime
from flask import url_for, current_app

def create_notification(user_id, message_text, link_url=None, notification_type=NotificationType.GENERAL_INFO):
    """
    Creates and saves a new notification for a user.
    """
    user = User.query.get(user_id)
    if not user:
        current_app.logger.error(f"Attempted to create notification for non-existent user ID: {user_id}")
        return None

    notification = Notification(
        user_id=user_id,
        message_text=message_text,
        link_url=link_url,
        notification_type=notification_type, # Use the passed enum member
        created_at=datetime.utcnow()
    )
    db.session.add(notification)
    try:
        db.session.commit()
        current_app.logger.info(f"Notification ({notification_type.name}) created for User {user_id}: '{message_text[:50]}...'")
        return notification
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating notification for User {user_id}: {e}", exc_info=True)
        return None

def get_unread_notifications_count(user_id):
    """
    Gets the count of unread notifications for a user.
    """
    return Notification.query.filter_by(user_id=user_id, is_read=False).count()

def get_user_notifications(user_id, page=1, per_page=10):
    """
    Gets paginated notifications for a user, unread first, then by date.
    """
    query = Notification.query.filter_by(user_id=user_id)\
                              .order_by(Notification.is_read.asc(), Notification.created_at.desc())

    return query.paginate(page=page, per_page=per_page, error_out=False)


def mark_notification_as_read(notification_id, user_id):
    """
    Marks a specific notification as read for the given user.
    Returns True if successful, False otherwise.
    """
    notification = Notification.query.get(notification_id)
    if notification and notification.user_id == user_id and not notification.is_read:
        notification.is_read = True
        try:
            db.session.commit()
            current_app.logger.info(f"Notification {notification_id} marked as read for User {user_id}.")
            return True
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error marking notification {notification_id} as read: {e}", exc_info=True)
            return False
    elif notification and notification.user_id == user_id and notification.is_read:
        return True # Already read, consider it a success
    return False

def mark_all_notifications_as_read(user_id):
    """Marks all unread notifications for a user as read."""
    try:
        # Ensure we are only updating for the specific user_id
        updated_count = Notification.query.filter_by(user_id=user_id, is_read=False)\
                                        .update({'is_read': True}, synchronize_session='fetch')
        db.session.commit()
        current_app.logger.info(f"{updated_count} notifications marked as read for User {user_id}.")
        return updated_count if updated_count is not None else 0
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error marking all notifications as read for User {user_id}: {e}", exc_info=True)
        return 0


# --- Helper functions to generate specific notifications (called from other parts of the app) ---

def notify_new_ticket_issued(ticket):
    if not ticket or not ticket.issued_to_user_id: return
    message = f"A new ticket (#{ticket.id}) for '{ticket.violation_details[:50]}...' has been issued to you. Fine: {ticket.fine_amount:.2f}."
    link = url_for('dot.view_ticket_detail', ticket_id=ticket.id, _external=False) # Internal link
    create_notification(ticket.issued_to_user_id, message, link, NotificationType.NEW_TICKET_ISSUED)

def notify_permit_approved(permit_application):
    if not permit_application or not permit_application.user_id: return
    message = f"Your permit application (#{permit_application.id}) for '{permit_application.vehicle_type}' has been approved."
    if permit_application.permit_fee and permit_application.permit_fee > 0:
        message += f" A fee of {permit_application.permit_fee:.2f} is due."
    link = url_for('dot.view_permit_application_detail', application_id=permit_application.id, _external=False)
    create_notification(permit_application.user_id, message, link, NotificationType.PERMIT_APP_APPROVED)

def notify_permit_denied(permit_application):
    if not permit_application or not permit_application.user_id: return
    message = f"Your permit application (#{permit_application.id}) for '{permit_application.vehicle_type}' has been denied."
    link = url_for('dot.view_permit_application_detail', application_id=permit_application.id, _external=False)
    create_notification(permit_application.user_id, message, link, NotificationType.PERMIT_APP_DENIED)

def notify_new_message_received(conversation, recipient_user_id, sender_user_id):
    if not conversation or not recipient_user_id or not sender_user_id: return

    sender = User.query.get(sender_user_id)
    sender_name = sender.username if sender else "Someone"

    message_preview = f"You have a new message from {sender_name} regarding: '{conversation.subject[:50]}...'."
    link = url_for('messaging.view_conversation', conversation_id=conversation.id, _external=False)
    create_notification(recipient_user_id, message_preview, link, NotificationType.NEW_MESSAGE_RECEIVED)
