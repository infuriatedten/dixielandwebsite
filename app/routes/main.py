from flask import Blueprint, render_template, url_for, redirect, flash, request
from flask_login import current_user, login_required
from app.decorators import admin_required, officer_required
from app.models import (
    User, UserRole, RulesContent, Farmer, Parcel, UserVehicle, 
    Account, InsuranceClaim, Contract, ContractStatus, Company
)
from app.forms import (
    ParcelForm, InsuranceClaimForm, ContractForm, CompanyNameForm
)
from app import db
import mistune
from datetime import datetime

main_bp = Blueprint('main', __name__)

# Home route
@main_bp.route('/', endpoint='index')
def main_index():
    return render_template('main/index.html', title='Home')


# Admin dashboard
@main_bp.route('/admin-dashboard')
@admin_required
def admin_dashboard():
    stats = {
        'total_users': User.query.count(),
        'pending_permits': 0,  # Add logic later
        'open_tickets': 0,     # Add logic later
        'revenue': 0           # Add logic later
    }
    return render_template('admin/dashboard.html', title='Admin Dashboard', stats=stats)


# Officer area
@main_bp.route('/officer-area')
@officer_required
def officer_area():
    return render_template('officer/area.html', title='Officer Area')


# Rules page (Markdown-based)
@main_bp.route('/rules', endpoint='view_rules')
def view_rules():
    rules_entry = RulesContent.query.first()
    markdown_parser = mistune.create_markdown(escape=False)
    
    if rules_entry and rules_entry.content_markdown:
        rules_content_html = markdown_parser(rules_entry.content_markdown)
    else:
        rules_content_html = "<p>The rules have not been set yet. Please check back later.</p>"
        if current_user.is_authenticated and current_user.role == UserRole.ADMIN:
            rules_content_html += f'<p><a href="{url_for("admin.edit_rules")}">Set the rules now.</a></p>'

    return render_template('main/rules.html', title='Rules',
                           rules_content_html=rules_content_html,
                           current_user=current_user, UserRole=UserRole)



# Farmer area: parcels, claims, etc.

from app.models import Farmer, Parcel, UserVehicle, Account, InsuranceClaim, Contract, ContractStatus, Transaction, TransactionType
from app.forms import ParcelForm, InsuranceClaimForm, ContractForm
from flask import redirect, flash
from app import db
from datetime import datetime


@main_bp.route('/farmers', methods=['GET', 'POST'])
@login_required
def farmers():
    parcel_form = ParcelForm()
    insurance_form = InsuranceClaimForm()
    farmer = Farmer.query.filter_by(user_id=current_user.id).first()

    # Handle parcel submission
    if parcel_form.validate_on_submit() and parcel_form.submit.data:
        if farmer:
            new_parcel = Parcel(
                location=parcel_form.location.data,
                size=parcel_form.size.data,
                farmer_id=farmer.id
            )
            db.session.add(new_parcel)
            db.session.commit()
            flash('Parcel added successfully!', 'success')
        else:
            flash('You must be a registered farmer to add a parcel.', 'danger')
        return redirect(url_for('main.farmers'))

    # Handle insurance claim
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

    # Gather related data
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


from app.models import Company, UserVehicle, Account
from app.forms import CompanyNameForm
from app import db


# Company registration and dashboard
@main_bp.route('/company', methods=['GET', 'POST'])
@login_required
def company():
    form = CompanyNameForm()
    company = Company.query.filter_by(user_id=current_user.id).first()

    if form.validate_on_submit():
        if not company:
            company = Company(user_id=current_user.id)
            db.session.add(company)
        company.name = form.name.data
        db.session.commit()
        return redirect(url_for('main.company'))

    vehicles = UserVehicle.query.filter_by(user_id=current_user.id).all()
    if company:
        form.name.data = company.name

    return render_template('main/company.html', title='Company', form=form, vehicles=vehicles)


# View available contracts
@main_bp.route('/contracts')
@login_required
def contracts():
    available_contracts = Contract.query.filter_by(status=ContractStatus.AVAILABLE).all()
    return render_template('main/contracts.html', title='Contracts', contracts=available_contracts)


# Claim a contract
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
    return redirect(request.referrer or url_for('main.contracts'))


# List users
@main_bp.route('/users')
@admin_required
def users():
    all_users = User.query.all()
    return render_template('main/users.html', title='Users', users=all_users)

@main_bp.route('/contract/<int:contract_id>/delete', methods=['POST'])
@login_required
def delete_contract(contract_id):
    contract = Contract.query.get_or_404(contract_id)
    if contract.creator_id != current_user.id:
        flash('You are not authorized to delete this contract.', 'danger')
        return redirect(url_for('main.contracts'))
    db.session.delete(contract)
    db.session.commit()
    flash('Contract deleted successfully!', 'success')
    return redirect(url_for('main.contracts'))

# Create a contract
@main_bp.route('/contracts/create', methods=['GET', 'POST'])
@login_required
def create_contract():
    form = ContractForm()
    if form.validate_on_submit():
        new_contract = Contract(
            title=form.title.data,
            description=form.description.data,
            reward=form.reward.data,
            creator_id=current_user.id
        )
        db.session.add(new_contract)
        db.session.commit()
        flash('Contract created successfully!', 'success')
        return redirect(url_for('main.contracts'))
    return render_template('main/create_contract.html', title='Create Contract', form=form)


@main_bp.route('/contract/<int:contract_id>/complete', methods=['POST'])
@login_required
def complete_contract(contract_id):
    contract = Contract.query.get_or_404(contract_id)
    if contract.claimant_id != current_user.id:
        flash('You are not authorized to complete this contract.', 'danger')
        return redirect(url_for('main.contracts'))

    if contract.status != ContractStatus.CLAIMED:
        flash('This contract cannot be completed.', 'danger')
        return redirect(url_for('main.contracts'))

    # Transfer the reward to the claimant's account
    claimant_account = Account.query.filter_by(user_id=contract.claimant_id).first()
    if not claimant_account:
        flash('You do not have a bank account to receive the reward.', 'danger')
        return redirect(url_for('main.contracts'))

    claimant_account.balance += contract.reward
    transaction = Transaction(
        account_id=claimant_account.id,
        type=TransactionType.OTHER,
        amount=contract.reward,
        description=f"Reward for completing contract #{contract.id}: {contract.title}"
    )
    db.session.add(transaction)

    contract.status = ContractStatus.COMPLETED
    db.session.commit()

    flash('Contract completed successfully! The reward has been transferred to your account.', 'success')
    return redirect(url_for('main.contracts'))

