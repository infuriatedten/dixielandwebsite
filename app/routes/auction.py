from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app as app_flask
from flask_login import current_user, login_required
from app import db
from app.models import User, UserRole, Account, Transaction, TransactionType, \
                     AuctionItem, AuctionBid, AuctionStatus
from app.forms import SubmitAuctionItemForm, ApproveAuctionItemForm, PlaceBidForm
from app.decorators import admin_required, login_required # Ensure login_required is consistently used
from datetime import datetime, timedelta
from decimal import Decimal

auction_bp = Blueprint('auction', __name__)

# --- User Facing Auction Routes ---

@auction_bp.route('/')
def index():
    """Public listing of active auctions."""
    page = request.args.get('page', 1, type=int)
    active_auctions = AuctionItem.query.filter_by(status=AuctionStatus.ACTIVE)\
                                     .order_by(AuctionItem.current_end_time.asc())\
                                     .paginate(page=page, per_page=10) # Configurable per_page
    return render_template('auction/auction_list.html', title='Active Auctions',
                           auctions=active_auctions, AuctionStatus=AuctionStatus)


@auction_bp.route('/submit', methods=['GET', 'POST'])
@login_required
def submit_auction_item():
    form = SubmitAuctionItemForm()
    if form.validate_on_submit():
        new_item = AuctionItem(
            submitter_user_id=current_user.id,
            item_name=form.item_name.data,
            item_description=form.item_description.data,
            suggested_starting_bid=form.suggested_starting_bid.data,
            image_url=form.image_url.data,
            status=AuctionStatus.PENDING_APPROVAL,
            submission_time=datetime.utcnow()
        )
        db.session.add(new_item)
        db.session.commit()
        flash('Your item has been submitted for auction and is pending admin approval.', 'success')
        # TODO: Notify admins of new pending auction
        return redirect(url_for('auction.my_submissions'))
    return render_template('auction/submit_item.html', title='Submit Item for Auction', form=form)


@auction_bp.route('/my_submissions')
@login_required
def my_submissions():
    page = request.args.get('page', 1, type=int)
    submissions = AuctionItem.query.filter_by(submitter_user_id=current_user.id)\
                                 .order_by(AuctionItem.submission_time.desc())\
                                 .paginate(page=page, per_page=10)
    return render_template('auction/my_submissions.html', title='My Auction Submissions',
                           submissions=submissions, AuctionStatus=AuctionStatus)


