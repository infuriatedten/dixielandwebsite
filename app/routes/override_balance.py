# admin_views.py
from flask import Blueprint, request, redirect, render_template
from models import db, Farmer, BalanceHistory
from flask_login import login_required

admin = Blueprint('admin', __name__)

@admin.route('/admin/override_balance/<int:farmer_id>', methods=['GET', 'POST'])
@login_required
def override_balance(farmer_id):
    farmer = Farmer.query.get_or_404(farmer_id)
    account = farmer.bank_account

    if request.method == 'POST':
        new_balance = float(request.form['new_balance'])
        description = request.form['description']

        change = new_balance - account.balance
        account.balance = new_balance
        account.updated_at = datetime.utcnow()

        history = BalanceHistory(
            account_id=account.id,
            change=change,
            balance_after=new_balance,
            description=description,
            source='ADMIN'
        )
        db.session.add(history)
        db.session.commit()
        return redirect('/admin/farmer/' + str(farmer_id))

    return render_template('admin/override_balance.html', farmer=farmer, account=account)
