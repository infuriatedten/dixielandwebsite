from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import current_user, login_required
from app import db
from app.models import User, UserRole, Account, Transaction, TransactionType
from app.forms import AccountForm, EditBalanceForm, TransactionForm
from app.decorators import admin_required
from decimal import Decimal

bp = Blueprint('admin', __name__)

@bp.route('/')
@login_required
@admin_required
def index():
    return render_template('admin/index.html', title='Admin Dashboard')

# Account Management
@bp.route('/accounts', methods=['GET', 'POST'])
@login_required
@admin_required
def manage_accounts():
    form = AccountForm()
    # Filter out users who already have an account if one account per user rule
    form.user_id.choices = [(u.id, u.username) for u in User.query.filter(~User.accounts.any()).order_by(User.username).all()]

    if form.validate_on_submit():
        user = User.query.get(form.user_id.data)
        if not user:
            flash('Invalid user selected.', 'danger')
            return redirect(url_for('admin.manage_accounts'))

        if Account.query.filter_by(user_id=user.id).first():
            flash(f'User {user.username} already has an account.', 'warning')
            return redirect(url_for('admin.manage_accounts'))

        account = Account(
            user_id=form.user_id.data,
            balance=form.balance.data,
            currency=form.currency.data
        )
        db.session.add(account)
        db.session.flush() # To get account.id for the transaction

        # Log initial balance as a transaction
        initial_transaction = Transaction(
            account_id=account.id,
            type=TransactionType.INITIAL_SETUP,
            amount=form.balance.data,
            description=f"Initial account setup by admin {current_user.username}."
            # processed_by_admin_id=current_user.id # If you add this field
        )
        db.session.add(initial_transaction)
        db.session.commit()
        flash(f'Account created for {user.username} with balance {account.balance} {account.currency}.', 'success')
        return redirect(url_for('admin.manage_accounts'))

    accounts = Account.query.join(User).order_by(User.username).all()
    return render_template('admin/manage_accounts.html', title='Manage Accounts', accounts=accounts, form=form)