@auction_bp.route('/<int:auction_id>', methods=['GET', 'POST'])
def view_auction(auction_id):
    auction_item = AuctionItem.query.get_or_404(auction_id)

    if auction_item.status == AuctionStatus.PENDING_APPROVAL and \
       (not current_user.is_authenticated or \
        (current_user.id != auction_item.submitter_user_id and current_user.role != UserRole.ADMIN)):
        flash('This auction is currently pending approval and not yet viewable.', 'info')
        return redirect(url_for('auction.index'))

    form = None
    if auction_item.status == AuctionStatus.ACTIVE and current_user.is_authenticated:
        highest_bid_obj = auction_item.bids.order_by(AuctionBid.bid_amount.desc()).first()
        current_highest_bid_val = highest_bid_obj.bid_amount if highest_bid_obj else Decimal('0.00')
        starting_bid_val = auction_item.actual_starting_bid
        min_increment_val = auction_item.minimum_bid_increment or app_flask.config.get('AUCTION_DEFAULT_MIN_BID_INCREMENT', Decimal('1.00'))

        form = PlaceBidForm(current_highest_bid=current_highest_bid_val,
                            starting_bid=starting_bid_val,
                            min_increment=min_increment_val)

        if form.validate_on_submit():
            if not current_user.accounts.first(): # Check if user has a bank account
                flash("You need a bank account to place bids. Please contact an admin.", "danger")
                return redirect(url_for('auction.view_auction', auction_id=auction_id))

            if current_user.id == auction_item.submitter_user_id:
                flash("You cannot bid on your own auction.", "warning")
                return redirect(url_for('auction.view_auction', auction_id=auction_id))

            # Check if user has enough balance for this bid (optional pre-check, final check on win)
            # user_account = current_user.accounts.first()
            # if user_account.balance < form.bid_amount.data:
            #     flash(f"Insufficient funds to place this bid. Your balance: {user_account.balance:.2f}", "danger")
            #     return redirect(url_for('auction.view_auction', auction_id=auction_id))


            new_bid = AuctionBid(
                auction_item_id=auction_item.id,
                bidder_user_id=current_user.id,
                bid_amount=form.bid_amount.data,
                bid_time=datetime.utcnow()
            )
            db.session.add(new_bid)

            # Anti-sniping logic
            now = datetime.utcnow()
            threshold_time = auction_item.current_end_time - timedelta(minutes=app_flask.config.get('AUCTION_ANTI_SNIPE_THRESHOLD_MINUTES', 2))
            if now >= threshold_time:
                extension_minutes = app_flask.config.get('AUCTION_ANTI_SNIPE_EXTENSION_MINUTES', 5)
                auction_item.current_end_time = now + timedelta(minutes=extension_minutes)
                flash(f'Auction extended by {extension_minutes} minutes due to late bid!', 'info')

            db.session.commit()
            flash(f'Your bid of {form.bid_amount.data:.2f} has been placed successfully!', 'success')
            # TODO: Notify previous highest bidder they've been outbid.
            return redirect(url_for('auction.view_auction', auction_id=auction_id))

    highest_bid = auction_item.bids.order_by(AuctionBid.bid_amount.desc()).first()
    time_remaining = auction_item.current_end_time - datetime.utcnow() if auction_item.current_end_time and auction_item.status == AuctionStatus.ACTIVE else None

    return render_template('auction/view_auction_detail.html', title=auction_item.item_name,
                           auction=auction_item, form=form, highest_bid=highest_bid,
                           time_remaining=time_remaining, AuctionStatus=AuctionStatus)


@auction_bp.route('/<int:auction_id>/cancel_submission', methods=['POST'])
@login_required
def cancel_submission(auction_id):
    item = AuctionItem.query.get_or_404(auction_id)
    if item.submitter_user_id != current_user.id:
        flash('You are not authorized to cancel this submission.', 'danger')
        return redirect(url_for('auction.my_submissions'))
    if item.status != AuctionStatus.PENDING_APPROVAL:
        flash('This auction can no longer be cancelled by you as it has been processed.', 'warning')
        return redirect(url_for('auction.my_submissions'))

    item.status = AuctionStatus.CANCELLED_BY_SUBMITTER
    item.admin_notes = (item.admin_notes or "") + f"\nCancelled by submitter on {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}."
    db.session.commit()
    flash('Your auction submission has been cancelled.', 'info')
    return redirect(url_for('auction.my_submissions'))


# --- Admin Auction Routes ---
@auction_bp.route('/admin/pending_approval', methods=['GET'])
@login_required
@admin_required
def list_pending_auctions():
    page = request.args.get('page', 1, type=int)
    pending_auctions = AuctionItem.query.filter_by(status=AuctionStatus.PENDING_APPROVAL)\
                                      .order_by(AuctionItem.submission_time.asc())\
                                      .paginate(page=page, per_page=10)
    return render_template('admin/auction/list_pending_auctions.html', title='Pending Auction Approvals',
                           auctions=pending_auctions)


