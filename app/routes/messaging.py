from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import current_user, login_required
from app import db
from app.models import User, UserRole, Conversation, Message, ConversationStatus, NotificationType
from app.forms import StartConversationForm, SendMessageForm
from app.services import messaging_service, notification_service
from flask_login import login_required
from app.decorators import admin_required

messaging_bp = Blueprint('messaging', __name__)

# --- User Routes ---
@messaging_bp.route('/')
@login_required
def list_my_conversations():
    page = request.args.get('page', 1, type=int)
    # This route is for the logged-in user's perspective.
    # If admin, they see conversations where they are the admin_id.
    # If regular user, they see conversations where they are the user_id.
    if current_user.role == UserRole.ADMIN:
        conversations_pagination = messaging_service.get_admin_conversations_list(
            admin_user_id=current_user.id, page=page
        )
        title = "My Admin Conversations"
    else:
        conversations_pagination = messaging_service.get_user_conversations(current_user.id, page=page)
        title = "My Messages"

    return render_template('messaging/conversation_list.html',
                           title=title,
                           conversations_pagination=conversations_pagination,
                           ConversationStatus=ConversationStatus)


@messaging_bp.route('/conversation/<int:conversation_id>', methods=['GET', 'POST'])
@login_required
def view_conversation(conversation_id):
    # Service handles auth check and marking as read
    conversation, messages = messaging_service.get_conversation_with_messages(conversation_id, current_user.id)

    if not conversation:
        flash('Conversation not found or you do not have access.', 'danger')
        return redirect(url_for('messaging.list_my_conversations'))

    form = SendMessageForm() # Renamed from ReplyMessageForm for clarity
    if form.validate_on_submit() and conversation.status == ConversationStatus.OPEN:
        reply = messaging_service.reply_to_conversation(
            conversation_id=conversation.id,
            sender_id=current_user.id,
            body=form.body.data # Changed from message_body
        )
        if reply:
            flash('Your reply has been sent.', 'success')
            # Determine recipient for notification
            recipient_id = conversation.user_id if current_user.id == conversation.admin_id else conversation.admin_id
            notification_service.notify_new_message_received(conversation, recipient_id, current_user.id)
            return redirect(url_for('messaging.view_conversation', conversation_id=conversation.id))
        else:
            flash('There was an error sending your reply. The conversation might be closed or an issue occurred.', 'danger')

    return render_template('messaging/conversation_thread.html',
                           title=f"Re: {conversation.subject}",
                           conversation=conversation,
                           messages=messages,
                           form=form,
                           ConversationStatus=ConversationStatus)


@messaging_bp.route('/conversation/<int:conversation_id>/close', methods=['POST'])
@login_required
def close_conversation_route(conversation_id):
    success = messaging_service.close_conversation(conversation_id, current_user.id)
    if success:
        flash("Conversation has been closed.", "info")
    else:
        flash("Could not close conversation, it may already be closed or you are not authorized.", "danger")

    # Redirect to the conversation list they were likely on
    if current_user.role == UserRole.ADMIN:
        return redirect(url_for('messaging.admin_list_all_conversations')) # Or their specific list
    return redirect(url_for('messaging.list_my_conversations'))


# --- Admin Specific Messaging Routes ---
@messaging_bp.route('/admin/conversations', methods=['GET']) # Changed route for clarity
@login_required
@admin_required
def admin_list_all_conversations(): # Renamed for clarity
    page = request.args.get('page', 1, type=int)
    filter_unread = request.args.get('unread', 'false').lower() == 'true'

    # Service function get_admin_conversations_list with admin_id=None and show_all_admin=True
    # would show ALL conversations if that's the intent.
    # For now, let's assume this lists all conversations in the system for any admin to browse.
    # The service logic for get_admin_conversations_list might need adjustment if it's currently scoped per admin.
    # Let's refine: get_admin_conversations_list(admin_id=None, page=page, show_all_admin=True, filter_unread=filter_unread)
    # For now, sticking to the service as is, meaning it will show convos for THIS admin, or all if admin_id is None.
    # This route implies "all", so admin_id should be None.
    conversations_pagination = messaging_service.get_admin_conversations_list(
        admin_user_id=None, # Pass None to indicate all for any admin if service supports it
        page=page,
        show_all_admin=True, # Add this flag to service if needed, or adjust service
        filter_unread=filter_unread
    )
    # If get_admin_conversations_list doesn't have show_all_admin, it will only show where current_user is admin_id
    # Let's assume the service get_admin_conversations_list(admin_id=None) means show all for an admin.

    return render_template('admin/messaging/admin_conversation_list.html',
                           title='All System Conversations',
                           conversations_pagination=conversations_pagination,
                           filter_unread=filter_unread,
                           ConversationStatus=ConversationStatus)


@messaging_bp.route('/admin/start_conversation', methods=['GET', 'POST'])
@messaging_bp.route('/admin/start_conversation/for_user/<int:target_user_id>', methods=['GET', 'POST']) # More RESTful
@login_required
@admin_required
def admin_start_conversation(target_user_id=None):
    form = StartConversationForm()
    target_user = None

    if target_user_id:
        target_user = User.query.get(target_user_id)
        if target_user:
            form.user_search.data = target_user.username # Pre-fill for display, search still happens on POST
            form.user_search.render_kw = {'readonly': True} # Make it readonly if user is pre-selected
        else:
            flash("Target user for conversation not found.", "warning")

    if form.validate_on_submit():
        # If target_user was pre-filled by URL, use that. Otherwise, search.
        if not target_user:
            searched_username = form.user_search.data
            target_user = User.query.filter(User.username.ilike(searched_username)).first()

        if not target_user:
            flash(f"User '{form.user_search.data if not target_user_id else searched_username}' not found.", 'danger')
        elif target_user.id == current_user.id: # Admin trying to message self as 'user'
            flash("You cannot start a user-conversation with yourself.", "warning")
        elif target_user.role == UserRole.ADMIN:
            flash("This form is for starting conversations with non-admin users. For admin-to-admin, use other channels or a different system.", "info")
        else:
            conversation = messaging_service.create_conversation(
                admin_id=current_user.id,
                target_user_id=target_user.id,
                subject=form.subject.data or f"Message regarding your account", # Default subject
                initial_message_body=form.initial_message_body.data # Changed from message_body
            )
            if conversation:
                flash(f'Conversation started with {target_user.username}.', 'success')
                # Notify user about the new message/conversation (already done by reply_to_conversation if create also calls reply)
                # The create_conversation in service now adds the first message.
                # The reply_to_conversation in service should be the one triggering notification.
                # Let's adjust: create_conversation makes the convo and first message.
                # Then the notification for that first message.
                if conversation.messages: # Check if first message was successfully created
                    notification_service.notify_new_message_received(
                        conversation,
                        target_user.id, # Recipient of the first message
                        current_user.id # Sender of the first message (admin)
                    )
                return redirect(url_for('messaging.view_conversation', conversation_id=conversation.id))
            else:
                flash('Could not start conversation. An error occurred (see logs).', 'danger')

    return render_template('admin/messaging/start_conversation.html',
                           title='Start New Conversation with User',
                           form=form,
                           target_username=target_user.username if target_user else None)

@messaging_bp.app_context_processor
def inject_message_unread_count():
    if current_user.is_authenticated:
        unread_msgs = messaging_service.get_total_unread_message_count(current_user.id)
        return dict(unread_message_count=unread_msgs)
    return dict(unread_message_count=0)
