from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import current_user, login_required
from app import db
from app.models import User, UserRole, Ticket, TicketStatus, Account, Transaction, TransactionType
from app.forms import IssueTicketForm, ContestTicketForm # ResolveTicketForm will be on admin side
from app.decorators import officer_required, admin_required # officer_required for issuing
from datetime import datetime, timedelta
from decimal import Decimal

bp = Blueprint('dot', __name__)

# --- Officer Routes ---
@bp.route('/issue_ticket', methods=['GET', 'POST'])
@login_required
@officer_required # Ensures only OFFICERS or ADMINS can access
def issue_ticket():
    form = IssueTicketForm()
    if form.validate_on_submit():
        # Find the user to ticket
        user_to_ticket = User.query.filter(User.username.ilike(form.user_search.data)).first()
        if not user_to_ticket:
            flash(f"User '{form.user_search.data}' not found.", 'danger')
            return render_template('dot/issue_ticket.html', title='Issue New Ticket', form=form)

        if user_to_ticket.id == current_user.id:
            flash("You cannot issue a ticket to yourself.", "danger")
            return redirect(url_for('dot.issue_ticket'))

        if user_to_ticket.role == UserRole.ADMIN or user_to_ticket.role == UserRole.OFFICER :
             if current_user.role != UserRole.ADMIN: # Officers cannot ticket other officers/admins
                flash("Officers cannot issue tickets to other officers or administrators.", "warning")
                return redirect(url_for('dot.issue_ticket'))


        issue_dt = datetime.utcnow()
        due_dt = issue_dt + timedelta(hours=72)

        new_ticket = Ticket(
            issued_to_user_id=user_to_ticket.id,
            issued_by_officer_id=current_user.id,
            vehicle_id=form.vehicle_id.data,
            violation_details=form.violation_details.data,
            fine_amount=form.fine_amount.data,
            issue_date=issue_dt,
            due_date=due_dt,
            status=TicketStatus.OUTSTANDING
        )
        db.session.add(new_ticket)
        db.session.commit() # Commit first to get new_ticket.id
        flash(f'Ticket #{new_ticket.id} issued successfully to {user_to_ticket.username}. Due by {due_dt.strftime("%Y-%m-%d %H:%M:%S UTC")}.', 'success')

        # Notify user
        from app.services import notification_service # Ensure import
        from app.models import NotificationType # Ensure import
        notification_service.notify_new_ticket_issued(new_ticket) # Use helper from service

        return redirect(url_for('dot.list_issued_tickets')) # Or a general DOT dashboard

    return render_template('dot/issue_ticket.html', title='Issue New Ticket', form=form)

@bp.route('/issued_tickets')
@login_required
@officer_required
def list_issued_tickets():
    page = request.args.get('page', 1, type=int)
    # Officers see tickets they issued. Admins see all if they use this route.
    query = Ticket.query
    if current_user.role == UserRole.OFFICER:
        query = query.filter_by(issued_by_officer_id=current_user.id)

    tickets_pagination = query.order_by(Ticket.issue_date.desc()).paginate(page=page, per_page=10)
    return render_template('dot/list_issued_tickets.html', title='My Issued Tickets', tickets_pagination=tickets_pagination)


# --- User Routes for Tickets ---
@bp.route('/my_tickets')
@login_required
def my_tickets():
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', None)

    query = Ticket.query.filter_by(issued_to_user_id=current_user.id)

    if status_filter and hasattr(TicketStatus, status_filter.upper()):
        query = query.filter_by(status=TicketStatus[status_filter.upper()])

    tickets_pagination = query.order_by(Ticket.issue_date.desc()).paginate(page=page, per_page=10)
    return render_template('dot/my_tickets.html', title='My Tickets',
                           tickets_pagination=tickets_pagination,
                           TicketStatus=TicketStatus, # Pass enum for template use
                           current_status_filter=status_filter)


