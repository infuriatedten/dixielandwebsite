from flask import Blueprint, render_template, flash, redirect, url_for, request
from app.decorators import admin_required
 feature/admin-dashboard-routes
from app.models import User, Account, Ticket, PermitApplication, Inspection, TaxBracket, PermitApplicationStatus, TicketStatus, Transaction, TransactionType, VehicleRegion
from app.forms import EditRulesForm, EditUserForm, EditAccountForm, EditTicketForm, EditPermitForm, EditInspectionForm, EditTaxBracketForm
from app.models import RulesContent, UserRole
from app import db
=======
from app.models import User, Account, Ticket, PermitApplication, Inspection, TaxBracket
>>>>>>> main

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/')
@admin_required
def index():
    stats = {
        'total_users': User.query.count(),
        'pending_permits': PermitApplication.query.filter_by(status=PermitApplicationStatus.PENDING_REVIEW).count(),
        'open_tickets': Ticket.query.filter_by(status=TicketStatus.OUTSTANDING).count(),
        'revenue': db.session.query(db.func.sum(Transaction.amount)).filter(Transaction.type.in_([TransactionType.TICKET_PAYMENT, TransactionType.PERMIT_FEE_PAYMENT])).scalar() or 0
    }
    return render_template('admin/dashboard.html', title='Admin Dashboard', stats=stats)

@admin_bp.route('/manage_tickets')
@admin_required
 feature/admin-dashboard-routes
def tickets():
    page = request.args.get('page', 1, type=int)
    tickets = Ticket.query.order_by(Ticket.issue_date.desc()).paginate(page=page, per_page=10)
    return render_template('admin/tickets.html', title='Manage Tickets', tickets=tickets)
=======
def manage_tickets():
    page = request.args.get('page', 1, type=int)
    tickets = Ticket.query.order_by(Ticket.issue_date.desc()).paginate(page=page, per_page=10)
    return render_template('admin/manage_tickets.html', title='Manage Tickets', tickets_pagination=tickets, TicketStatus=TicketStatus)

from app.forms import EditRulesForm, EditUserForm, EditAccountForm, EditTicketForm, EditPermitForm, EditInspectionForm, EditTaxBracketForm
from app.models import RulesContent, UserRole
from app import db
>>>>>>> main

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


@admin_bp.route('/accounts')
@admin_required
def manage_accounts():
    page = request.args.get('page', 1, type=int)
    accounts = Account.query.order_by(Account.last_updated_on.desc()).paginate(page=page, per_page=10)
    return render_template('admin/manage_accounts.html', title='Manage Accounts', accounts=accounts)

@admin_bp.route('/inspections')
@admin_required
def manage_inspections():
    page = request.args.get('page', 1, type=int)
    inspections = Inspection.query.order_by(Inspection.timestamp.desc()).paginate(page=page, per_page=10)
    return render_template('admin/manage_inspections.html', title='Manage Inspections', inspections=inspections)

@admin_bp.route('/permits')
@admin_required
def manage_permits():
    page = request.args.get('page', 1, type=int)
    permits = PermitApplication.query.order_by(PermitApplication.application_date.desc()).paginate(page=page, per_page=10)
    return render_template('admin/manage_permits.html', title='Manage Permits', permits=permits)

@admin_bp.route('/users')
@admin_required
def manage_users():
    page = request.args.get('page', 1, type=int)
    users = User.query.order_by(User.username).paginate(page=page, per_page=10)
    return render_template('admin/manage_users.html', title='Manage Users', users=users)

@admin_bp.route('/tax_brackets')
@admin_required
def manage_tax_brackets():
    page = request.args.get('page', 1, type=int)
    tax_brackets = TaxBracket.query.order_by(TaxBracket.min_balance).paginate(page=page, per_page=10)
    return render_template('admin/manage_tax_brackets.html', title='Manage Tax Brackets', tax_brackets=tax_brackets)

