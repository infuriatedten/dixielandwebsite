from app import db, scheduler # Import db and scheduler from the app package
from app.models import Account, Transaction, TransactionType, TaxBracket, AutomatedTaxDeductionLog, User
from sqlalchemy import and_, or_
from datetime import datetime
from decimal import Decimal

def apply_weekly_taxes():
    """
    Job function to apply weekly percentage-based taxes to user accounts.
    This function will be called by the APScheduler.
    """
    # This function is now designed to be called from a script run by a Render Cron Job.
    # It assumes an app context is already active if called from such a script (like run_tax_job.py).
    # If called directly or from APScheduler within app, app context is handled by scheduler.app.app_context()
    # For direct script, run_tax_job.py will provide the context.

    # from flask import current_app # If you need current_app directly
    # with current_app.app_context(): # This would be redundant if run_tax_job.py already establishes context

    print(f"[{datetime.utcnow()}] Starting weekly tax collection job (via direct call or external scheduler)...")

    active_brackets = TaxBracket.query.filter_by(is_active=True).order_by(TaxBracket.min_balance.desc()).all()
    if not active_brackets:
        print("No active tax brackets found. Exiting tax collection job.")
            return

        users_with_positive_balance = User.query.join(Account).filter(Account.balance > 0).all()
        processed_users_count = 0
        total_tax_collected = Decimal('0.0')

        for user in users_with_positive_balance:
            # Assuming one account per user for now as per current banking setup
            account = Account.query.filter_by(user_id=user.id).first()
            if not account or account.balance <= 0: # Double check, though query should handle balance > 0
                continue

            applicable_bracket = None
            for bracket in active_brackets: # Already sorted by min_balance desc
                if account.balance >= bracket.min_balance:
                    if bracket.max_balance is None or account.balance < bracket.max_balance:
                        applicable_bracket = bracket
                        break # Found the highest applicable bracket

            if applicable_bracket:
                balance_before_deduction = account.balance
                tax_rate_to_apply = applicable_bracket.tax_rate

                # Calculate tax amount (round to 2 decimal places)
                tax_amount = round(balance_before_deduction * (tax_rate_to_apply / Decimal('100.0')), 2)

                if tax_amount > Decimal('0.00'):
                    try:
                        # Create banking transaction for the tax deduction
                        bank_transaction = Transaction(
                            account_id=account.id,
                            type=TransactionType.AUTOMATED_TAX_DEDUCTION, # Ensure this enum value exists
                            amount=-tax_amount, # Negative amount for deduction
                            description=f"Weekly tax ({applicable_bracket.name} @ {tax_rate_to_apply}%)"
                            # processed_by_admin_id could be null or a system user ID if you have one
                        )
                        db.session.add(bank_transaction)

                        # Update account balance
                        account.balance -= tax_amount
                        db.session.add(account)

                        # Flush to get bank_transaction.id
                        db.session.flush()

                        # Log the tax deduction
                        tax_log = AutomatedTaxDeductionLog(
                            user_id=user.id,
                            tax_bracket_id=applicable_bracket.id,
                            balance_before_deduction=balance_before_deduction,
                            tax_rate_applied=tax_rate_to_apply,
                            amount_deducted=tax_amount,
                            deduction_date=datetime.utcnow(),
                            banking_transaction_id=bank_transaction.id
                        )
                        db.session.add(tax_log)

                        db.session.commit()
                        processed_users_count += 1
                        total_tax_collected += tax_amount
                        print(f"Successfully taxed user {user.username} (Account ID: {account.id}): {tax_amount} {account.currency}")
                    except Exception as e:
                        db.session.rollback()
                        print(f"Error processing tax for user {user.username} (Account ID: {account.id}): {e}")
                else:
                    print(f"Calculated tax for user {user.username} is zero or less. Skipping.")
            else:
                print(f"No applicable tax bracket for user {user.username} with balance {account.balance}.")

        print(f"Weekly tax collection job finished. Processed {processed_users_count} users. Total tax collected: {total_tax_collected}.")

# The add_tax_job_to_scheduler function is no longer needed if using Render Cron Jobs.
# It can be removed or commented out.
# def add_tax_job_to_scheduler(app_scheduler):
#     """Adds the tax job to the scheduler if it doesn't already exist."""
#     job_id = 'weekly_tax_collection_job'
#     if not app_scheduler.get_job(job_id):
#         app_scheduler.add_job(
#             id=job_id,
#             func=apply_weekly_taxes, # Make sure this path is correct if re-enabled
#             trigger='cron',
#             day_of_week='sun',
#             hour=0,
#             minute=5
#         )
#         print(f"Job '{job_id}' added to scheduler.")
#     else:
#         print(f"Job '{job_id}' already exists in scheduler.")

# Ensure TransactionType.AUTOMATED_TAX_DEDUCTION exists (already verified).
