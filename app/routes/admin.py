from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import current_user, login_required
from app import db
from app.models import (
    User, UserRole, Account, Transaction, TransactionType,
    TaxBracket, AutomatedTaxDeductionLog,
    Ticket, TicketStatus, NotificationType,
    Inspection,
    PermitApplication, PermitApplicationStatus
)
from app.forms import (
    AccountForm, EditBalanceForm, TransactionForm,
    TaxBracketForm, ResolveTicketForm
)
from app.decorators import admin_required
from app.services import notification_service
from datetime import datetime, timedelta

# admin.py (line 19)
@bp.route('/')
@login_required
def index():
    return render_template('admin/index.html', title='Admin Dashboard')



# Account Management with admin role assignment
@bp.route('/accounts', methods=['GET', 'POST'])
@login_required
@admin_required
def manage_accounts():
    form = AccountForm()
    # Only users without an account can be assigned
    form.user_id.choices = [(u.id, u.username) for u in User.query.filter(~User.accounts.any()).order_by(User.username).all()]

    if form.validate_on_submit():
        user = User.query.get(form.user_id.data)
        if not user:
            flash('Invalid user selected.', 'danger')
            return redirect(url_for('admin.manage_accounts'))

        if Account.query.filter_by(user_id=user.id).first():
            flash(f'User {user.username} already has an account.', 'warning')
            return redirect(url_for('admin.manage_accounts'))

        make_admin = form.make_admin.data
        admins_exist = User.query.filter_by(role='admin').count() > 0

        if make_admin:
            if not admins_exist or current_user.role == 'admin':
                user.role = 'admin'
                flash(f'{user.username} has been granted admin privileges.', 'success')
            else:
                flash('Only admins can assign admin role.', 'danger')
                return redirect(url_for('admin.manage_accounts'))

        account = Account(user_id=user.id, balance=form.balance.data, currency=form.currency.data)
        db.session.add(account)
        db.session.flush()  # To get account.id for transaction

        initial_transaction = Transaction(
            account_id=account.id,
            type=TransactionType.INITIAL_SETUP,
            amount=form.balance.data,
            description=f"Initial account setup by admin {current_user.username}."
        )
        db.session.add(initial_transaction)
        db.session.commit()

        flash(f'Account created for {user.username} with balance {account.balance} {account.currency}.', 'success')
        return redirect(url_for('admin.manage_accounts'))

    accounts = Account.query.join(User).order_by(User.username).all()
    return render_template('admin/manage_accounts.html', title='Manage Accounts', accounts=accounts, form=form)