@admin_bp.route('/user/<int:user_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    form = EditUserForm(original_username=user.username, original_email=user.email)
    if form.validate_on_submit():
        user.username = form.username.data
        user.email = form.email.data
        user.role = UserRole[form.role.data]
        user.discord_user_id = form.discord_user_id.data
 feature/admin-dashboard-routes
        user.region = VehicleRegion[form.region.data]
=======
        user.region = form.region.data
>>>>>>> main
        db.session.commit()
        flash('User updated successfully.', 'success')
        return redirect(url_for('admin.manage_users'))
    elif request.method == 'GET':
        form.username.data = user.username
        form.email.data = user.email
        form.role.data = user.role.name
        form.discord_user_id.data = user.discord_user_id
 feature/admin-dashboard-routes
        form.region.data = user.region.name
=======
        form.region.data = user.region
>>>>>>> main
    return render_template('admin/edit_user.html', title='Edit User', form=form, user=user)

@admin_bp.route('/account/<int:account_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_account(account_id):
    account = Account.query.get_or_404(account_id)
    form = EditAccountForm(obj=account)
    if form.validate_on_submit():
        account.balance = form.balance.data
        account.is_company = form.is_company.data
        db.session.commit()
        flash('Account updated successfully.', 'success')
        return redirect(url_for('admin.manage_accounts'))
    return render_template('admin/edit_account.html', title='Edit Account', form=form, account=account)

@admin_bp.route('/ticket/<int:ticket_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_ticket(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    form = EditTicketForm(obj=ticket)
    if form.validate_on_submit():
        ticket.fine_amount = form.fine_amount.data
        ticket.status = TicketStatus[form.status.data]
        db.session.commit()
        flash('Ticket updated successfully.', 'success')
 feature/admin-dashboard-routes
        return redirect(url_for('admin.tickets'))
=======
        return redirect(url_for('admin.manage_tickets'))
>>>>>>> main
    return render_template('admin/edit_ticket.html', title='Edit Ticket', form=form, ticket=ticket)

@admin_bp.route('/permit/<int:permit_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_permit(permit_id):
    permit = PermitApplication.query.get_or_404(permit_id)
    form = EditPermitForm(obj=permit)
    if form.validate_on_submit():
        permit.status = PermitApplicationStatus[form.status.data]
        permit.permit_fee = form.permit_fee.data
        db.session.commit()
        flash('Permit application updated successfully.', 'success')
        return redirect(url_for('admin.manage_permits'))
    return render_template('admin/edit_permit.html', title='Edit Permit Application', form=form, permit=permit)

@admin_bp.route('/inspection/<int:inspection_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_inspection(inspection_id):
    inspection = Inspection.query.get_or_404(inspection_id)
    form = EditInspectionForm(obj=inspection)
    if form.validate_on_submit():
        inspection.pass_status = form.pass_status.data
        inspection.notes = form.notes.data
        db.session.commit()
        flash('Inspection updated successfully.', 'success')
        return redirect(url_for('admin.manage_inspections'))
    return render_template('admin/edit_inspection.html', title='Edit Inspection', form=form, inspection=inspection)

feature/admin-dashboard-routes
@admin_bp.route('/tax_bracket/<int:bracket_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_tax_bracket(bracket_id):
    tax_bracket = TaxBracket.query.get_or_404(bracket_id)
=======
@admin_bp.route('/tax_bracket/<int:tax_bracket_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_tax_bracket(tax_bracket_id):
    tax_bracket = TaxBracket.query.get_or_404(tax_bracket_id)
>>>>>>> main
    form = EditTaxBracketForm(obj=tax_bracket)
    if form.validate_on_submit():
        tax_bracket.name = form.name.data
        tax_bracket.min_balance = form.min_balance.data
        tax_bracket.max_balance = form.max_balance.data
        tax_bracket.tax_rate = form.tax_rate.data
        tax_bracket.is_active = form.is_active.data
        db.session.commit()
        flash('Tax bracket updated successfully.', 'success')
        return redirect(url_for('admin.manage_tax_brackets'))
 feature/admin-dashboard-routes
    return render_template('admin/edit_tax_bracket.html', title='Edit Tax Bracket', form=form, bracket=tax_bracket)

@admin_bp.route('/user/<int:user_id>/delete', methods=['POST'])
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash('User deleted successfully.', 'success')
    return redirect(url_for('admin.manage_users'))
=======
    return render_template('admin/edit_tax_bracket.html', title='Edit Tax Bracket', form=form, tax_bracket=tax_bracket)
   main