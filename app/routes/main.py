from flask import Blueprint, render_template, url_for, redirect, flash
from flask_login import current_user, login_required
from app.decorators import admin_required, officer_required
from app.models import (
    UserRole, RulesContent, Farmer, Parcel, UserVehicle, Account,
    InsuranceClaim, Company, Contract, ContractStatus, User
)
from app.forms import (
    ParcelForm, InsuranceClaimForm, CompanyNameForm, ContractForm
)
from app import db
from datetime import datetime
import mistune

main_bp = Blueprint('main', __name__)

# ------------------- General Routes -------------------

@main_bp.route('/', endpoint='index')
def main_index():
    return render_template('main/index.html', title='Home')

@main_bp.route('/rules', endpoint='view_rules')
def view_rules():
    rules_entry = RulesContent.query.first()
    rules_content_html = ""
    if rules_entry and rules_entry.content_markdown:
        markdown_parser = mistune.create_markdown(escape=False)
        rules_content_html = markdown_parser(rules_entry.content_markdown)
    else:
        rules_content_html = "<p>The rules have not been set yet. Please check back later.</p>"
        if current_user.is_authenticated and hasattr(current_user, 'role') and current_user.role.value == UserRole.ADMIN.value:
            rules_content_html += f'<p><a href="{url_for("admin.edit_rules")}">Set the rules now.</a></p>'

    return render_template('main/rules.html', title='Rules',
                           rules_content_html=rules_content_html,
                           current_user=current_user, UserRole=UserRole)

# ------------------- Admin & Officer Dashboards -------------------

@main_bp.route('/admin-dashboard')
@admin_required
def admin_dashboard():
    stats = {
        'total_users': User.query.count(),
        'pending_permits': 0,  # Add real logic if needed
        'open_tickets': 0,     # Add real logic if needed
        'revenue': 0           # Add real logic if needed
    }
    return render_template('admin/dashboard.html', title='Admin Dashboard', stats=stats)

@main_bp.route('/officer-area')
@officer_required
def officer_area():
    return render_template('officer/area.html', title='Officer Area')

# ------------------- Farmers Section -------------------

@main_bp.route('/farmers', methods=['GET', 'POST'])
@login_required
def farmers():
    parcel_form = ParcelForm()
    insurance_form = InsuranceClaimForm()
    farmer = Farmer.query.filter_by(user_id=current_user.id).first()

    if parcel_form.validate_on_submit() and parcel_form.submit.data:
        if farmer:
            parcel = Parcel(
                location=parcel_form.location.data,
                size=parcel_form.size.data,
                farmer_id=farmer.id
            )
            db.session.add(parcel)
            db.session.commit()
            flash('Parcel added successfully!', 'success')
        else:
            flash('You must be a registered farmer to add a parcel.', 'danger')
        return redirect(url_for('main.farmers'))

    if insurance_form.validate_on_submit() and insurance_form.submit.data:
        if farmer:
            claim = InsuranceClaim(
                reason=insurance_form.reason.data,
                farmer_id=farmer.id
            )
            db.session.add(claim)
            db.session.commit()
            flash('Insurance claim submitted successfully!', 'success')
        else:
            flash('You must be a registered farmer to submit a claim.', 'danger')
        return redirect(url_for('main.farmers'))

    parcels = Parcel.query.filter_by(farmer_id=farmer.id).all() if farmer else []
    total_acres = sum(parcel.size for parcel in parcels)
    vehicles = UserVehicle.query.filter_by(user_id=current_user.id).all()
    bank_accounts = Account.query.filter_by(user_id=current_user.id).all()
    insurance_claims = InsuranceClaim.query.filter_by(farmer_id=farmer.id).all() if farmer else []

    return render_template(
        'main/farmers.html',
        title='Farmers',
        parcels=parcels,
        total_acres=total_acres,
        vehicles=vehicles,
        bank_accounts=bank_accounts,
        insurance_claims=insurance_claims,
        parcel_form=parcel_form,
        insurance_form=insurance_form
    )

# ------------------- Company Management -------------------

@main_bp.route('/company', methods=['GET', 'POST'])
@login_required
def company():
    form = CompanyNameForm()
    if form.validate_on_submit():
        company = Company.query.filter_by(user_id=current_user.id).first()
        if not company:
            company = Company(user_id=current_user.id)
        company.name = form.name.data
        db.session.add(company)
        db.session.commit()
        return redirect(url_for('main.company'))

    company = Company.query.filter_by(user_id=current_user.id).first()
    vehicles = UserVehicle.query.filter_by(user_id=current_user.id).all() if company else []
    if company:
        form.name.data = company.name

    return render_template('main/company.html', title='Company', form=form, vehicles=vehicles)

# ------------------- Contracts System -------------------

@main_bp.route('/contracts')
@login_required
def contracts():
    contracts = Contract.query.filter_by(status=ContractStatus.AVAILABLE).all()
    return render_template('main/contracts.html', title='Contracts', contracts=contracts)

@main_bp.route('/contract/<int:contract_id>/claim', methods=['POST'])
@login_required
def claim_contract(contract_id):
    contract = Contract.query.get_or_404(contract_id)
    if contract.status == ContractStatus.AVAILABLE:
        contract.status = ContractStatus.CLAIMED
        contract.claimant_id = current_user.id
        contract.claimed_date = datetime.utcnow()
        db.session.commit()
        flash('Contract claimed successfully!', 'success')
    else:
        flash('This contract is not available to be claimed.', 'danger')
    return redirect(url_for('main.contracts'))

@main_bp.route('/contracts/create', methods=['GET', 'POST'])
@login_required
def create_contract():
    form = ContractForm()
    if form.validate_on_submit():
        contract = Contract(
            title=form.title.data,
            description=form.description.data,
            reward=form.reward.data,
            creator_id=current_user.id
        )
        db.session.add(contract)
        db.session.commit()
        flash('Contract created successfully!', 'success')
        return redirect(url_for('main.contracts'))
    return render_template('main/create_contract.html', title='Create Contract', form=form)

# ------------------- User List -------------------

@main_bp.route('/users')
@login_required
def users():
    users = User.query.all()
    return render_template('main/users.html', title='Users', users=users)
