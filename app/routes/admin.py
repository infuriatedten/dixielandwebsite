from flask import Blueprint, render_template, flash, redirect, url_for, request
from flask_login import login_required
from app import db
from app.decorators import admin_required
from app.models import (
    User, Account, Ticket, PermitApplication, Inspection, TaxBracket, Transaction,
    TransactionType, VehicleRegion, RulesContent, UserRole, InsuranceClaim,
    InsuranceClaimStatus, PermitApplicationStatus, TicketStatus, Contract
)
from app.forms import (
    EditRulesForm, EditUserForm, EditAccountForm, EditTicketForm, EditPermitForm,
    EditInspectionForm, EditTaxBracketForm, EditBalanceForm, EditInsuranceClaimForm,
    EditBankForm
)

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

@admin_bp.route('/users')
@admin_required
def manage_users():
    page = request.args.get('page', 1, type=int)
    users = User.query.order_by(User.username).paginate(page=page, per_page=10)
    return render_template('admin/manage_users.html', title='Manage Users', users=users)

@admin_bp.route('/users', methods=['GET', 'POST'])
@admin_required
def manage_users():
    page = request.args.get('page', 1, type=int)
    users = User.query.paginate(page=page, per_page=10)

    delete_forms = {user.id: DeleteUserForm() for user in users.items}
    return render_template("admin/manage_users.html", users=users, delete_forms=delete_forms)

@admin_bp.route('/users/delete/<int:user_id>', methods=['POST'])
@admin_required
def delete_user(user_id):
    form = DeleteUserForm()
    if form.validate_on_submit():
        user = User.query.get_or_404(user_id)
        db.session.delete(user)
        db.session.commit()
        flash(f"User {user.username} deleted.", "success")
    else:
        flash("CSRF validation failed.", "danger")
    return redirect(url_for("admin.manage_users"))


# ---------------- Account Management ---------------- #

@admin_bp.route('/accounts')
@admin_required
def manage_accounts():
    page = request.args.get('page', 1, type=int)
    accounts = Account.query.order_by(Account.last_updated_on.desc()).paginate(page=page, per_page=10)
    return render_template('admin/manage_accounts.html', title='Manage Accounts', accounts=accounts)

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

import logging

@admin_bp.route('/account/<int:account_id>/edit_balance', methods=['GET', 'POST'])
@admin_required
def edit_account_balance(account_id):
    account = Account.query.get_or_404(account_id)
    form = EditBalanceForm()
    if form.validate_on_submit():
        amount = form.amount.data
        description = form.description.data
        logging.info(f"Attempting to update balance for account {account_id} by {amount}")
        try:
            transaction = Transaction(
                account_id=account.id,
                amount=amount,
                description=description,
                type=TransactionType.ADMIN_DEPOSIT if amount > 0 else TransactionType.ADMIN_WITHDRAWAL
            )
            db.session.add(transaction)
            account.balance += amount
            db.session.commit()
            flash('Account balance updated successfully.', 'success')
            logging.info(f"Successfully updated balance for account {account_id}")
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating account balance: {e}', 'danger')
            logging.error(f"Error updating balance for account {account_id}: {e}")
        return redirect(url_for('admin.manage_accounts'))
    return render_template('admin/edit_account_balance.html', title='Edit Account Balance', form=form, account=account)


@admin_bp.route('/account/<int:account_id>/edit_bank', methods=['GET', 'POST'])
@admin_required
def edit_bank(account_id):
    account = Account.query.get_or_404(account_id)
    form = EditBankForm(obj=account)
    if form.validate_on_submit():
        account.bank_name = form.bank_name.data
        account.account_number = form.account_number.data
        account.routing_number = form.routing_number.data
        db.session.commit()
        flash('Bank details updated successfully.', 'success')
        return redirect(url_for('admin.manage_accounts'))
    return render_template('admin/edit_bank.html', title='Edit Bank Details', form=form, account=account)


# ---------------- Ticket Management ---------------- #

@admin_bp.route('/tickets')
@admin_required
def tickets():
    page = request.args.get('page', 1, type=int)
    tickets = Ticket.query.order_by(Ticket.issue_date.desc()).paginate(page=page, per_page=10)
    return render_template('admin/tickets.html', title='Manage Tickets', tickets_pagination=tickets, TicketStatus=TicketStatus)

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
        return redirect(url_for('admin.tickets'))
    return render_template('admin/edit_ticket.html', title='Edit Ticket', form=form, ticket=ticket)


