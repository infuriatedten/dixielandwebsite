from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.forms import EditProfileForm
from app.models import Company, Farmer, Parcel

bp = Blueprint('user', __name__)

@bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = EditProfileForm(
        original_username=current_user.username,
        original_email=current_user.email,
        obj=current_user
    )

    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.email = form.email.data
        current_user.about_me = form.about_me.data

        # Handle optional fields
        if hasattr(form, 'region') and form.region.data:
            current_user.region = form.region.data

        db.session.commit()
        flash('Your profile has been updated.', 'success')
        return redirect(url_for('user.profile'))

    # Pre-fill optional fields only on GET
    if request.method == 'GET' and hasattr(form, 'region'):
        form.region.data = current_user.region or 'OTHER_DEFAULT'

    return render_template(
        'user/profile.html',
        title='My Profile',
        form=form,
        user=current_user
    )