@bp.route('/account/<int:account_id>/edit_balance', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_account_balance(account_id):
    account = Account.query.get_or_404(account_id)
    form = EditBalanceForm()

    if form.validate_on_submit():
        amount_change = form.amount.data
        description = form.description.data

        # Create a transaction record for this change
        transaction_type = TransactionType.ADMIN_DEPOSIT if amount_change > 0 else TransactionType.ADMIN_WITHDRAWAL

        transaction = Transaction(
            account_id=account.id,
            type=transaction_type,
            amount=amount_change, # Store the actual change amount
            description=f"{description} (Admin: {current_user.username})"
            # processed_by_admin_id=current_user.id # If you add this field
        )

        # Update balance
        original_balance = account.balance
        account.balance += amount_change # amount_change can be negative

        db.session.add(transaction)
        db.session.add(account) # Add account to session to save balance change
        db.session.commit()

        flash(f'Balance for account {account.id} ({account.owner_user.username}) updated from {original_balance} to {account.balance}. Change: {amount_change}.', 'success')
        return redirect(url_for('admin.manage_accounts'))

    return render_template('admin/edit_account_balance.html', title='Edit Account Balance', form=form, account=account)


# Transaction Management
@bp.route('/transactions', methods=['GET', 'POST'])
@login_required
@admin_required
def manage_transactions():
    form = TransactionForm()
    if form.validate_on_submit():
        account = Account.query.get(form.account_id.data)
        if not account:
            flash('Invalid account selected.', 'danger')
            return redirect(url_for('admin.manage_transactions'))

        transaction_type_value = form.type.data
        transaction_type_enum = TransactionType(transaction_type_value) # Convert string value to Enum
        amount = form.amount.data # This is the direct amount for the transaction type
                                  # For deposits, it's positive. For withdrawals, it should be entered as positive by admin, then made negative if logic implies.
                                  # Or, form can have separate deposit/withdrawal fields.
                                  # Current TransactionForm's amount is just "Amount".
                                  # Let's assume positive amount for deposit, negative for withdrawal for generic admin types.
                                  # For simplicity, we'll assume admin enters it correctly or the type implies direction.

        # If it's a withdrawal type, ensure amount is negative if user entered positive
        if transaction_type_enum == TransactionType.ADMIN_WITHDRAWAL and amount > 0:
            amount = -amount

        transaction = Transaction(
            account_id=account.id,
            type=transaction_type_enum,
            amount=amount,
            description=f"{form.description.data} (Admin: {current_user.username})"
            # processed_by_admin_id=current_user.id
        )

        original_balance = account.balance
        account.balance += amount # amount can be negative for withdrawals

        db.session.add(transaction)
        db.session.add(account)
        db.session.commit()
        flash(f'Transaction of {amount} {account.currency} for {account.owner_user.username} recorded. Balance changed from {original_balance} to {account.balance}.', 'success')
        return redirect(url_for('admin.manage_transactions'))

    page = request.args.get('page', 1, type=int)
    transactions = Transaction.query.join(Account).join(User).order_by(Transaction.timestamp.desc()).paginate(page=page, per_page=15)
    return render_template('admin/manage_transactions.html', title='Manage Transactions', transactions=transactions, form=form)

@bp.route('/users')
@login_required
@admin_required
def manage_users():
    # Basic user listing, can be expanded with edit roles, etc.
    page = request.args.get('page', 1, type=int)
    users = User.query.order_by(User.username).paginate(page=page, per_page=15)
    return render_template('admin/manage_users.html', title='Manage Users', users=users)


# --- Tax Bracket Management (Admin) ---
from app.models import TaxBracket, AutomatedTaxDeductionLog
from app.forms import TaxBracketForm

@bp.route('/tax_brackets', methods=['GET', 'POST'])
@login_required
@admin_required
def manage_tax_brackets():
    form = TaxBracketForm()
    if form.validate_on_submit():
        # Check for overlapping brackets before saving (basic check, more complex validation might be needed)
        # For simplicity, admin is responsible for logical tiers. We can add validation later.
        new_bracket = TaxBracket(
            name=form.name.data,
            description=form.description.data,
            min_balance=form.min_balance.data,
            max_balance=form.max_balance.data if form.max_balance.data is not None else None, # Store None if blank
            tax_rate=form.tax_rate.data,
            is_active=form.is_active.data
        )
        db.session.add(new_bracket)
        db.session.commit()
        flash(f'Tax Bracket "{new_bracket.name}" created successfully.', 'success')
        return redirect(url_for('admin.manage_tax_brackets'))

    brackets = TaxBracket.query.order_by(TaxBracket.min_balance).all()
    return render_template('admin/manage_tax_brackets.html', title='Manage Tax Brackets', form=form, brackets=brackets)

@bp.route('/tax_bracket/<int:bracket_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_tax_bracket(bracket_id):
    bracket = TaxBracket.query.get_or_404(bracket_id)
    form = TaxBracketForm(obj=bracket) # Pre-populate form with existing data

    if form.validate_on_submit():
        bracket.name = form.name.data
        bracket.description = form.description.data
        bracket.min_balance = form.min_balance.data
        bracket.max_balance = form.max_balance.data if form.max_balance.data is not None else None
        bracket.tax_rate = form.tax_rate.data
        bracket.is_active = form.is_active.data
        db.session.commit()
        flash(f'Tax Bracket "{bracket.name}" updated successfully.', 'success')
        return redirect(url_for('admin.manage_tax_brackets'))

    return render_template('admin/edit_tax_bracket.html', title='Edit Tax Bracket', form=form, bracket=bracket)

@bp.route('/tax_bracket/<int:bracket_id>/toggle_active', methods=['POST'])
@login_required
@admin_required
def toggle_tax_bracket_active(bracket_id):
    bracket = TaxBracket.query.get_or_404(bracket_id)
    bracket.is_active = not bracket.is_active
    db.session.commit()
    status = "activated" if bracket.is_active else "deactivated"
    flash(f'Tax Bracket "{bracket.name}" has been {status}.', 'info')
    return redirect(url_for('admin.manage_tax_brackets'))

@bp.route('/tax_deduction_logs')
@login_required
@admin_required
def view_tax_deduction_logs():
    page = request.args.get('page', 1, type=int)
    logs = AutomatedTaxDeductionLog.query.join(User).join(TaxBracket)\
                                       .order_by(AutomatedTaxDeductionLog.deduction_date.desc())\
                                       .paginate(page=page, per_page=20)
    return render_template('admin/view_tax_deduction_logs.html', title='Automated Tax Deduction Logs', logs=logs)

# --- DOT Ticket Management (Admin) ---
from app.models import Ticket, TicketStatus, NotificationType # Already imported User, added NotificationType
from app.forms import ResolveTicketForm # Create this form
from app.services import notification_service # For sending notifications

@bp.route('/tickets', methods=['GET'])
@login_required
@admin_required
def manage_tickets():
    page = request.args.get('page', 1, type=int)
    status_filter_str = request.args.get('status', None)

    query = Ticket.query

    if status_filter_str and hasattr(TicketStatus, status_filter_str.upper()):
        query = query.filter_by(status=TicketStatus[status_filter_str.upper()])

    tickets_pagination = query.order_by(Ticket.issue_date.desc()).paginate(page=page, per_page=15)
    return render_template('admin/manage_tickets.html', title='Manage All Tickets',
                           tickets_pagination=tickets_pagination, TicketStatus=TicketStatus,
                           current_status_filter=status_filter_str)


@bp.route('/ticket/<int:ticket_id>/resolve', methods=['GET', 'POST'])
@login_required
@admin_required
def resolve_ticket(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    if ticket.status not in [TicketStatus.CONTESTED, TicketStatus.OUTSTANDING]:
        flash(
            f'This ticket is not in a state that can be resolved by admin directly '
            f'(Status: {ticket.status.value}). Consider cancelling if appropriate.',
            'warning'
        )
        return redirect(url_for('admin.manage_tickets'))

    form = ResolveTicketForm()

    if form.validate_on_submit():
        new_status_val = form.new_status.data
        new_status_enum = TicketStatus(new_status_val)  # Convert string to Enum

        ticket.status = new_status_enum
        ticket.resolution_notes = form.resolution_notes.data
        ticket.resolved_by_admin_id = current_user.id

        if new_status_enum == TicketStatus.RESOLVED_UNPAID:
            ticket.due_date = datetime.utcnow() + timedelta(hours=72)
            flash(
                f'Ticket #{ticket.id} resolved as "Fine Upheld". User notified to pay. '
                f'New due date: {ticket.due_date.strftime("%Y-%m-%d %H:%M")}',
                'info'
            )

        db.session.commit()
        flash(f'Ticket #{ticket.id} has been updated to status: {new_status_enum.value}.', 'success')

        # Send notifications based on resolution status
        if new_status_enum == TicketStatus.RESOLVED_DISMISSED:
            notification_service.create_notification(
                user_id=ticket.issued_to_user_id,
                message_text=f"Your contested Ticket #{ticket.id} has been Dismissed by an admin.",
                link_url=url_for('dot.view_ticket_detail', ticket_id=ticket.id, _external=True),
                notification_type=NotificationType.GENERAL_INFO,
            )
        elif new_status_enum == TicketStatus.RESOLVED_UNPAID:
            notification_service.create_notification(
                user_id=ticket.issued_to_user_id,
                message_text=f"Your contested Ticket #{ticket.id} has been reviewed: Fine Upheld. Please pay the outstanding amount.",
                link_url=url_for('dot.view_ticket_detail', ticket_id=ticket.id, _external=True),
                notification_type=NotificationType.GENERAL_INFO,
            )
        # TODO: Add notification handling for CANCELLED if needed

        return redirect(url_for('admin.manage_tickets'))

    # Pre-fill form with existing resolution notes for GET or if validation fails
    form.resolution_notes.data = ticket.resolution_notes
    return render_template(
        'admin/resolve_ticket.html',
        title=f'Resolve Ticket #{ticket.id}',
        form=form,
        ticket=ticket
    )



@bp.route('/ticket/<int:ticket_id>/cancel_by_admin', methods=['POST'])
@login_required
@admin_required
def cancel_ticket_by_admin(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    if ticket.status == TicketStatus.PAID:
        flash("Cannot cancel a ticket that has already been paid. Consider a refund process if needed.", "danger")
        return redirect(url_for('admin.manage_tickets'))

    # Add cancellation reason, perhaps via a small form or predefined reasons
    ticket.status = TicketStatus.CANCELLED
    ticket.resolution_notes = f"Cancelled by Admin {current_user.username} on {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}. Reason: (Admin should add reason if form is implemented)"
    ticket.resolved_by_admin_id = current_user.id
    db.session.commit()
    flash(f"Ticket #{ticket.id} has been cancelled.", "success")
    return redirect(url_for('admin.manage_tickets'))

# --- DOT Inspection Management (Admin) ---
from app.models import Inspection # Already imported User, TicketStatus, etc.

@bp.route('/inspections/all', methods=['GET'])
@login_required
@admin_required
def manage_inspections():
    page = request.args.get('page', 1, type=int)
    # Potential filters: by officer, by pass/fail, by date range

    inspections_pagination = Inspection.query.order_by(Inspection.timestamp.desc()).paginate(page=page, per_page=15)
    return render_template('admin/manage_inspections.html', title='Manage All Inspections',
                           inspections_pagination=inspections_pagination)

# --- Permit Application Management (Admin) ---
from app.models import PermitApplication, PermitApplicationStatus # User, etc. already imported

@bp.route('/permits', methods=['GET'])
@login_required
@admin_required
def manage_permit_applications():
    page = request.args.get('page', 1, type=int)
    status_filter_str = request.args.get('status', None)
    user_filter = request.args.get('user', None) # Search by username

    query = PermitApplication.query.join(User, PermitApplication.user_id == User.id) # Join for username sort/filter

    if status_filter_str and hasattr(PermitApplicationStatus, status_filter_str.upper()):
        query = query.filter(PermitApplication.status == PermitApplicationStatus[status_filter_str.upper()])

    if user_filter:
        query = query.filter(User.username.ilike(f"%{user_filter}%"))

    applications_pagination = query.order_by(PermitApplication.application_date.desc()).paginate(page=page, per_page=15)

    return render_template('admin/manage_permit_applications.html',
                           title='Manage All Permit Applications',
                           applications_pagination=applications_pagination,
                           PermitApplicationStatus=PermitApplicationStatus, # Pass enum for template use
                           current_status_filter=status_filter_str,
                           current_user_filter=user_filter)

# Admin can also use the processing routes in dot_bp if they have officer role or decorator allows admin.
# If specific admin overrides or different processing logic is needed, it can be added here.
# For example, an admin might directly issue a permit without fee, or edit submitted applications.
# For now, admin uses the same review/process views as officers via dot_bp, but this admin list gives full overview.