@bp.route('/ticket/<int:ticket_id>/pay', methods=['POST'])
@login_required
def pay_ticket(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    if ticket.issued_to_user_id != current_user.id:
        flash('You are not authorized to pay this ticket.', 'danger')
        return redirect(url_for('dot.my_tickets'))

    if ticket.status not in [TicketStatus.OUTSTANDING, TicketStatus.RESOLVED_UNPAID]:
        flash(f'This ticket is not currently payable (Status: {ticket.status.value}).', 'warning')
        return redirect(url_for('dot.view_ticket_detail', ticket_id=ticket.id))

    user_account = Account.query.filter_by(user_id=current_user.id).first()
    if not user_account:
        flash('You do not have a bank account to make this payment.', 'danger')
        return redirect(url_for('dot.view_ticket_detail', ticket_id=ticket.id))

    if user_account.balance < ticket.fine_amount:
        flash(f'Insufficient funds. You need {ticket.fine_amount} {user_account.currency}, but have {user_account.balance} {user_account.currency}.', 'danger')
        return redirect(url_for('dot.view_ticket_detail', ticket_id=ticket.id))

    try:
        payment_transaction = Transaction(
            account_id=user_account.id,
            type=TransactionType.TICKET_PAYMENT,
            amount=-ticket.fine_amount, # Negative for deduction
            description=f"Payment for Ticket #{ticket.id}"
        )
        db.session.add(payment_transaction)

        user_account.balance -= ticket.fine_amount
        db.session.add(user_account)

        ticket.status = TicketStatus.PAID
        ticket.banking_transaction_id = payment_transaction.id # Link after flush/commit
        db.session.add(ticket)

        # Need to flush to get payment_transaction.id before assigning to ticket if not deferred
        db.session.flush()
        ticket.banking_transaction_id = payment_transaction.id

        db.session.commit()
        flash(f'Ticket #{ticket.id} paid successfully. {ticket.fine_amount} {user_account.currency} deducted from your account.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error processing payment for ticket #{ticket.id}: {str(e)}', 'danger')

    return redirect(url_for('dot.view_ticket_detail', ticket_id=ticket.id))


@bp.route('/ticket/<int:ticket_id>/contest', methods=['GET', 'POST'])
@login_required
def contest_ticket(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    if ticket.issued_to_user_id != current_user.id:
        flash('You are not authorized to contest this ticket.', 'danger')
        return redirect(url_for('dot.my_tickets'))

    if ticket.status != TicketStatus.OUTSTANDING:
        flash(f'This ticket cannot be contested at this time (Status: {ticket.status.value}).', 'warning')
        return redirect(url_for('dot.view_ticket_detail', ticket_id=ticket.id))

    form = ContestTicketForm()
    if form.validate_on_submit():
        ticket.status = TicketStatus.CONTESTED
        ticket.user_contest_reason = form.user_contest_reason.data
        db.session.commit()
        flash(f'Ticket #{ticket.id} has been marked as contested. An admin will review your reason.', 'info')
        # TODO: Notify admins/relevant officer
        return redirect(url_for('dot.view_ticket_detail', ticket_id=ticket.id))

    return render_template('dot/contest_ticket.html', title=f'Contest Ticket #{ticket.id}', form=form, ticket=ticket)


@bp.route('/ticket/<int:ticket_id>')
@login_required
def view_ticket_detail(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    # User can view their own tickets. Officers/Admins can view any ticket (or tickets they issued for officers).
    if ticket.issued_to_user_id != current_user.id and \
       (current_user.role not in [UserRole.ADMIN, UserRole.OFFICER] or \
        (current_user.role == UserRole.OFFICER and ticket.issued_by_officer_id != current_user.id)): # Officer can only view their own issued tickets unless admin
        flash('You are not authorized to view this ticket detail.', 'danger')
        if current_user.role == UserRole.OFFICER:
            return redirect(url_for('dot.list_issued_tickets'))
        else: # Regular user trying to access someone else's ticket
            return redirect(url_for('dot.my_tickets'))

    return render_template('dot/view_ticket_detail.html', title=f'Ticket #{ticket.id} Details', ticket=ticket, TicketStatus=TicketStatus)


# --- Permit Application Routes (User Facing) ---
from app.models import PermitApplication, PermitApplicationStatus # Import new models
from app.forms import ApplyPermitForm # Import new form
import uuid # For generating unique permit ID string

from datetime import datetime

@bp.route('/permits/apply', methods=['GET', 'POST'])
@login_required
def apply_for_permit():
    form = ApplyPermitForm()
    if form.validate_on_submit():
        new_application = PermitApplication(
            user_id=current_user.id,
            vehicle_type=form.vehicle_type.data,
            route_details=form.route_details.data,
            travel_start_date=form.travel_start_date.data,
            travel_end_date=form.travel_end_date.data,
            user_notes=form.user_notes.data,
            application_date=datetime.utcnow(),
            status=PermitApplicationStatus.PENDING_REVIEW
        )
        db.session.add(new_application)
        db.session.commit()
        flash('Your permit application has been submitted successfully and is pending review.', 'success')
        # TODO: Notify relevant officers/admins
        return redirect(url_for('dot.my_permit_applications'))

    return render_template('dot/apply_permit.html', title='Apply for Vehicle Movement Permit', form=form)


@bp.route('/permits/my_applications')
@login_required
def my_permit_applications():
    page = request.args.get('page', 1, type=int)
    applications_pagination = PermitApplication.query.filter_by(user_id=current_user.id)\
                                       .order_by(PermitApplication.application_date.desc())\
                                       .paginate(page=page, per_page=10)
    return render_template('dot/my_permit_applications.html', title='My Permit Applications',
                           applications_pagination=applications_pagination,
                           PermitApplicationStatus=PermitApplicationStatus)


@bp.route('/permits/application/<int:application_id>')
@login_required
def view_permit_application_detail(application_id):
    application = PermitApplication.query.get_or_404(application_id)

    # Determine permissions
    is_owner = (application.user_id == current_user.id)
    is_admin = (current_user.role == UserRole.ADMIN)
    can_officer_view = (
        current_user.role == UserRole.OFFICER and
        (application.reviewed_by_officer_id == current_user.id or application.status == PermitApplicationStatus.PENDING_REVIEW)
    )

    if not (is_owner or can_officer_view or is_admin):
        flash('You are not authorized to view this permit application.', 'danger')
        # Redirect owners to their permit apps, others to main index or dashboard
        return redirect(url_for('dot.my_permit_applications') if is_owner else url_for('main.index'))

    return render_template(
        'dot/view_permit_application_detail.html',
        title=f'Permit Application #{application.id}',
        application=application,
        PermitApplicationStatus=PermitApplicationStatus
    )



@bp.route('/permits/application/<int:application_id>/pay', methods=['POST'])
@login_required
def pay_for_permit(application_id):
    application = PermitApplication.query.get_or_404(application_id)

    # Authorization check
    if application.user_id != current_user.id:
        flash('You are not authorized to pay for this permit.', 'danger')
        return redirect(url_for('dot.my_permit_applications'))

    # Status check
    if application.status != PermitApplicationStatus.APPROVED_PENDING_PAYMENT:
        flash(
            f'This permit application is not currently awaiting payment '
            f'(Status: {application.status.value}).',
            'warning'
        )
        return redirect(url_for('dot.view_permit_application_detail', application_id=application.id))

    # Permit fee validation
    if not application.permit_fee or application.permit_fee <= 0:
        flash('Permit fee is not set or invalid. Please contact an administrator.', 'danger')
        return redirect(url_for('dot.view_permit_application_detail', application_id=application.id))

    # Get user account — assume one account per user for consistency
    user_account = current_user.accounts.first()
    if not user_account:
        flash('You do not have a bank account to make this payment.', 'danger')
        return redirect(url_for('dot.view_permit_application_detail', application_id=application.id))

    # Balance check
    if user_account.balance < application.permit_fee:
        flash(
            f'Insufficient funds. You need {application.permit_fee} {user_account.currency}, '
            f'but have {user_account.balance} {user_account.currency}.',
            'danger'
        )
        return redirect(url_for('dot.view_permit_application_detail', application_id=application.id))

    try:
        # Create transaction record
        payment_transaction = Transaction(
            account_id=user_account.id,
            type=TransactionType.PERMIT_FEE_PAYMENT,
            amount=-application.permit_fee,  # negative to deduct
            description=f"Payment for Permit Application #{application.id}"
        )
        db.session.add(payment_transaction)

        # Deduct fee from account balance
        user_account.balance -= application.permit_fee
        db.session.add(user_account)

        # Update application status & link transaction
        application.status = PermitApplicationStatus.PAID_AWAITING_ISSUANCE
        db.session.flush()  # assign ID to payment_transaction
        application.banking_transaction_id = payment_transaction.id
        db.session.add(application)

        db.session.commit()
        flash(
            f'Permit fee of {application.permit_fee} {user_account.currency} paid successfully '
            f'for Application #{application.id}. Awaiting final issuance.',
            'success'
        )
    except Exception as e:
        db.session.rollback()
        flash(f'Error processing payment: {str(e)}', 'danger')

    return redirect(url_for('dot.view_permit_application_detail', application_id=application.id))



@bp.route('/permits/application/<int:application_id>/cancel_by_user', methods=['POST'])
@login_required
def cancel_permit_application_by_user(application_id):
    application = PermitApplication.query.get_or_404(application_id)
    
    if application.user_id != current_user.id:
        flash('You are not authorized to cancel this application.', 'danger')
        return redirect(url_for('dot.my_permit_applications'))

    allowed_statuses = [PermitApplicationStatus.PENDING_REVIEW, PermitApplicationStatus.REQUIRES_MODIFICATION]
    if application.status not in allowed_statuses:
        flash(
            f'This application cannot be cancelled by you at its current status: {application.status.value}.',
            'warning'
        )
        return redirect(url_for('dot.view_permit_application_detail', application_id=application.id))

    application.status = PermitApplicationStatus.CANCELLED_BY_USER
    application.officer_notes = (
        (application.officer_notes or "") + 
        f"\nApplication cancelled by user on {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}."
    )
    db.session.commit()
    flash(f'Permit Application #{application.id} has been cancelled.', 'info')
    return redirect(url_for('dot.my_permit_applications'))



# --- Officer/Admin Permit Management Routes (Placeholder - to be expanded) ---
from app.forms import ReviewPermitApplicationForm

@bp.route('/permits/review_list')
@login_required
@officer_required # Or admin_required if it's an admin-only overview
def review_permit_applications_list():
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', 'PENDING_REVIEW') # Default to pending review

    query = PermitApplication.query
    if status_filter and hasattr(PermitApplicationStatus, status_filter.upper()):
        query = query.filter_by(status=PermitApplicationStatus[status_filter.upper()])

    applications_pagination = query.order_by(PermitApplication.application_date.asc()).paginate(page=page, per_page=10) # Oldest first
    return render_template('dot/review_permit_applications_list.html', title='Review Permit Applications',
                           applications_pagination=applications_pagination,
                           PermitApplicationStatus=PermitApplicationStatus,
                           current_status_filter=status_filter)


@bp.route('/permits/review/<int:application_id>', methods=['GET', 'POST'])
@login_required
@officer_required # Admins are also officers via decorator logic
def review_permit_application(application_id):
    application = PermitApplication.query.get_or_404(application_id)
    form = ReviewPermitApplicationForm(obj=application) # Pre-populate with existing data if any (e.g. notes)

    # Customize choices for the form based on current status, for example:
    current_status = application.status
    available_statuses = []
    if current_status == PermitApplicationStatus.PENDING_REVIEW:
        available_statuses = [
            (PermitApplicationStatus.APPROVED_PENDING_PAYMENT.value, "Approve (Set Fee, Awaiting Payment)"),
            (PermitApplicationStatus.REQUIRES_MODIFICATION.value, "Requires Modification (Send to User)"),
            (PermitApplicationStatus.REJECTED.value, "Reject Application")
        ]
    elif current_status == PermitApplicationStatus.REQUIRES_MODIFICATION: # If user resubmits, it might come back to PENDING_REVIEW
         available_statuses = [ # Or officer can directly approve after user edits
            (PermitApplicationStatus.APPROVED_PENDING_PAYMENT.value, "Approve (Set Fee, Awaiting Payment)"),
            (PermitApplicationStatus.REJECTED.value, "Reject Application")
        ]
    # Add more logic for other statuses if officer can change them (e.g. CANCELLED_BY_ADMIN)
    form.new_status.choices = available_statuses


    if form.validate_on_submit():
        new_status_val = form.new_status.data
        new_status_enum = PermitApplicationStatus(new_status_val)

        application.status = new_status_enum
        application.officer_notes = form.officer_notes.data
        application.reviewed_by_officer_id = current_user.id

        if new_status_enum == PermitApplicationStatus.APPROVED_PENDING_PAYMENT:
            if form.permit_fee.data and form.permit_fee.data > 0:
                application.permit_fee = form.permit_fee.data
            else: # Should be caught by form validation, but as a safeguard
                flash("A valid permit fee must be set when approving.", "danger")
                return render_template('dot/review_permit_application.html', title=f'Review Permit App #{application.id}',
                               form=form, application=application, PermitApplicationStatus=PermitApplicationStatus)
        else: # If not approving, ensure fee is cleared or handled appropriately
            application.permit_fee = None

        db.session.commit()
        flash(f'Permit Application #{application.id} status updated to "{new_status_enum.value}".', 'success')

        # Notify user of status change
        from app.services import notification_service # Ensure import
        from app.models import NotificationType # Ensure import, PermitApplicationStatus
        if new_status_enum == PermitApplicationStatus.APPROVED_PENDING_PAYMENT:
            notification_service.notify_permit_approved(application)
        elif new_status_enum == PermitApplicationStatus.REJECTED:
            notification_service.notify_permit_denied(application)
        elif new_status_enum == PermitApplicationStatus.REQUIRES_MODIFICATION:
            # Create a generic notification or a specific one for requires modification
            notification_service.create_notification(
                user_id=application.user_id,
                message_text=f"Your Permit Application #{application.id} ('{application.vehicle_type}') requires modification. Officer notes: {application.officer_notes[:100]}...",
                link_url=url_for('dot.view_permit_application_detail', application_id=application.id, _external=False), # Internal link
                notification_type=NotificationType.GENERAL_INFO # Or a new specific type
            )

        return redirect(url_for('dot.review_permit_applications_list'))

    return render_template('dot/process_permit_application.html', title=f'Process Permit App #{application.id}',
                           form=form, application=application, PermitApplicationStatus=PermitApplicationStatus)


@bp.route('/permits/application/<int:application_id>/issue_final', methods=['POST'])
@login_required
@officer_required
def issue_final_permit(application_id):
    application = PermitApplication.query.get_or_404(application_id)
    
    if application.status != PermitApplicationStatus.PAID_AWAITING_ISSUANCE:
        flash(
            "This permit application is not ready for final issuance (must be 'Paid - Awaiting Issuance').",
            "warning"
        )
        return redirect(url_for('dot.list_permit_applications_for_review'))

    # Generate Permit ID: Two options:
    # Option 1: Year + zero-padded application ID + suffix (e.g., 2025-00042-P)
    year = datetime.utcnow().year
    sequential_part = str(application.id).zfill(5)
    permit_id = f"{year}-{sequential_part}-P"
    
    # Option 2: Use UUID for uniqueness if you want
    # permit_id = f"PERMIT-{datetime.utcnow().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
    
    application.issued_permit_id_str = permit_id
    application.status = PermitApplicationStatus.ISSUED
    application.issued_on_date = datetime.utcnow()
    application.issued_by_officer_id = current_user.id

    application.officer_notes = (
        (application.officer_notes or "") + 
        f"\nPermit issued by {current_user.username} on {application.issued_on_date.strftime('%Y-%m-%d %H:%M')} with ID: {permit_id}."
    )

    db.session.commit()
    flash(f"Permit #{permit_id} has been officially issued for Application #{application.id}.", "success")
    # TODO: Notify user that their permit is issued and available.

    return redirect(url_for('dot.view_permit_application_detail', application_id=application.id))



# --- DOT Inspection Routes (Officer Facing) ---
from app.forms import RecordInspectionForm, IssueTicketForm # Added IssueTicketForm
from app.models import Inspection, UserVehicle # Already imported User, UserRole, Ticket, TicketStatus etc.

@bp.route('/inspections/record', methods=['GET', 'POST'])
@login_required
@officer_required
def record_inspection():
    form = RecordInspectionForm()
    if form.validate_on_submit():
        inspected_user = None
        if form.inspected_user_search.data:
            inspected_user = User.query.filter(User.username.ilike(form.inspected_user_search.data)).first()
            if not inspected_user:
                flash(f"Inspected user '{form.inspected_user_search.data}' not found. Proceeding without linking user.", 'warning')
            # Consider if officer should be blocked if user not found, or if non-registered users can be inspected.
            # Current model allows nullable inspected_user_id.

        pass_status_bool = form.pass_status.data == 'True'

        new_inspection = Inspection(
            officer_user_id=current_user.id,
            inspected_user_id=inspected_user.id if inspected_user else None,
            vehicle_id=form.vehicle_id.data,
            pass_status=pass_status_bool,
            notes=form.notes.data,
            timestamp=datetime.utcnow() # Explicitly set, though model has default
        )
        db.session.add(new_inspection)
        db.session.commit()
        flash(f'Inspection for vehicle {new_inspection.vehicle_id} recorded successfully (Result: {"Pass" if pass_status_bool else "Fail"}).', 'success')
        return redirect(url_for('dot.view_inspection_detail', inspection_id=new_inspection.id))

    return render_template('dot/record_inspection.html', title='Record Vehicle Inspection', form=form)


@bp.route('/inspections/my_conducted')
@login_required
@officer_required
def list_my_conducted_inspections():
    page = request.args.get('page', 1, type=int)
    inspections_pagination = Inspection.query.filter_by(officer_user_id=current_user.id)\
                                        .order_by(Inspection.timestamp.desc())\
                                        .paginate(page=page, per_page=10)
    return render_template('dot/list_my_conducted_inspections.html',
                           title='My Conducted Inspections',
                           inspections_pagination=inspections_pagination)


@bp.route('/inspections/<int:inspection_id>')
@login_required # User could see their own, officer their own, admin all.
def view_inspection_detail(inspection_id):
    inspection = Inspection.query.get_or_404(inspection_id)

    # Authorization:
    # 1. Admin can see all.
    # 2. Officer can see inspections they conducted.
    # 3. User can see inspections where they were the inspected_user_id (TODO for user visibility feature)

    can_view = False
    if current_user.role == UserRole.ADMIN:
        can_view = True
    elif current_user.role == UserRole.OFFICER and inspection.officer_user_id == current_user.id:
        can_view = True
    elif inspection.inspected_user_id == current_user.id: # For future user visibility
        can_view = True # Or redirect to a user-specific view

    if not can_view:
        flash('You are not authorized to view this inspection record.', 'danger')
        if current_user.role == UserRole.OFFICER:
            return redirect(url_for('dot.list_my_conducted_inspections'))
        # Add redirects for other roles or a general home if user visibility is not yet for them
        return redirect(url_for('main.index'))

    return render_template('dot/view_inspection_detail.html',
                           title=f'Inspection Details #{inspection.id}',
                           inspection=inspection)


# --- Permit Application Routes (User Facing) ---
from app.forms import ApplyPermitForm #, ReviewPermitApplicationForm (for officer/admin side)
from app.models import PermitApplication, PermitApplicationStatus #, Account, Transaction, TransactionType (already imported)
import uuid # For generating initial unique part of permit ID

# --- Officer/Admin Permit Management Routes (can be in dot_bp or admin_bp) ---
# For now, let's add a basic review list here, more advanced admin views can be in admin_bp
from app.forms import ReviewPermitApplicationForm

@bp.route('/permits/review_list')
@login_required
@officer_required # Admins can also access due to decorator logic
def list_permit_applications_for_review():
    page = request.args.get('page', 1, type=int)
    # Officers see PENDING_REVIEW or those they are assigned to review (if assignment logic is added)
    # Admins would see all. For now, simple view for officers:
    query = PermitApplication.query.filter(
        PermitApplication.status.in_([
            PermitApplicationStatus.PENDING_REVIEW,
            PermitApplicationStatus.REQUIRES_MODIFICATION, # If officer needs to re-review after user edits
            PermitApplicationStatus.PAID_AWAITING_ISSUANCE # For final issuance step
        ])
    )
    # TODO: If a system assigns applications to specific officers, filter by that.
    # query = query.filter(or_(PermitApplication.reviewed_by_officer_id == current_user.id, PermitApplication.reviewed_by_officer_id == None))

    applications_pagination = query.order_by(PermitApplication.application_date.asc()).paginate(page=page, per_page=10)
    return render_template('dot/list_permit_applications_review.html',
                           title='Permit Applications for Review/Issuance',
                           applications_pagination=applications_pagination,
                           PermitApplicationStatus=PermitApplicationStatus)


@bp.route('/permits/process_application/<int:application_id>', methods=['GET', 'POST'])
@login_required
@officer_required
def process_permit_application(application_id):
    application = PermitApplication.query.get_or_404(application_id)
    form = ReviewPermitApplicationForm(obj=application) # Pre-populate with existing data if any

    # Customize form choices based on current status
    current_status = application.status
    if current_status == PermitApplicationStatus.PENDING_REVIEW or current_status == PermitApplicationStatus.REQUIRES_MODIFICATION:
        form.new_status.choices = [
            (PermitApplicationStatus.APPROVED_PENDING_PAYMENT.value, "Approve (Set Fee, Awaiting Payment)"),
            (PermitApplicationStatus.REQUIRES_MODIFICATION.value, "Requires User Modification (Send Back)"),
            (PermitApplicationStatus.REJECTED.value, "Reject Application"),
        ]
    elif current_status == PermitApplicationStatus.PAID_AWAITING_ISSUANCE:
         # This state is for final issuance, not fee setting.
         # The form might not be ideal here, direct "Issue Permit" button might be better.
         # Or a simplified form for just notes + issue button.
         # For now, we'll skip form validation if just issuing.
         pass # Handled by specific 'issue' route/button later
    else:
        flash(f"Application is in status '{current_status.value}' and cannot be processed this way.", "warning")
        return redirect(url_for('dot.list_permit_applications_for_review'))


    if form.validate_on_submit() and current_status not in [PermitApplicationStatus.PAID_AWAITING_ISSUANCE]:
        new_status_enum = PermitApplicationStatus(form.new_status.data)

        application.status = new_status_enum
        application.officer_notes = form.officer_notes.data
        application.reviewed_by_officer_id = current_user.id

        if new_status_enum == PermitApplicationStatus.APPROVED_PENDING_PAYMENT:
            application.permit_fee = form.permit_fee.data
            if not application.permit_fee or application.permit_fee <= 0:
                flash("A positive permit fee must be set when approving.", "danger")
                # This should be caught by form validator, but double check.
                return render_template('dot/process_permit_application.html', title=f'Process Permit App #{application.id}', form=form, application=application, PermitApplicationStatus=PermitApplicationStatus)

        db.session.commit()
        flash(f'Permit Application #{application.id} updated to {new_status_enum.value}.', 'success')
        # TODO: Notify user of status change, especially if REQUIRES_MODIFICATION or APPROVED
        return redirect(url_for('dot.list_permit_applications_for_review'))

    return render_template('dot/process_permit_application.html',
                           title=f'Process Permit App #{application.id}',
                           form=form, application=application,
                           PermitApplicationStatus=PermitApplicationStatus)



