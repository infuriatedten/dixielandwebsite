from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models import User, Transaction, TransactionType
from datetime import datetime

timesheet_bp = Blueprint('timesheet', __name__)

@timesheet_bp.route('/clock_in', methods=['POST'])
@login_required
def clock_in():
    if current_user.is_clocked_in:
        flash('You are already clocked in.', 'warning')
        return redirect(url_for('main.home'))

    current_user.is_clocked_in = True
    current_user.current_session_start = datetime.utcnow()
    db.session.commit()
    flash('You have successfully clocked in.', 'success')
    return redirect(url_for('main.home'))

@timesheet_bp.route('/clock_out', methods=['POST'])
@login_required
def clock_out():
    if not current_user.is_clocked_in or current_user.current_session_start is None:
        flash('You are not clocked in or your session is invalid.', 'warning')
        return redirect(url_for('main.home'))

    clock_out_time = datetime.utcnow()
    duration_seconds = (clock_out_time - current_user.current_session_start).total_seconds()

    # Pay rate is per hour, so convert duration to hours
    duration_hours = duration_seconds / 3600
    amount_earned = duration_hours * float(current_user.pay_rate)

    if amount_earned > 0:
        # Assume the user has one primary account
        user_account = current_user.accounts.first()
        if user_account:
            new_transaction = Transaction(
                account_id=user_account.id,
                type=TransactionType.ADMIN_DEPOSIT,
                amount=amount_earned,
                description=f'Pay for {duration_hours:.2f} hours of work.'
            )
            user_account.balance += amount_earned
            db.session.add(new_transaction)
            flash(f'You have been paid ${amount_earned:.2f} for your work.', 'success')
        else:
            flash('Could not find a bank account to deposit your pay. Please contact an admin.', 'danger')

    current_user.is_clocked_in = False
    current_user.current_session_start = None
    db.session.commit()

    return redirect(url_for('main.home'))
