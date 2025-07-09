from app import db
from app.models import Account, Transaction, TransactionType, TaxBracket, AutomatedTaxDeductionLog, User
from datetime import datetime
from decimal import Decimal

def apply_weekly_taxes():
    print(f"[{datetime.utcnow()}] Starting weekly tax collection job...")

    active_brackets = TaxBracket.query.filter_by(is_active=True).order_by(TaxBracket.min_balance.desc()).all()
    if not active_brackets:
        print("No active tax brackets found. Exiting tax collection job.")
        return  # <-- This was indented incorrectly in your snippet

    users_with_positive_balance = User.query.join(Account).filter(Account.balance > 0).all()
    processed_users_count = 0
    total_tax_collected = Decimal('0.0')

    for user in users_with_positive_balance:
        # Assuming one account per user
        account = Account.query.filter_by(user_id=user.id).first()
        if not account or account.balance <= 0:
            continue

        applicable_bracket = None
        for bracket in active_brackets:
            if account.balance >= bracket.min_balance:
                if bracket.max_balance is None or account.balance < bracket.max_balance:
                    applicable_bracket = bracket
                    break

        if applicable_bracket:
            balance_before_deduction = account.balance
            tax_rate_to_apply = applicable_bracket.tax_rate

            # Calculate tax amount (round to 2 decimal places)
            tax_amount = round(balance_before_deduction * (tax_rate_to_apply / Decimal('100.0')), 2)

            if tax_amount > Decimal('0.00'):
                try:
                    bank_transaction = Transaction(
                        account_id=account.id,
                        type=TransactionType.AUTOMATED_TAX_DEDUCTION,  # ensure this exists
                        amount=-tax_amount,
                        description=f"Weekly tax ({applicable_bracket.name} @ {tax_rate_to_apply}%)"
                    )
                    db.session.add(bank_transaction)

                    # Update account balance
                    account.balance -= tax_amount
                    db.session.add(account)

                    db.session.flush()  # to get transaction ID

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
                    print(f"Successfully taxed user {user.username}: {tax_amount}")
                except Exception as e:
                    db.session.rollback()
                    print(f"Error processing tax for user {user.username}: {e}")
            else:
                print(f"Calculated tax for user {user.username} is zero or less. Skipping.")
        else:
            print(f"No applicable tax bracket for user {user.username} with balance {account.balance}.")

    print(f"Weekly tax collection job finished. Processed {processed_users_count} users. Total tax collected: {total_tax_collected}.")