@bp.route('/toggle_role/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def toggle_user_role(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("You cannot change your own role.", "warning")
        return redirect(url_for('admin.manage_accounts'))

    user.role = 'admin' if user.role != 'admin' else 'user'
    db.session.commit()
    flash(f"{user.username}'s role changed to {user.role}.", "success")
    return redirect(url_for('admin.manage_accounts'))


@bp.route('/account/<int:account_id>/edit_balance', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_account_balance(account_id):
    account = Account.query.get_or_404(account_id)
    form = EditBalanceForm()

    if form.validate_on_submit():
        amount_change = form.amount.data
        description = form.description.data

        transaction_type = TransactionType.ADMIN_DEPOSIT if amount_change > 0 else TransactionType.ADMIN_WITHDRAWAL
        transaction = Transaction(
            account_id=account.id,
            type=transaction_type,
            amount=amount_change,
            description=f"{description} (Admin: {current_user.username})"
        )

        original_balance = account.balance
        account.balance += amount_change

        db.session.add(transaction)
        db.session.add(account)
        db.session.commit()

        flash(
            f'Balance for account {account.id} ({account.owner_user.username}) updated from '
            f'{original_balance} to {account.balance}. Change: {amount_change}.',
            'success'
        )
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

        transaction_type_enum = TransactionType(form.type.data)
        amount = form.amount.data

        # Ensure withdrawal amounts are negative
        if transaction_type_enum == TransactionType.ADMIN_WITHDRAWAL and amount > 0:
            amount = -amount

        transaction = Transaction(
            account_id=account.id,
            type=transaction_type_enum,
            amount=amount,
            description=f"{form.description.data} (Admin: {current_user.username})"
        )

        original_balance = account.balance
        account.balance += amount

        db.session.add(transaction)
        db.session.add(account)
        db.session.commit()

        flash(
            f'Transaction of {amount} {account.currency} for {account.owner_user.username} recorded. '
            f'Balance changed from {original_balance} to {account.balance}.',
            'success'
        )
        return redirect(url_for('admin.manage_transactions'))

    page = request.args.get('page', 1, type=int)
    transactions = Transaction.query.join(Account).join(User).order_by(Transaction.timestamp.desc()).paginate(page=page, per_page=15)
    return render_template('admin/manage_transactions.html', title='Manage Transactions', transactions=transactions, form=form)


@bp.route('/users')
@login_required
@admin_required
def manage_users():
    page = request.args.get('page', 1, type=int)
    users = User.query.order_by(User.username).paginate(page=page, per_page=15)
    return render_template('admin/manage_users.html', title='Manage Users', users=users)


# Tax Bracket Management
@bp.route('/tax_brackets', methods=['GET', 'POST'])
@login_required
@admin_required
def manage_tax_brackets():
    form = TaxBracketForm()

    if form.validate_on_submit():
        new_bracket = TaxBracket(
            name=form.name.data,
            description=form.description.data,
            min_balance=form.min_balance.data,
            max_balance=form.max_balance.data if form.max_balance.data is not None else None,
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
    form = TaxBracketForm(obj=bracket)

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


# DOT Ticket Management
@bp.route('/tickets', methods=['GET'])
@login_required
@admin_required
def manage_tickets():
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', None, type=str)

    query = Ticket.query.order_by(Ticket.issue_date.desc())

    if status_filter:
        try:
            status_enum = TicketStatus(status_filter)
            query = query.filter(Ticket.status == status_enum)
        except ValueError:
            flash('Invalid ticket status filter.', 'warning')

    tickets = query.paginate(page=page, per_page=20)
    return render_template('admin/manage_tickets.html', title='Manage Tickets', tickets=tickets, status_filter=status_filter)


@bp.route('/ticket/<int:ticket_id>/resolve', methods=['GET', 'POST'])
@login_required
@admin_required
def resolve_ticket(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    form = ResolveTicketForm()

    if form.validate_on_submit():
        ticket.status = TicketStatus.RESOLVED
        ticket.resolution_notes = form.notes.data
        ticket.resolved_by_id = current_user.id
        ticket.resolution_date = datetime.utcnow()
        db.session.commit()

        notification_service.notify_user(
            user_id=ticket.issued_to_id,
            notification_type=NotificationType.TICKET_RESOLVED,
            message=f"Your ticket #{ticket.id} has been resolved."
        )

        flash(f'Ticket #{ticket.id} marked as resolved.', 'success')
        return redirect(url_for('admin.manage_tickets'))

    return render_template('admin/resolve_ticket.html', title='Resolve Ticket', ticket=ticket, form=form)


# DOT Inspection Management
@bp.route('/inspections', methods=['GET'])
@login_required
@admin_required
def manage_inspections():
    page = request.args.get('page', 1, type=int)
    inspections = Inspection.query.order_by(Inspection.date.desc()).paginate(page=page, per_page=20)
    return render_template('admin/manage_inspections.html', title='Manage Inspections', inspections=inspections)


# Permit Applications Management
@bp.route('/permits', methods=['GET'])
@login_required
@admin_required
def manage_permits():
    page = request.args.get('page', 1, type=int)
    permits = PermitApplication.query.order_by(PermitApplication.application_date.desc()).paginate(page=page, per_page=20)
    return render_template('admin/manage_permits.html', title='Manage Permit Applications', permits=permits)


@bp.route('/permit/<int:permit_id>/approve', methods=['POST'])
@login_required
@admin_required
def approve_permit(permit_id):
    permit = PermitApplication.query.get_or_404(permit_id)
    if permit.status != PermitApplicationStatus.PENDING:
        flash('Permit application already processed.', 'warning')
        return redirect(url_for('admin.manage_permits'))

    permit.status = PermitApplicationStatus.APPROVED
    permit.reviewed_by_id = current_user.id
    permit.review_date = datetime.utcnow()
    db.session.commit()

    notification_service.notify_user(
        user_id=permit.user_id,
        notification_type=NotificationType.PERMIT_APPROVED,
        message=f"Your permit application #{permit.id} has been approved."
    )

    flash(f'Permit application #{permit.id} approved.', 'success')
    return redirect(url_for('admin.manage_permits'))


@bp.route('/permit/<int:permit_id>/reject', methods=['POST'])
@login_required
@admin_required
def reject_permit(permit_id):
    permit = PermitApplication.query.get_or_404(permit_id)
    if permit.status != PermitApplicationStatus.PENDING:
        flash('Permit application already processed.', 'warning')
        return redirect(url_for('admin.manage_permits'))

    permit.status = PermitApplicationStatus.REJECTED
    permit.reviewed_by_id = current_user.id
    permit.review_date = datetime.utcnow()
    db.session.commit()

    notification_service.notify_user(
        user_id=permit.user_id,
        notification_type=NotificationType.PERMIT_REJECTED,
        message=f"Your permit application #{permit.id} has been rejected."
    )

    flash(f'Permit application #{permit.id} rejected.', 'info')
    return redirect(url_for('admin.manage_permits'))