@auction_bp.route('/admin/approve/<int:item_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def approve_auction_item(item_id):
    item = AuctionItem.query.get_or_404(item_id)
    if item.status != AuctionStatus.PENDING_APPROVAL:
        flash('This item is not currently pending approval.', 'warning')
        return redirect(url_for('auction.list_pending_auctions'))

    form = ApproveAuctionItemForm(obj=item) # Pre-populate if admin wants to see suggested values
    if not form.actual_starting_bid.data and item.suggested_starting_bid: # Pre-fill actual with suggested if empty
        form.actual_starting_bid.data = item.suggested_starting_bid
    if form.minimum_bid_increment.data is None: # Ensure default is populated
         form.minimum_bid_increment.data = app_flask.config.get('AUCTION_DEFAULT_MIN_BID_INCREMENT', 1.00)


    if request.method == 'POST': # Check which button was pressed
        if form.submit_approve.data and form.validate():
            item.actual_starting_bid = form.actual_starting_bid.data
            item.minimum_bid_increment = form.minimum_bid_increment.data or app_flask.config.get('AUCTION_DEFAULT_MIN_BID_INCREMENT', 1.00)
            item.admin_notes = form.admin_notes.data
            item.admin_approver_id = current_user.id
            item.approval_time = datetime.utcnow()
            item.start_time = item.approval_time # Auction starts immediately on approval

            duration_hours = app_flask.config.get('AUCTION_DEFAULT_DURATION_HOURS', 24)
            item.original_end_time = item.start_time + timedelta(hours=duration_hours)
            item.current_end_time = item.original_end_time
            item.status = AuctionStatus.ACTIVE

            db.session.commit()
            flash(f'Auction item "{item.item_name}" has been approved and is now active.', 'success')
            # TODO: Notify submitter
            return redirect(url_for('auction.list_pending_auctions'))

        elif form.submit_reject.data: # Minimal validation for notes if rejecting
            if not form.admin_notes.data or len(form.admin_notes.data.strip()) < 10 :
                 flash("Admin notes are required for rejection (min 10 characters).", "danger")
            else:
                item.admin_notes = form.admin_notes.data
                item.admin_approver_id = current_user.id # Admin who rejected
                item.approval_time = datetime.utcnow() # Time of rejection
                item.status = AuctionStatus.REJECTED_BY_ADMIN
                db.session.commit()
                flash(f'Auction item "{item.item_name}" has been rejected.', 'info')
                # TODO: Notify submitter
                return redirect(url_for('auction.list_pending_auctions'))

    return render_template('admin/auction/approve_auction_item.html', title='Approve/Reject Auction Item',
                           form=form, item=item)


@auction_bp.route('/admin/manage_all', methods=['GET'])
@login_required
@admin_required
def manage_all_auctions():
    page = request.args.get('page', 1, type=int)
    status_filter_str = request.args.get('status')

    query = AuctionItem.query
    active_filter_enum = None
    if status_filter_str:
        try:
            active_filter_enum = AuctionStatus[status_filter_str.upper()]
            query = query.filter_by(status=active_filter_enum)
        except KeyError:
            flash(f"Invalid status filter: {status_filter_str}", "warning")

    all_auctions = query.order_by(AuctionItem.submission_time.desc()).paginate(page=page, per_page=15)
    return render_template('admin/auction/manage_all_auctions.html', title='Manage All Auctions',
                           auctions=all_auctions, AuctionStatus=AuctionStatus, current_status_filter_str=status_filter_str)


@auction_bp.route('/admin/cancel/<int:auction_id>', methods=['POST'])
@login_required
@admin_required
def cancel_auction_by_admin(auction_id):
    item = AuctionItem.query.get_or_404(auction_id)
    # Admins can cancel PENDING_APPROVAL or ACTIVE auctions. Others need more thought.
    if item.status not in [AuctionStatus.PENDING_APPROVAL, AuctionStatus.ACTIVE]:
        flash(f"Cannot cancel auction in '{item.status.value}' state directly. Review item details.", "warning")
        return redirect(url_for('auction.manage_all_auctions'))

    item.status = AuctionStatus.CANCELLED_BY_ADMIN
    item.admin_notes = (item.admin_notes or "") + f"\nCancelled by admin {current_user.username} on {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}."
    # If active, might need to notify bidders (TODO)
    db.session.commit()
    flash(f"Auction #{item.id} ('{item.item_name}') has been cancelled by admin.", "success")
    return redirect(url_for('auction.manage_all_auctions'))


# TODO: Add routes for user's won auctions, bid history on an auction.
# TODO: Add scheduled job for closing auctions (Phase 1 for winner determination, Phase 2 for payment)
