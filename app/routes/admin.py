from flask import Blueprint, render_template, flash, redirect, url_for, request
from flask_login import login_required
from app import db
from app.decorators import admin_required
from app.models import (
    User, Account, Ticket, PermitApplication, Inspection, TaxBracket, Transaction,
    TransactionType, VehicleRegion, RulesContent, UserRole, InsuranceClaim,
    InsuranceClaimStatus, PermitApplicationStatus, TicketStatus, Contract,
    Conversation, Message
)
from app.forms import (
    EditRulesForm, EditUserForm, EditAccountForm, EditTicketForm, EditPermitForm,
    EditInspectionForm, EditTaxBracketForm, EditBalanceForm, EditInsuranceClaimForm,
    EditBankForm, DeleteUserForm
)
import logging

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# ---------------- Dashboard ---------------- #

@admin_bp.route('/')
@admin_required
def index():
    revenue_query = db.session.query(db.func.sum(Transaction.amount)).filter(
        Transaction.type.in_([
            TransactionType.TICKET_PAYMENT,
            TransactionType.PERMIT_FEE_PAYMENT,
            TransactionType.PERMIT_FEE
        ])
    ).scalar()

    stats = {
        'total_users': User.query.count(),
        'pending_permits': PermitApplication.query.filter_by(
            status=PermitApplicationStatus.PENDING_REVIEW
        ).count(),
        'open_tickets': Ticket.query.filter_by(
            status=TicketStatus.OUTSTANDING
        ).count(),
        'revenue': revenue_query or 0.0
    }
    return render_template('admin/dashboard.html', title='Admin Dashboard', stats=stats)

# ---------------- Rules ---------------- #

@admin_bp.route('/rules/edit', methods=['GET', 'POST'])
@admin_required
def edit_rules():
    rules = RulesContent.query.first()
    if not rules:
        rules = RulesContent(content_markdown='Initial rules content.')
        db.session.add(rules)
        db.session.commit()

    form = EditRulesForm(obj=rules)
    if form.validate_on_submit():
        rules.content_markdown = form.content_markdown.data
        db.session.commit()
        flash('Rules updated successfully.', 'success')
        return redirect(url_for('main.view_rules'))
    return render_template('admin/edit_rules.html', title='Edit Rules', form=form)

# ---------------- User Management ---------------- #

@admin_bp.route('/users', methods=['GET'])
@admin_required
def manage_users():
    page = request.args.get('page', 1, type=int)
    users = User.query.order_by(User.username).paginate(page=page, per_page=10)
    delete_forms = {user.id: DeleteUserForm(prefix=str(user.id)) for user in users.items}
    return render_template('admin/manage_users.html', title='Manage Users', users=users, delete_forms=delete_forms)

@admin_bp.route('/user/<int:user_id>/delete', methods=['POST'])
@admin_required
def delete_user(user_id):
    form = DeleteUserForm()
    if form.validate_on_submit():
        user_to_delete = User.query.get_or_404(user_id)
        db.session.delete(user_to_delete)
        db.session.commit()
        flash(f"User {user_to_delete.username} deleted.", "success")
    else:
        flash("CSRF validation failed or invalid form submission.", "danger")
    return redirect(url_for('admin.manage_users'))

@admin_bp.route('/user/<int:user_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    form = EditUserForm(obj=user)
    if form.validate_on_submit():
        user.username = form.username.data
        user.email = form.email.data
        user.role_id = form.role_id.data
        db.session.commit()
        flash('User updated successfully.', 'success')
        return redirect(url_for('admin.manage_users'))
    return render_template('admin/edit_user.html', title='Edit User', form=form, user=user)

# ... [All other unchanged route handlers below stay the same, e.g. account, tickets, permits, etc.]

