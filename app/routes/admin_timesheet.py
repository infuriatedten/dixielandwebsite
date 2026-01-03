from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required
from app.decorators import admin_required
from app.models import User, Timesheet
from app import db
from datetime import datetime

bp = Blueprint('admin_timesheet', __name__)

@bp.route('/admin/timesheets')
@login_required
@admin_required
def view_timesheets():
    # Placeholder data
    users = [
        {'username': 'testuser', 'timesheets': [
            {'clock_in_time': datetime(2023, 10, 27, 8, 0, 0), 'clock_out_time': datetime(2023, 10, 27, 17, 0, 0)},
            {'clock_in_time': datetime(2023, 10, 26, 8, 5, 0), 'clock_out_time': datetime(2023, 10, 26, 17, 10, 0)},
        ]},
        {'username': 'anotheruser', 'timesheets': [
            {'clock_in_time': datetime(2023, 10, 27, 9, 0, 0), 'clock_out_time': datetime(2023, 10, 27, 17, 30, 0)},
        ]},
    ]
    return render_template('admin/timesheets.html', users=users)

@bp.route('/admin/users/manage')
@login_required
@admin_required
def manage_users():
    # Placeholder data
    users = [
        {'id': 1, 'username': 'testuser', 'position': 'Driver', 'pay_rate': 25.50},
        {'id': 2, 'username': 'anotheruser', 'position': 'Mechanic', 'pay_rate': 30.00},
    ]
    return render_template('admin/manage_users.html', users=users)

@bp.route('/admin/users/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    # This would be a form to edit the user's position and pay rate
    flash('User updated successfully.', 'success')
    return redirect(url_for('admin_timesheet.manage_users'))
