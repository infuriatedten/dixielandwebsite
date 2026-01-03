from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required
from app.decorators import admin_required
from app.models import User, Timesheet
from app import db
from datetime import datetime

bp = Blueprint('admin_timesheet', __name__)

from app.forms import EditUserForm

@bp.route('/admin/timesheets')
@login_required
@admin_required
def view_timesheets():
    users = User.query.all()
    return render_template('admin/timesheets.html', users=users)

@bp.route('/admin/users/manage')
@login_required
@admin_required
def manage_users():
    users = User.query.all()
    return render_template('admin/manage_users.html', users=users)

@bp.route('/admin/users/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    form = EditUserForm(obj=user)
    if form.validate_on_submit():
        user.position = form.position.data
        user.pay_rate = form.pay_rate.data
        db.session.commit()
        flash('User updated successfully.', 'success')
        return redirect(url_for('admin_timesheet.manage_users'))
    return render_template('admin/edit_user.html', form=form, user=user)
