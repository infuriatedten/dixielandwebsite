import os
from app import create_app, db
from app.models import TaxBracket

# Create an application context
app = create_app()
app.app_context().push()

def seed_tax_brackets():
    """
    Clears all existing tax brackets and seeds the database with a new,
    progressive set of brackets.
    """
    try:
        # Clear existing brackets
        num_deleted = db.session.query(TaxBracket).delete()
        if num_deleted > 0:
            print(f"Deleted {num_deleted} existing tax bracket(s).")

        # Define the new tax brackets
        brackets = [
            {'name': 'Tier 1', 'min_balance': 0, 'max_balance': 10000, 'tax_rate': 1.0, 'is_active': True},
            {'name': 'Tier 2', 'min_balance': 10000.01, 'max_balance': 50000, 'tax_rate': 2.5, 'is_active': True},
            {'name': 'Tier 3', 'min_balance': 50000.01, 'max_balance': 250000, 'tax_rate': 5.0, 'is_active': True},
            {'name': 'Tier 4', 'min_balance': 250000.01, 'max_balance': None, 'tax_rate': 10.0, 'is_active': True}
        ]

        # Add new brackets to the session
        for bracket_data in brackets:
            bracket = TaxBracket(**bracket_data)
            db.session.add(bracket)

        # Commit the changes to the database
        db.session.commit()
        print(f"Successfully seeded {len(brackets)} new tax brackets.")

    except Exception as e:
        db.session.rollback()
        print(f"An error occurred while seeding tax brackets: {e}")

if __name__ == '__main__':
    print("Running tax bracket seeder...")
    seed_tax_brackets()
    print("Seeding complete.")
