from flask import Blueprint, render_template, flash, redirect, url_for, request
from flask_login import login_required
from sqlalchemy.orm import joinedload
from app import db
from app.decorators import admin_required
from app.models import (
    User, Account, Ticket, PermitApplication, Inspection, TaxBracket, Transaction,
    TransactionType, VehicleRegion, RulesContent, UserRole, InsuranceClaim,
    InsuranceClaimStatus, PermitApplicationStatus, TicketStatus, Contract,
    Conversation, Message, Fine
)
from app.forms import (
    EditRulesForm, EditUserForm, AccountForm, EditAccountForm, EditTicketForm, EditPermitForm,
    EditInspectionForm, EditTaxBracketForm, EditBalanceForm, EditInsuranceClaimForm,
    EditBankForm, DeleteUserForm, FineForm
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

# ---------------- Routes in Alphabetical Order ---------------- #

@admin_bp.route('/manage/accounts', methods=['GET'])
@login_required
@admin_required
def manage_accounts():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    query = Account.query
    
    # Search functionality
    search_query = request.args.get('search')
    if search_query:
        query = query.join(User).filter(User.username.ilike(f'%{search_query}%'))

    accounts = query.options(
        db.joinedload(Account.user)
    ).order_by(Account.id.desc()).paginate(page=page, per_page=per_page)
    
    return render_template('admin/manage_accounts.html', accounts=accounts, title="Manage Accounts")


@admin_bp.route('/manage/accounts/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_account():
    form = AccountForm()
    if form.validate_on_submit():
        account = Account(
            user_id=form.user_id.data,
            name=form.name.data,
            balance=form.balance.data,
            is_company=form.is_company.data,
            currency=form.currency.data
        )
        db.session.add(account)
        db.session.commit()
        flash('Account created successfully.', 'success')
        return redirect(url_for('admin.manage_accounts'))
    return render_template('admin/edit_account.html', form=form, title="Create Account", account=Account())


@admin_bp.route('/manage/accounts/edit/<int:account_id>', methods=['GET', 'POST'])
@login_required
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
    return render_template('admin/edit_account.html', form=form, title="Edit Account", account=account)


@admin_bp.route('/manage/contracts', methods=['GET'])
@login_required
@admin_required
def manage_contracts():
    contracts = Contract.query.order_by(Contract.created_at.desc()).all()
    return render_template('admin/manage_contracts.html', contracts=contracts)


@admin_bp.route('/manage/fines', methods=['GET'])
@login_required
@admin_required
def manage_fines():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    fines = Fine.query.order_by(Fine.name.asc()).paginate(page=page, per_page=per_page)
    return render_template('admin/manage_fines.html', fines=fines, title="Manage Fines")


@admin_bp.route('/manage/fines/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_fine():
    form = FineForm()
    if form.validate_on_submit():
        new_fine = Fine(
            name=form.name.data,
            description=form.description.data,
            amount=form.amount.data
        )
        db.session.add(new_fine)
        db.session.commit()
        flash('Fine added successfully.', 'success')
        return redirect(url_for('admin.manage_fines'))
    return render_template('admin/edit_fine.html', form=form, title="Add Fine")


@admin_bp.route('/manage/fines/edit/<int:fine_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_fine(fine_id):
    fine = Fine.query.get_or_404(fine_id)
    form = FineForm(obj=fine)
    if form.validate_on_submit():
        fine.name = form.name.data
        fine.description = form.description.data
        fine.amount = form.amount.data
        db.session.commit()
        flash('Fine updated successfully.', 'success')
        return redirect(url_for('admin.manage_fines'))
    return render_template('admin/edit_fine.html', form=form, title="Edit Fine", fine=fine)


@admin_bp.route('/manage/inspections', methods=['GET'])
@login_required
@admin_required
def manage_inspections():
    inspections = Inspection.query.order_by(Inspection.timestamp.desc()).all()
    return render_template('admin/manage_inspections.html', inspections=inspections)

@admin_bp.route('/manage/permits', methods=['GET', 'POST'])
@login_required
@admin_required
def manage_permits():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    permits = PermitApplication.query.order_by(PermitApplication.application_date.desc()).paginate(page=page, per_page=per_page)
    form = EditPermitForm()

    if form.validate_on_submit():
        permit = PermitApplication.query.get(form.id.data)
        if permit:
            permit.status = form.status.data
            # Add more fields here as needed
            db.session.commit()
            flash('Permit updated.', 'success')
        return redirect(url_for('admin.manage_permits'))

    return render_template('admin/manage_permits.html', permits=permits, form=form)

@admin_bp.route('/manage/tax_brackets', methods=['GET', 'POST'])
@login_required
@admin_required
def manage_tax_brackets():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    tax_brackets = TaxBracket.query.order_by(TaxBracket.min_balance.asc()).paginate(page=page, per_page=per_page)
    return render_template('admin/manage_tax_brackets.html', tax_brackets=tax_brackets)

@admin_bp.route('/manage/transactions')
@login_required
@admin_required
def manage_transactions():
    transactions = Transaction.query.order_by(Transaction.date.desc()).all()
    return render_template('admin/manage_transactions.html', transactions=transactions)

@admin_bp.route('/manage/transactions/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_transaction(id):
    transaction = Transaction.query.get_or_404(id)
    form = EditBalanceForm(obj=transaction)
    if form.validate_on_submit():
        transaction.amount = form.amount.data
        transaction.type = form.type.data
        db.session.commit()
        flash('Transaction updated.', 'success')
        return redirect(url_for('admin.manage_transactions'))
    return render_template('admin/edit_transaction.html', form=form, transaction=transaction)

@admin_bp.route('/manage/tickets', methods=['GET', 'POST'])
@login_required
@admin_required
def manage_tickets():
    tickets = Ticket.query.all()
    form = EditTicketForm()

    if form.validate_on_submit():
        ticket = Ticket.query.get(form.id.data)
        if ticket:
            ticket.status = form.status.data
            ticket.fine_amount = form.fine_amount.data
            # Other fields as needed
            db.session.commit()
            flash('Ticket updated.', 'success')
        return redirect(url_for('admin.manage_tickets'))

    return render_template('admin/manage_tickets.html', tickets=tickets, form=form)

@admin_bp.route('/manage/tickets/edit/<int:ticket_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_ticket(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    form = EditTicketForm(obj=ticket)
    if form.validate_on_submit():
        ticket.fine_amount = form.fine_amount.data
        ticket.status = form.status.data
        db.session.commit()
        flash('Ticket updated successfully.', 'success')
        return redirect(url_for('admin.manage_tickets'))
    return render_template('admin/edit_ticket.html', form=form, ticket=ticket)

@admin_bp.route('/manage/vehicle_regions')
@login_required
@admin_required
def manage_vehicle_regions():
    regions = VehicleRegion.query.all()
    return render_template('admin/manage_vehicle_regions.html', regions=regions)

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

@admin_bp.route('/tickets', methods=['GET'])
@login_required
@admin_required
def tickets():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    tickets = Ticket.query.order_by(Ticket.issue_date.desc()).paginate(page=page, per_page=per_page)
    return render_template('admin/tickets.html', title='Manage Tickets', tickets_pagination=tickets, TicketStatus=TicketStatus)

@admin_bp.route('/user/<int:user_id>/delete', methods=['GET', 'POST'])
@admin_required
def delete_user(user_id):
    if request.method == 'GET':
        flash("To delete a user, please use the delete button on the Manage Users page.", "info")
        return redirect(url_for('admin.manage_users'))

    form = DeleteUserForm(prefix=str(user_id))
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
    form = EditUserForm(original_username=user.username, original_email=user.email, obj=user)
    if form.validate_on_submit():
        user.username = form.username.data
        user.email = form.email.data
        user.role = form.role.data
        db.session.commit()
        flash('User updated successfully.', 'success')
        return redirect(url_for('admin.manage_users'))
    return render_template('admin/edit_user.html', title='Edit User', form=form, user=user)

@admin_bp.route('/users', methods=['GET'])
@admin_required
def manage_users():
    page = request.args.get('page', 1, type=int)
    users = User.query.order_by(User.username).paginate(page=page, per_page=10)
    delete_forms = {user.id: DeleteUserForm(prefix=str(user.id)) for user in users.items}
    return render_template('admin/manage_users.html', title='Manage Users', users=users, delete_forms=delete_forms)
