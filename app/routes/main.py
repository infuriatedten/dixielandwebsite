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
    Transaction, TransactionType, InsuranceRate, Fine, SiloStorage
)
from app.forms import (
    ParcelForm, InsuranceClaimForm, ContractForm, CompanyNameForm, CompanyVehicleForm, CompanyContractForm, CompanyInsuranceClaimForm
)

main_bp = Blueprint('main', __name__)


# ------------------------ HOME ------------------------

@main_bp.route('/', endpoint='index')
def main_index():
    if current_user.is_authenticated:
        if hasattr(current_user, 'farmer') and current_user.farmer:
            return redirect(url_for('main.farmer_dashboard'))
        elif hasattr(current_user, 'company') and current_user.company:
            return redirect(url_for('main.company_dashboard'))

    recent_listings = MarketplaceListing.query \
        .filter_by(status=MarketplaceListingStatus.AVAILABLE) \
        .order_by(MarketplaceListing.creation_date.desc()) \
        .limit(4).all()

    announcements = [
        {
            'title': 'Welcome to the new and improved Game Portal!',
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

    insurance_rates = InsuranceRate.query.order_by(InsuranceRate.rate_type).all()
    dynamic_rates = []
    for rate in insurance_rates:
        new_rate = float(rate.rate) * (1 + (rate.payout_requests / 10))
        dynamic_rates.append({
            'rate_type': rate.rate_type,
            'name': rate.name,
            'description': rate.description,
            'rate': new_rate
        })

    return render_template('main/index.html', title='Home',
                           recent_listings=recent_listings,
                           announcements=announcements,
                           stats=stats,
                           insurance_rates=dynamic_rates)


@main_bp.route('/site-home', endpoint='site_home')
def site_home():
    recent_listings = MarketplaceListing.query \
        .filter_by(status=MarketplaceListingStatus.AVAILABLE) \
        .order_by(MarketplaceListing.creation_date.desc()) \
        .limit(4).all()

    announcements = [
        {
            'title': 'Welcome to the new and improved Game Portal!',
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

    insurance_rates = InsuranceRate.query.order_by(InsuranceRate.rate_type).all()
    dynamic_rates = []
    for rate in insurance_rates:
        new_rate = float(rate.rate) * (1 + (rate.payout_requests / 10))
        dynamic_rates.append({
            'rate_type': rate.rate_type,
            'name': rate.name,
            'description': rate.description,
            'rate': new_rate
        })

    return render_template('main/index.html', title='Home',
                           recent_listings=recent_listings,
                           announcements=announcements,
                           stats=stats,
                           insurance_rates=dynamic_rates)


# Create markdown parser once (reuse)
markdown_parser = mistune.create_markdown(escape=False)

# ------------------------ RULES ------------------------

@main_bp.route('/rules', endpoint='view_rules')
def view_rules():
    rules_entry = RulesContent.query.first()

    if rules_entry and rules_entry.content_markdown:
        rules_content_html = markdown_parser(rules_entry.content_markdown)
    else:
        rules_content_html = "<p>The rules have not been set yet. Please check back later.</p>"
        if current_user.is_authenticated and current_user.role == UserRole.ADMIN:
            rules_content_html += f'<p><a href="{url_for("admin.edit_rules")}">Set the rules now.</a></p>'

    return render_template('main/rules.html', title='Rules',
                           rules_content_html=rules_content_html,
                           current_user=current_user, UserRole=UserRole)


@main_bp.route('/fines', endpoint='fines')
def fines():
    fines = Fine.query.order_by(Fine.name.asc()).all()
    return render_template('main/fines.html', title='Fines', fines=fines)


# ------------------------ ADMIN ------------------------


@main_bp.route('/admin-dashboard')
@admin_required
def admin_dashboard():
    stats = {
        'total_users': User.query.count(),
        'pending_permits': PermitApplication.query.filter_by(status='PENDING_REVIEW').count(),
        'open_tickets': Ticket.query.filter_by(status='OUTSTANDING').count(),
        'revenue': 0  # TODO: Implement revenue logic
    }
    return render_template('admin/dashboard.html', title='Admin Dashboard', stats=stats)


# ------------------------ OFFICER ------------------------

@main_bp.route('/officer-area')
@officer_required
def officer_area():
    return render_template('officer/area.html', title='Officer Area')
# ------------------------ FARMERS ------------------------

@main_bp.route('/farmer-dashboard', methods=['GET', 'POST'])
@login_required
def farmer_dashboard():
    bank_accounts = Account.query.filter_by(user_id=current_user.id).all()
    farmer = Farmer.query.filter_by(user_id=current_user.id).first()
    parcels = Parcel.query.filter_by(farmer_id=farmer.id).all() if farmer else []
    silo_contents = SiloStorage.query.filter_by(farmer_id=farmer.id).order_by(SiloStorage.crop_type).all() if farmer else []
    vehicles = UserVehicle.query.filter_by(user_id=current_user.id).all()
    tickets = Ticket.query.filter_by(issued_to_user_id=current_user.id).all()
    insurance_claims = InsuranceClaim.query.filter_by(farmer_id=farmer.id).all() if farmer else []
    parcel_form = ParcelForm()
    insurance_form = InsuranceClaimForm()

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
        return redirect(url_for('main.farmer_dashboard'))

    if insurance_form.validate_on_submit() and insurance_form.submit.data:
        if farmer:
            claim = InsuranceClaim(
                reason=insurance_form.reason.data,
                farmer_id=farmer.id
            )
            db.session.add(claim)

            rate_to_update = InsuranceRate.query.filter_by(name=insurance_form.reason.data).first()
            if rate_to_update:
                rate_to_update.payout_requests += 1

            db.session.commit()
            flash('Insurance claim submitted successfully!', 'success')
        else:
            flash('You must be a registered farmer to submit a claim.', 'danger')
        return redirect(url_for('main.farmer_dashboard'))

    return render_template(
        'main/farmer_dashboard.html',
        title='Farmer Dashboard',
        bank_accounts=bank_accounts,
        parcels=parcels,
        vehicles=vehicles,
        tickets=tickets,
        insurance_claims=insurance_claims,
        parcel_form=parcel_form,
        insurance_form=insurance_form,
        silo_contents=silo_contents
    )



# ------------------------ COMPANY ------------------------
@main_bp.route('/company-dashboard', methods=['GET', 'POST'])
@login_required
def company_dashboard():
    company = Company.query.filter_by(user_id=current_user.id).first()
    if not company:
        flash('You do not have a company.', 'danger')
        return redirect(url_for('main.index'))

    bank_accounts = Account.query.filter_by(user_id=current_user.id).all()
    vehicles = CompanyVehicle.query.filter_by(company_id=company.id).all()
    tickets = Ticket.query.filter_by(issued_to_user_id=current_user.id).all()
    contracts = CompanyContract.query.filter_by(company_id=company.id).all()
    insurance_claims = CompanyInsuranceClaim.query.filter_by(company_id=company.id).all()

    vehicle_form = CompanyVehicleForm()
    contract_form = CompanyContractForm()
    insurance_form = CompanyInsuranceClaimForm()

    if vehicle_form.validate_on_submit() and vehicle_form.submit.data:
        new_vehicle = CompanyVehicle(
            company_id=company.id,
            vehicle_make=vehicle_form.vehicle_make.data,
            vehicle_model=vehicle_form.vehicle_model.data,
            vehicle_type=vehicle_form.vehicle_type.data,
            vehicle_description=vehicle_form.vehicle_description.data,
            license_plate=f"{vehicle_form.region_format.data}-{company.name.upper()}-{len(vehicles) + 1}",
            region_format=vehicle_form.region_format.data
        )
        db.session.add(new_vehicle)
        db.session.commit()
        flash('Vehicle registered successfully!', 'success')
        return redirect(url_for('main.company_dashboard'))

    if contract_form.validate_on_submit() and contract_form.submit.data:
        new_contract = CompanyContract(
            title=contract_form.title.data,
            description=contract_form.description.data,
            reward=contract_form.reward.data,
            company_id=company.id
        )
        db.session.add(new_contract)
        db.session.commit()
        flash('Contract created successfully!', 'success')
        return redirect(url_for('main.company_dashboard'))

    if insurance_form.validate_on_submit() and insurance_form.submit.data:
        claim = CompanyInsuranceClaim(
            reason=insurance_form.reason.data,
            company_id=company.id
        )
        db.session.add(claim)
        db.session.commit()
        flash('Insurance claim submitted successfully!', 'success')
        return redirect(url_for('main.company_dashboard'))

    return render_template(
        'main/company_dashboard.html',
        title='Company Dashboard',
        company=company,
        bank_accounts=bank_accounts,
        vehicles=vehicles,
        tickets=tickets,
        contracts=contracts,
        insurance_claims=insurance_claims,
        vehicle_form=vehicle_form,
        contract_form=contract_form,
        insurance_form=insurance_form
    )

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
