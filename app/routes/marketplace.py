from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app as app_flask
from flask_login import current_user, login_required
from app import db
from app.models import (
    User, UserRole, MarketplaceListing,
    MarketplaceListingStatus, Account
)
from app.forms import CreateListingForm, EditListingForm
from app.services.discord_webhook_service import (
    post_listing_to_discord, update_listing_on_discord
)

bp = Blueprint('marketplace', __name__)

@bp.route('/')
def index():
    """Public view of available marketplace listings."""
    page = request.args.get('page', 1, type=int)

    listings_pagination = MarketplaceListing.query \
        .filter(MarketplaceListing.status.in_([
            MarketplaceListingStatus.AVAILABLE,
            MarketplaceListingStatus.SOLD_MORE_AVAILABLE
        ])) \
        .order_by(MarketplaceListing.creation_date.desc()) \
        .paginate(page=page, per_page=12)

    return render_template(
        'marketplace/index.html',
        title='Marketplace',
        listings_pagination=listings_pagination,
        MarketplaceListingStatus=MarketplaceListingStatus
    )


@bp.route('/new', methods=['GET', 'POST'])
@login_required
def create_listing():
    form = CreateListingForm()
    if form.validate_on_submit():
        new_listing = MarketplaceListing(
            seller_user_id=current_user.id,
            item_name=form.item_name.data,
            description=form.description.data,
            price=form.price.data,
            quantity=form.quantity.data,
            unit=form.unit.data,
            status=MarketplaceListingStatus.AVAILABLE
        )
        db.session.add(new_listing)
        db.session.commit()

        db.session.refresh(new_listing)

        discord_post_success = post_listing_to_discord(new_listing)

        if discord_post_success:
            flash('Listing created successfully and an attempt was made to post it to Discord!', 'success')
        else:
            app_flask.logger.warning(f"Listing {new_listing.id} created, but Discord post via webhook failed or was not configured.")
            flash('Listing created successfully, but there was an issue posting it to Discord (webhook may not be configured).', 'warning')

        return redirect(url_for('marketplace.view_listing_detail', listing_id=new_listing.id))

    return render_template('marketplace/create_listing.html', title='Create New Marketplace Listing', form=form)


@bp.route('/my_listings')
@login_required
def my_listings():
    page = request.args.get('page', 1, type=int)
    status_filter_str = request.args.get('status', None)

    query = MarketplaceListing.query.filter_by(seller_user_id=current_user.id)

    active_filter_enum = None
    if status_filter_str:
        try:
            active_filter_enum = MarketplaceListingStatus[status_filter_str.upper()]
            query = query.filter_by(status=active_filter_enum)
        except KeyError:
            flash(f"Invalid status filter: {status_filter_str}", "warning")

    listings_pagination = query.order_by(MarketplaceListing.creation_date.desc()).paginate(page=page, per_page=10)

    return render_template('marketplace/my_listings.html', title='My Marketplace Listings',
                           listings_pagination=listings_pagination,
                           MarketplaceListingStatus=MarketplaceListingStatus,
                           current_status_filter_str=status_filter_str)


@bp.route('/listing/<int:listing_id>')
def view_listing_detail(listing_id):
    listing = MarketplaceListing.query.get_or_404(listing_id)
    if listing.status == MarketplaceListingStatus.CANCELLED and \
       (not current_user.is_authenticated or \
        (current_user.id != listing.seller_user_id and (not hasattr(current_user, 'role') or current_user.role != UserRole.ADMIN))):
        flash("This listing has been cancelled by the seller.", "info")
        return redirect(url_for('marketplace.index'))

    return render_template('marketplace/view_listing_detail.html', title=f"View Listing: {listing.item_name}", listing=listing, MarketplaceListingStatus=MarketplaceListingStatus)


@bp.route('/listing/<int:listing_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_listing(listing_id):
    listing = MarketplaceListing.query.get_or_404(listing_id)
    if listing.seller_user_id != current_user.id and current_user.role != UserRole.ADMIN:
        flash('You are not authorized to edit this listing.', 'danger')
        return redirect(url_for('marketplace.index'))

    if listing.status not in [MarketplaceListingStatus.AVAILABLE, MarketplaceListingStatus.SOLD_MORE_AVAILABLE]:
        flash('Only listings that are "Available" or "Sold - More Available" can be edited. You may need to cancel and relist for major changes to sold items.', 'warning')
        return redirect(url_for('marketplace.view_listing_detail', listing_id=listing.id))

    form = EditListingForm(obj=listing)
    if form.validate_on_submit():
        listing.item_name = form.item_name.data
        listing.description = form.description.data
        listing.price = form.price.data
        listing.quantity = form.quantity.data
        listing.unit = form.unit.data
        db.session.commit()

        update_listing_on_discord(listing, action_text="Listing Details Updated")
        flash('Listing updated successfully. Discord update attempted.', 'success')
        return redirect(url_for('marketplace.view_listing_detail', listing_id=listing.id))

    return render_template('marketplace/edit_listing.html', title=f"Edit Listing: {listing.item_name}", form=form, listing=listing)


@bp.route('/listing/<int:listing_id>/update_status', methods=['POST'])
@login_required
def update_listing_status(listing_id):
    listing = MarketplaceListing.query.get_or_404(listing_id)
    if listing.seller_user_id != current_user.id and current_user.role != UserRole.ADMIN:
        flash('You are not authorized to update this listing status.', 'danger')
        return redirect(url_for('marketplace.index'))

    new_status_str = request.form.get('new_status')
    if not new_status_str:
        flash('No new status provided.', 'danger')
        return redirect(url_for('marketplace.view_listing_detail', listing_id=listing.id))

    try:
        new_status = MarketplaceListingStatus[new_status_str.upper()]
    except KeyError:
        flash('Invalid status update.', 'danger')
        return redirect(url_for('marketplace.view_listing_detail', listing_id=listing.id))

    if listing.status == MarketplaceListingStatus.CANCELLED:
         flash('Cannot change status of a "Cancelled" listing.', 'warning')
         return redirect(url_for('marketplace.view_listing_detail', listing_id=listing.id))

    listing.status = new_status
    db.session.commit()

    update_listing_on_discord(listing, action_text=f"Listing Status Updated to {new_status.value}")
    flash(f'Listing status updated to "{new_status.value}". Discord update attempted.', 'info')
    return redirect(url_for('marketplace.view_listing_detail', listing_id=listing.id))


# ======= NEW ADMIN ROUTE TO FIX THE ERROR =======
@bp.route('/admin/all_listings')
@login_required
def admin_all_listings():
    if current_user.role != UserRole.ADMIN:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('marketplace.index'))

    page = request.args.get('page', 1, type=int)
    listings_pagination = MarketplaceListing.query.order_by(MarketplaceListing.creation_date.desc()).paginate(page=page, per_page=20)

    return render_template('marketplace/admin_all_listings.html',
                           title='All Marketplace Listings (Admin)',
                           listings_pagination=listings_pagination,
                           MarketplaceListingStatus=MarketplaceListingStatus)
