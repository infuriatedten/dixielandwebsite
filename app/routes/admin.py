from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from sqlalchemy import func
from datetime import datetime

from app import db
from app.models import (
    User, Account, Transaction, TransactionType, TaxBracket,
    AutomatedTaxDeductionLog, Ticket, TicketStatus,
    PermitApplication, PermitApplicationStatus,
    Inspection, NotificationType
)
from app.forms import (
    TransactionForm, AccountForm, EditBalanceForm,
    TaxBracketForm, ResolveTicketForm
)
from app.decorators import admin_required
from app.services import notification_service  # Assuming this exists

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Admin Dashboard Home
@admin_bp.route('/')
@login_required
@admin_required
def index():
    return render_template('admin/index.html', title='Admin Dashboard')

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    total_users = User.query.count()
    pending_permits = PermitApplication.query.filter_by(status='PENDING_REVIEW').count()
    open_tickets = Ticket.query.filter_by(status='open').count()

    revenue = db.session.query(func.coalesce(func.sum(PermitApplication.permit_fee), 0)).scalar()

    stats = {
        'total_users': total_users,
        'pending_permits': pending_permits,
        'open_tickets': open_tickets,
        'revenue': revenue,
    }
    return render_template('admin/dashboard.html', stats=stats)

# Account Management
@admin_bp.route('/accounts', methods=['GET', 'POST'])
@login_required
@admin_required
def accounts():
    form = AccountForm()
    if form.validate_on_submit():
        user = User.query.get(form.user_id.data)
        if user:
            account = Account(
                user_id=user.id,
                balance=form.balance.data,
                is_company=form.is_company.data,
                name=form.name.data,
            )
            db.session.add(account)
            db.session.commit()
            flash('Account created successfully.', 'success')
        else:
            flash('User not found.', 'danger')
        return redirect(url_for('admin.accounts'))

    accounts = Account.query.all()
    return render_template('admin/accounts.html', accounts=accounts, form=form)

@admin_bp.route('/accounts/<int:account_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_account(account_id):
    account = Account.query.get_or_404(account_id)
    form = EditBalanceForm(obj=account)
    if form.validate_on_submit():
        account.balance = form.balance.data
        db.session.commit()
        flash('Account updated.', 'success')
        return redirect(url_for('admin.accounts'))
    return render_template('admin/edit_account.html', account=account, form=form)

# User Management
@admin_bp.route('/users')
@login_required
@admin_required
def users():
    users = User.query.all()
    return render_template('admin/users.html', users=users)

# Transactions
@admin_bp.route('/transactions', methods=['GET', 'POST'])
@login_required
@admin_required
def transactions():
    form = TransactionForm()
    if form.validate_on_submit():
        try:
            sender = Account.query.get(form.sender_account_id.data)
            receiver = Account.query.get(form.receiver_account_id.data)

            if not sender or not receiver:
                flash("Invalid sender or receiver account.", "danger")
            else:
                transaction = Transaction(
                    sender_account_id=sender.id,
                    receiver_account_id=receiver.id,
                    amount=form.amount.data,
                    transaction_type=TransactionType[form.transaction_type.data],
                    description=form.description.data,
                )
                db.session.add(transaction)
                db.session.commit()
                flash('Transaction added.', 'success')
                return redirect(url_for('admin.transactions'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding transaction: {e}', 'danger')

    transactions = Transaction.query.order_by(Transaction.timestamp.desc()).all()
    return render_template('admin/transactions.html', transactions=transactions, form=form)

# Tax Brackets
@admin_bp.route('/tax', methods=['GET', 'POST'])
@login_required
@admin_required
def tax():
    form = TaxBracketForm()
    if form.validate_on_submit():
        bracket = TaxBracket(
            min_balance=form.min_balance.data,
            max_balance=form.max_balance.data,
            tax_rate=form.tax_rate.data,
        )
        db.session.add(bracket)
        db.session.commit()
        flash('Tax bracket added.', 'success')
        return redirect(url_for('admin.tax'))

    tax_brackets = TaxBracket.query.order_by(TaxBracket.min_balance).all()
    return render_template('admin/tax.html', form=form, tax_brackets=tax_brackets)

@admin_bp.route('/tax/delete/<int:bracket_id>', methods=['POST'])
@login_required
@admin_required
def delete_tax_bracket(bracket_id):
    bracket = TaxBracket.query.get_or_404(bracket_id)
    db.session.delete(bracket)
    db.session.commit()
    flash('Tax bracket deleted.', 'success')
    return redirect(url_for('admin.tax'))

@admin_bp.route('/tax/deductions')
@login_required
@admin_required
def tax_deductions():
    logs = AutomatedTaxDeductionLog.query.order_by(AutomatedTaxDeductionLog.timestamp.desc()).limit(100).all()
    return render_template('admin/tax_deductions.html', logs=logs)

# Tickets
@admin_bp.route('/tickets')
@login_required
@admin_required
def tickets():
    tickets = Ticket.query.order_by(Ticket.issue_date.desc()).limit(100).all()
    return render_template('admin/tickets.html', tickets=tickets)

@admin_bp.route('/tickets/<int:ticket_id>/resolve', methods=['GET', 'POST'])
@login_required
@admin_required
def resolve_ticket(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    form = ResolveTicketForm()
    if form.validate_on_submit():
        ticket.status = TicketStatus.RESOLVED
        ticket.notes = form.notes.data
        ticket.resolved_by_id = current_user.id
        ticket.resolved_at = datetime.utcnow()
        db.session.commit()
        flash('Ticket resolved.', 'success')
        return redirect(url_for('admin.tickets'))
    return render_template('admin/resolve_ticket.html', ticket=ticket, form=form)

# Inspections
@admin_bp.route('/inspections')
@login_required
@admin_required
def inspections():
    inspections = Inspection.query.order_by(Inspection.timestamp.desc()).limit(100).all()
    return render_template('admin/inspections.html', inspections=inspections)

# Notifications
@admin_bp.route('/notifications/send', methods=['POST'])
@login_required
@admin_required
def send_notification():
    message = request.form.get('message')
    user_id = request.form.get('user_id')
    if message and user_id:
        notification_service.send_notification(
            recipient_id=int(user_id),
            message=message,
            notification_type=NotificationType.ADMIN_ALERT,
        )
        flash('Notification sent.', 'success')
    else:
        flash('Missing message or user ID.', 'danger')
    return redirect(url_for('admin.index'))

# Permits
@admin_bp.route('/permits')
@login_required
@admin_required
def permits():
    permits = PermitApplication.query.order_by(PermitApplication.created_at.desc()).all()
    return render_template('admin/permits.html', permits=permits)

@admin_bp.route('/permits/<int:permit_id>/approve')
@login_required
@admin_required
def approve_permit(permit_id):
    permit = PermitApplication.query.get_or_404(permit_id)
    permit.status = PermitApplicationStatus.APPROVED
    db.session.commit()
    flash('Permit approved.', 'success')
    return redirect(url_for('admin.permits'))

@admin_bp.route('/permits/<int:permit_id>/reject')
@login_required
@admin_required
def reject_permit(permit_id):
    permit = PermitApplication.query.get_or_404(permit_id)
    permit.status = PermitApplicationStatus.REJECTED
    db.session.commit()
    flash('Permit rejected.', 'danger')
    return redirect(url_for('admin.permits'))
