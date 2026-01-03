from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import Timesheet
from app import db
from datetime import datetime

bp = Blueprint('timesheet', __name__)

@bp.route('/timesheet')
@login_required
def view_timesheet():
    timesheets = Timesheet.query.filter_by(user_id=current_user.id).order_by(Timesheet.clock_in_time.desc()).all()
    return render_template('timesheet/view.html', timesheets=timesheets)

@bp.route('/clock_in', methods=['POST'])
@login_required
def clock_in():
    # Check if there is an open timesheet entry
    open_timesheet = Timesheet.query.filter_by(user_id=current_user.id, clock_out_time=None).first()
    if open_timesheet:
        flash('You are already clocked in.', 'warning')
    else:
        new_timesheet = Timesheet(user_id=current_user.id)
        db.session.add(new_timesheet)
        db.session.commit()
        flash('You have successfully clocked in.', 'success')
    return redirect(url_for('timesheet.view_timesheet'))

@bp.route('/clock_out', methods=['POST'])
@login_required
def clock_out():
    open_timesheet = Timesheet.query.filter_by(user_id=current_user.id, clock_out_time=None).first()
    if open_timesheet:
        open_timesheet.clock_out_time = datetime.utcnow()
        db.session.commit()
        flash('You have successfully clocked out.', 'success')
    else:
        flash('You are not clocked in.', 'warning')
    return redirect(url_for('timesheet.view_timesheet'))
