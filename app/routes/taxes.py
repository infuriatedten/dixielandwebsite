from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.models import TaxBracket, AutomatedTaxDeductionLog

bp = Blueprint('taxes', __name__)

@bp.route('/info')
@login_required
def tax_info():
    """
    Displays information about active tax brackets and the user's tax deduction history.
    """
    active_brackets = TaxBracket.query.filter_by(is_active=True).order_by(TaxBracket.min_balance).all()

    user_tax_logs = AutomatedTaxDeductionLog.query.filter_by(user_id=current_user.id)\
                                                .order_by(AutomatedTaxDeductionLog.deduction_date.desc())\
                                                .limit(20).all() # Show recent 20, or paginate if needed

    return render_template('taxes/tax_info.html',
                           title='Tax Information',
                           brackets=active_brackets,
                           user_logs=user_tax_logs)
