from flask import Blueprint, render_template, url_for, redirect, flash, request
from flask_login import current_user, login_required
from datetime import datetime
import mistune

from app import db
from app.decorators import admin_required, officer_required
from app.models import (
    User, UserRole, RulesContent, Farmer, Parcel, UserVehicle, CompanyVehicle,
    Account, InsuranceClaim, Contract, ContractStatus, Company, CompanyContract, CompanyInsuranceClaim,
    MarketplaceListing, MarketplaceListingStatus, Ticket, PermitApplication,
    Transaction, TransactionType, InsuranceRate, Fine, SiloStorage, InsuranceRateType
)
from app.forms import (
    ParcelForm, InsuranceClaimForm, ContractForm, CompanyNameForm, CompanyVehicleForm, CompanyContractForm, CompanyInsuranceClaimForm,
    ClockInForm, ClockOutForm
)
from app.services import vehicle_service

main_bp = Blueprint('main', __name__)


# ------------------------ HOME ------------------------

@main_bp.route('/', endpoint='index')
def main_index():
    return redirect(url_for('main.site_home'))


@main_bp.route('/site-home', endpoint='site_home')
def site_home():
    clock_in_form = ClockInForm()
    clock_out_form = ClockOutForm()

    # Generic data for all users
    recent_listings = MarketplaceListing.query \
        .filter_by(status=MarketplaceListingStatus.AVAILABLE) \
        .order_by(MarketplaceListing.creation_date.desc()) \
        .limit(4).all()
    announcements = [
        {
            'title': 'Welcome to Jays construction.',
            'content': 'We have redesigned the home page to be more informative and user-friendly.'
        },
        {
            'title': 'New Marketplace Items Available',
            'content': 'Check out the new items available in the marketplace. There are some great deals to be had!'
        },
    ]
    stats = {
        'active_players': User.query.count(),
        'open_tickets': Ticket.query.filter_by(status='OUTSTANDING').count(),
        'pending_permits': PermitApplication.query.filter_by(status='PENDING_REVIEW').count(),
    }
    insurance_rates = InsuranceRate.query.filter(InsuranceRate.rate_type == InsuranceRateType.FARM).order_by(InsuranceRate.rate_type).all()
    dynamic_rates = []
    
    for rate in insurance_rates:
        claims_count = InsuranceClaim.query.count()
        base_rate = float(rate.rate)
        rate_multiplier = 1 + (claims_count / 20.0) * 0.1
        new_rate = base_rate * rate_multiplier
        dynamic_rates.append({
            'rate_type': rate.rate_type,
            'name': rate.name,
            'description': rate.description,
            'rate': round(new_rate, 2),
            'claims_count': claims_count,
            'base_rate': base_rate
        })

    # Data for logged-in users
    farmer_data = {}
    company_data = {}
    if current_user.is_authenticated:
        if hasattr(current_user, 'farmer') and current_user.farmer:
            farmer = current_user.farmer
            farmer_data = {
                'parcels': Parcel.query.filter_by(farmer_id=farmer.id).all(),
                'silo_contents': SiloStorage.query.filter_by(farmer_id=farmer.id).order_by(SiloStorage.crop_type).all(),
                'insurance_claims': InsuranceClaim.query.filter_by(farmer_id=farmer.id).all(),
                'parcel_form': ParcelForm(),
                'insurance_form': InsuranceClaimForm()
            }
        elif hasattr(current_user, 'company') and current_user.company:
            company = current_user.company
            company_data = {
                'company': company,
                'vehicles': CompanyVehicle.query.filter_by(company_id=company.id).all(),
                'contracts': CompanyContract.query.filter_by(company_id=company.id).all(),
                'insurance_claims': CompanyInsuranceClaim.query.filter_by(company_id=company.id).all(),
                'vehicle_form': CompanyVehicleForm(),
                'contract_form': CompanyContractForm(),
                'insurance_form': CompanyInsuranceClaimForm()
            }

    return render_template('main/index.html', title='Home',
                           recent_listings=recent_listings,
                           announcements=announcements,
                           stats=stats,
                           insurance_rates=dynamic_rates,
                           clock_in_form=clock_in_form,
                           clock_out_form=clock_out_form,
                           farmer_data=farmer_data,
                           company_data=company_data)


# Create markdown parser once (reuse)
markdown_parser = mistune.create_markdown(escape=False)

# ------------------------ RULES ------------------------

@main_bp.route('/rules', endpoint='view_rules')
def view_rules():
    rules_entry = RulesContent.query.first()
    fines = Fine.query.order_by(Fine.name.asc()).all()

    if rules_entry and rules_entry.content_markdown:
        rules_content_html = markdown_parser(rules_entry.content_markdown)
    else:
        rules_content_html = "<p>The rules have not been set yet. Please check back later.</p>"
        if current_user.is_authenticated and current_user.role == UserRole.ADMIN:
            rules_content_html += f'<p><a href="{url_for("admin.edit_rules")}">Set the rules now.</a></p>'

    return render_template('main/rules.html', title='Rules',
                           rules_content_html=rules_content_html,
                           fines=fines,
                           current_user=current_user, UserRole=UserRole)


@main_bp.route('/fines', endpoint='fines')
def fines():
    fines = Fine.query.order_by(Fine.name.asc()).all()
    return render_template('main/fines.html', title='Fines', fines=fines)


@main_bp.route('/mods')
@login_required
def mods():
    """
    Renders the page for server mods and updates.
    Accessible only by logged-in users.
    """
    return render_template('main/mods.html', title='Mods & Updates')


# ------------------------ ADMIN ------------------------


@main_bp.route('/admin-dashboard')
@admin_required
def admin_dashboard():
    stats = {
        'total_users': User.query.count(),
        'pending_permits': PermitApplication.query.filter_by(status='PENDING_REVIEW').count(),
        'open_tickets': Ticket.query.filter_by(status='OUTSTANDING').count(),
          }
    return render_template('admin/dashboard.html', title='Admin Dashboard', stats=stats)


# ------------------------ OFFICER ------------------------

@main_bp.route('/officer-area')
@officer_required
def officer_area():
    return render_template('officer/area.html', title='Officer Area')

# ------------------------ COMPANY ------------------------

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


# ------------------------ CONTRACTS ------------------------

@main_bp.route('/contracts')
@login_required
def contracts():
    available_contracts = Contract.query.filter_by(status=ContractStatus.AVAILABLE).all()
    return render_template('main/contracts.html', title='Contracts', contracts=available_contracts)


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
    elif contract.claimant_id == current_user.id:
        flash('You have already claimed this contract.', 'info')
    else:
        flash('This contract is not available to be claimed.', 'danger')
    return redirect(request.referrer or url_for('main.contracts'))


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


# ------------------------ USER MANAGEMENT ------------------------

@main_bp.route('/users')
@admin_required
def users():
    all_users = User.query.all()
    return render_template('main/users.html', title='Users', users=all_users)
