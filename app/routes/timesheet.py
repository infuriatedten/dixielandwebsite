from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import Timesheet
from app import db
from datetime import datetime

bp = Blueprint('timesheet', __name__)

@bp.route('/timesheet')
@login_required
def view_timesheet():
    # Placeholder data
    timesheets = [
        {'clock_in_time': datetime(2023, 10, 27, 8, 0, 0), 'clock_out_time': datetime(2023, 10, 27, 17, 0, 0)},
        {'clock_in_time': datetime(2023, 10, 26, 8, 5, 0), 'clock_out_time': datetime(2023, 10, 26, 17, 10, 0)},
    ]
    return render_template('timesheet/view.html', timesheets=timesheets)

@bp.route('/timesheet/clock_in', methods=['POST'])
@login_required
def clock_in():
    # This would create a new Timesheet entry
    flash('You have successfully clocked in.', 'success')
    return redirect(url_for('timesheet.view_timesheet'))

@bp.route('/timesheet/clock_out', methods=['POST'])
@login_required
def clock_out():
    # This would update the latest Timesheet entry with a clock_out_time
    flash('You have successfully clocked out.', 'success')
    return redirect(url_for('timesheet.view_timesheet'))
