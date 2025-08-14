
from flask import Blueprint, make_response
from flask_login import login_required, current_user
from app.decorators import admin_required
from app.models import User, Transaction
import csv
from io import StringIO

export_bp = Blueprint('export', __name__)

@export_bp.route('/transactions/csv')
@login_required
def export_transactions_csv():
    """Export user's transactions to CSV"""
    account = current_user.accounts.first()
    if not account:
        return "No account found", 404
    
    output = StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['Date', 'Type', 'Amount', 'Description'])
    
    # Write transactions
    for transaction in account.transactions.order_by(Transaction.timestamp.desc()):
        writer.writerow([
            transaction.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            transaction.type.value,
            float(transaction.amount),
            transaction.description or ''
        ])
    
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = 'attachment; filename=transactions.csv'
    
    return response

@export_bp.route('/admin/users/csv')
@admin_required
def export_users_csv():
    """Export all users to CSV (admin only)"""
    output = StringIO()
    writer = csv.writer(output)
    
    writer.writerow(['ID', 'Username', 'Email', 'Role', 'Region'])
    
    for user in User.query.all():
        writer.writerow([
            user.id,
            user.username,
            user.email,
            user.role.value,
            user.region or 'OTHER_DEFAULT'
        ])
    
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = 'attachment; filename=users.csv'
    
    return response