# ---------------- Permit & Inspection ---------------- #

@admin_bp.route('/permits')
@admin_required
def manage_permits():
    page = request.args.get('page', 1, type=int)
    permits = PermitApplication.query.order_by(PermitApplication.application_date.desc()).paginate(page=page, per_page=10)
    return render_template('admin/manage_permits.html', title='Manage Permits', permits=permits)

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

@admin_bp.route('/inspections')
@admin_required
def manage_inspections():
    page = request.args.get('page', 1, type=int)
    inspections = Inspection.query.order_by(Inspection.timestamp.desc()).paginate(page=page, per_page=10)
    return render_template('admin/manage_inspections.html', title='Manage Inspections', inspections=inspections)

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


# ---------------- Tax ---------------- #

@admin_bp.route('/tax_brackets')
@admin_required
def manage_tax_brackets():
    page = request.args.get('page', 1, type=int)
    tax_brackets = TaxBracket.query.order_by(TaxBracket.min_balance).paginate(page=page, per_page=10)
    return render_template('admin/manage_tax_brackets.html', title='Manage Tax Brackets', tax_brackets=tax_brackets)

@admin_bp.route('/tax_bracket/<int:bracket_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_tax_bracket(bracket_id):
    bracket = TaxBracket.query.get_or_404(bracket_id)
    form = EditTaxBracketForm(obj=bracket)
    if form.validate_on_submit():
        bracket.name = form.name.data
        bracket.min_balance = form.min_balance.data
        bracket.max_balance = form.max_balance.data
        bracket.tax_rate = form.tax_rate.data
        bracket.is_active = form.is_active.data
        db.session.commit()
        flash('Tax bracket updated successfully.', 'success')
        return redirect(url_for('admin.manage_tax_brackets'))
    return render_template('admin/edit_tax_bracket.html', title='Edit Tax Bracket', form=form, bracket=bracket)


# ---------------- Contracts ---------------- #

@admin_bp.route('/contracts')
@admin_required
def manage_contracts():
    page = request.args.get('page', 1, type=int)
    contracts = Contract.query.order_by(Contract.creation_date.desc()).paginate(page=page, per_page=10)
    return render_template('admin/manage_contracts.html', title='Manage Contracts', contracts=contracts)

@admin_bp.route('/contract/<int:contract_id>/delete', methods=['POST'])
@admin_required
def delete_contract(contract_id):
    contract = Contract.query.get_or_404(contract_id)
    db.session.delete(contract)
    db.session.commit()
    flash('Contract deleted successfully.', 'success')
    return redirect(url_for('admin.manage_contracts'))


# ---------------- Insurance Claims ---------------- #

@admin_bp.route('/insurance_claims')
@admin_required
def manage_insurance_claims():
    page = request.args.get('page', 1, type=int)
    claims = InsuranceClaim.query.order_by(InsuranceClaim.claim_date.desc()).paginate(page=page, per_page=10)
    return render_template('admin/manage_insurance_claims.html', title='Manage Insurance Claims', claims=claims)

@admin_bp.route('/insurance_claim/<int:claim_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_insurance_claim(claim_id):
    claim = InsuranceClaim.query.get_or_404(claim_id)
    form = EditInsuranceClaimForm(obj=claim)
    if form.validate_on_submit():
        claim.status = InsuranceClaimStatus[form.status.data]
        db.session.commit()
        flash('Insurance claim updated successfully.', 'success')
        return redirect(url_for('admin.manage_insurance_claims'))
    return render_template('admin/edit_insurance_claim.html', title='Edit Insurance Claim', form=form, claim=claim)


# ---------------- Messaging (System Conversations) ---------------- #

@admin_bp.route('/conversations', methods=['GET'])
@admin_required
def admin_list_all_conversations():
    page = request.args.get('page', 1, type=int)
    conversations = Conversation.query.order_by(Conversation.last_message_date.desc()).paginate(page=page, per_page=10)
    return render_template('admin/conversations.html', title='All Conversations', conversations=conversations)

@admin_bp.route('/conversation/<int:conversation_id>', methods=['GET', 'POST'])
@admin_required
def admin_view_conversation(conversation_id):
    conversation = Conversation.query.get_or_404(conversation_id)
    messages = Message.query.filter_by(conversation_id=conversation_id).order_by(Message.timestamp).all()
    # Form to send new messages could go here (not shown)
    return render_template('admin/view_conversation.html', title='Conversation Details', conversation=conversation, messages=messages)
