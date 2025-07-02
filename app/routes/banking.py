from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import current_user, login_required
from app import db
from app.models import User, Account, Transaction
from app.decorators import admin_required # If any admin-specific banking views were here

bp = Blueprint('banking', __name__)

@bp.route('/dashboard')
@login_required
def dashboard():
    user_accounts = Account.query.filter_by(user_id=current_user.id).all()
    # Assuming a user might have multiple accounts in different currencies, though current setup is one.
    # If strictly one account per user is enforced elsewhere, this can be simplified.

    if not user_accounts:
        flash('You do not have any bank accounts set up yet. Please contact an administrator.', 'warning')
        # Or, if users can create their own (not current plan):
        # return redirect(url_for('banking.create_account'))
        return render_template('banking/dashboard_no_account.html', title='Banking Dashboard')

    # For simplicity, let's assume one primary account or just list all.
    # If there's a concept of a "primary" account, filter for that.
    # Here, we'll just take the first one found or prepare to list multiple.

    account_details = []
    for account in user_accounts:
        transactions = Transaction.query.filter_by(account_id=account.id).order_by(Transaction.timestamp.desc()).limit(10).all() # Recent 10
        account_details.append({
            'account': account,
            'recent_transactions': transactions
        })

    return render_template('banking/dashboard.html', title='Banking Dashboard', account_details=account_details)

@bp.route('/account/<int:account_id>')
@login_required
def view_account(account_id):
    account = Account.query.get_or_404(account_id)
    if account.user_id != current_user.id and current_user.role != UserRole.ADMIN: # Admins can view any
        flash('You are not authorized to view this account.', 'danger')
        return redirect(url_for('banking.dashboard'))

    page = request.args.get('page', 1, type=int)
    transactions = Transaction.query.filter_by(account_id=account.id)\
                                    .order_by(Transaction.timestamp.desc())\
                                    .paginate(page=page, per_page=15)

    return render_template('banking/view_account.html', title=f'Account {account.id} Statement', account=account, transactions=transactions)


@bp.route('/account/<int:account_id>/statement')
@login_required
def download_statement(account_id):
    account = Account.query.get_or_404(account_id)
    if account.user_id != current_user.id and current_user.role != UserRole.ADMIN:
        flash('You are not authorized to generate a statement for this account.', 'danger')
        return redirect(url_for('banking.dashboard'))

    # For now, just display it as a page. PDF generation would be more complex.
    all_transactions = Transaction.query.filter_by(account_id=account.id)\
                                     .order_by(Transaction.timestamp.asc()).all() # Asc for statement chronological order

    return render_template('banking/statement_page.html',
                           title=f'Statement for Account {account.id}',
                           account=account,
                           transactions=all_transactions)

# Note: Actual "download" would involve generating a file (CSV, PDF).
# This is a simplified "view statement" page.
# from flask import Response
# import io
# import csv
# @bp.route('/account/<int:account_id>/statement/download_csv')
# @login_required
# def download_statement_csv(account_id):
#     account = Account.query.get_or_404(account_id)
#     if account.user_id != current_user.id:
#         abort(403)
#     transactions = Transaction.query.filter_by(account_id=account.id).order_by(Transaction.timestamp.asc()).all()
#
#     output = io.StringIO()
#     writer = csv.writer(output)
#     writer.writerow(['Timestamp', 'Type', 'Amount', 'Currency', 'Description'])
#     for t in transactions:
#         writer.writerow([t.timestamp.strftime("%Y-%m-%d %H:%M:%S"), t.type.value, t.amount, account.currency, t.description])
#
#     output.seek(0)
#     return Response(output, mimetype="text/csv", headers={"Content-Disposition":f"attachment;filename=statement_account_{account.id}.csv"})
