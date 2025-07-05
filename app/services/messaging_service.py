from app import db
from app.models import Conversation, Message, User, UserRole, ConversationStatus
from datetime import datetime
from flask_login import current_user
from flask import current_app # For logger

def create_conversation(admin_id, target_user_id, subject, initial_message_body):
    """
    Creates a new conversation and the first message.
    Called by an admin initiating a conversation with a user.
    """
    if not subject or len(subject.strip()) == 0:
        subject = f"Message from Admin regarding User ID {target_user_id}"

    target_user = User.query.get(target_user_id)
    admin_user = User.query.get(admin_id)

    if not target_user or not admin_user or admin_user.role != UserRole.ADMIN:
        current_app.logger.error("Failed to create conversation: Invalid admin or target user.")
        return None

    conversation = Conversation(
        user_id=target_user_id,
        admin_id=admin_id,
        subject=subject,
        last_message_time=datetime.utcnow(),
        user_has_unread=True,
        admin_has_unread=False,
        status=ConversationStatus.OPEN
    )
    db.session.add(conversation)

    try:
        db.session.flush()
        first_message = Message(
            conversation_id=conversation.id,
            sender_id=admin_id,
            body=initial_message_body,
            timestamp=conversation.last_message_time
        )
        db.session.add(first_message)
        db.session.commit()
        current_app.logger.info(f"Conversation {conversation.id} created by Admin {admin_id} for User {target_user_id}.")
        return conversation
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating conversation: {e}", exc_info=True)
        return None


def reply_to_conversation(conversation_id, sender_id, body):
    """
    Adds a new message to an existing conversation.
    Updates last_message_time and unread flags.
    """
    conversation = Conversation.query.get(conversation_id)
    if not conversation:
        current_app.logger.warning(f"Reply attempt to non-existent conversation ID: {conversation_id}")
        return None

    if conversation.status != ConversationStatus.OPEN:
        current_app.logger.warning(f"Reply attempt to closed conversation ID: {conversation_id}")
        return None # Or raise an error / return a specific status

    sender = User.query.get(sender_id)
    if not sender:
        current_app.logger.error(f"Reply attempt by non-existent sender ID: {sender_id}")
        return None

    message = Message(
        conversation_id=conversation.id,
        sender_id=sender_id,
        body=body,
        timestamp=datetime.utcnow()
    )
    db.session.add(message)

    conversation.last_message_time = message.timestamp

    # Determine who is the recipient for unread flag
    if sender.id == conversation.admin_id : # Admin sent the message
        conversation.user_has_unread = True
    elif sender.id == conversation.user_id: # User sent the message
        conversation.admin_has_unread = True
    else: # Sender is not part of this conversation - should not happen with proper checks in routes
        current_app.logger.error(f"Sender ID {sender_id} is not part of conversation ID {conversation_id}.")
        db.session.rollback() # Rollback the message add
        return None

    try:
        db.session.commit()
        current_app.logger.info(f"Reply sent in conversation {conversation.id} by User {sender_id}.")
        return message
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error replying to conversation {conversation.id}: {e}", exc_info=True)
        return None


def get_user_conversations(user_id, page=1, per_page=15):
    """Gets paginated conversations for a specific non-admin user."""
    return Conversation.query.filter_by(user_id=user_id)\
                             .order_by(Conversation.last_message_time.desc())\
                             .paginate(page=page, per_page=per_page, error_out=False)

def get_admin_conversations_list(admin_user_id, page=1, per_page=15, filter_unread=False):
    """
    Gets paginated conversations for a specific admin, or all conversations if current_user is an admin and admin_user_id is None.
    """
    query = Conversation.query
    # If a specific admin_user_id is provided, filter for that admin.
    # Otherwise, if current_user is an admin, they see all conversations.
    # This logic might need adjustment if admins should only see convos they are assigned to vs all.
    # For now, assuming an admin can see all conversations if admin_user_id is not specified.
    if admin_user_id:
         query = query.filter_by(admin_id=admin_user_id)

    if filter_unread:
        query = query.filter(Conversation.admin_has_unread == True)

    return query.order_by(Conversation.last_message_time.desc())\
                .paginate(page=page, per_page=per_page, error_out=False)


def get_conversation_with_messages(conversation_id, viewing_user_id):
    """
    Gets a specific conversation and its messages.
    Also marks the conversation as read for the viewing_user_id.
    """
    conversation = Conversation.query.get(conversation_id)
    if not conversation:
        return None, []

    viewing_user = User.query.get(viewing_user_id)
    if not viewing_user:
        return None, [] # Should not happen if viewing_user_id comes from current_user

    # Authorization check
    if viewing_user.id == conversation.user_id: # Viewing user is the non-admin participant
        if conversation.user_has_unread:
            conversation.user_has_unread = False
            db.session.commit()
    elif viewing_user.id == conversation.admin_id: # Viewing user is the admin participant
        if conversation.admin_has_unread:
            conversation.admin_has_unread = False
            db.session.commit()
    elif viewing_user.role == UserRole.ADMIN: # Another admin viewing the conversation
        # Decide if other admins viewing should mark admin_has_unread as False.
        # For now, only the assigned admin explicitly marks it read for admin.
        # This might be okay as the assigned admin is the primary contact.
        pass
    else: # User is not authorized
        current_app.logger.warning(f"User {viewing_user_id} attempted to view unauthorized conversation {conversation_id}.")
        return None, []

    messages = Message.query.filter_by(conversation_id=conversation.id).order_by(Message.timestamp.asc()).all()
    return conversation, messages


def get_total_unread_message_count(user_id):
    """
    Calculates total unread messages for a user (admin or non-admin).
    Admins see unread counts from all conversations they are assigned to or all if global admin.
    Regular users see unread counts from their conversations.
    """
    user = User.query.get(user_id)
    if not user:
        return 0

    if user.role == UserRole.ADMIN:
        # Sum of admin_has_unread for conversations this admin is part of
        # Or, if super-admin view, could be all admin_has_unread conversations.
        # For now, specific to assigned admin.
        count = db.session.query(Conversation).filter(
            Conversation.admin_id == user.id,
            Conversation.admin_has_unread == True
        ).count()
    else: # Regular User
        count = db.session.query(Conversation).filter(
            Conversation.user_id == user.id,
            Conversation.user_has_unread == True
        ).count()
    return count if count is not None else 0

def close_conversation(conversation_id, closing_user_id):
    """Closes a conversation by the user or admin involved."""
    conversation = Conversation.query.get(conversation_id)
    if not conversation:
        return False

    closing_user = User.query.get(closing_user_id)
    if not closing_user:
        return False

    if conversation.user_id == closing_user_id:
        conversation.status = ConversationStatus.CLOSED_BY_USER
        db.session.commit()
        return True
    elif conversation.admin_id == closing_user_id and closing_user.role == UserRole.ADMIN:
        conversation.status = ConversationStatus.CLOSED_BY_ADMIN
        db.session.commit()
        return True

    return False # Not authorized or conversation already closed by other means
