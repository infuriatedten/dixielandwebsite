from flask import Blueprint, render_template, flash, redirect, url_for, request
from app.decorators import admin_required
from app.models import User, Account, Ticket, PermitApplication, Inspection, TaxBracket

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/')
@admin_required
def index():
    return render_template('admin/dashboard.html', title='Admin Dashboard')

@admin_bp.route('/manage_tickets')
@admin_required
def manage_tickets():
    page = request.args.get('page', 1, type=int)
    tickets = Ticket.query.order_by(Ticket.issue_date.desc()).paginate(page=page, per_page=10)
    return render_template('admin/manage_tickets.html', title='Manage Tickets', tickets_pagination=tickets, TicketStatus=TicketStatus)

from app.forms import EditRulesForm
from app.models import RulesContent
from app import db

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
