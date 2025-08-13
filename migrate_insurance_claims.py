
"""
Migration script to update insurance_claims table with farm-specific fields
Run this once to update your existing database
"""

from app import create_app, db
from app.models import InsuranceClaim
from sqlalchemy import text

def migrate_insurance_claims():
    app = create_app()
    
    with app.app_context():
        try:
            # Add new columns to insurance_claims table
            db.engine.execute(text("""
                ALTER TABLE insurance_claims 
                ADD COLUMN IF NOT EXISTS description TEXT,
                ADD COLUMN IF NOT EXISTS estimated_loss NUMERIC(10, 2)
            """))
            
            # Update existing claims with default values
            db.engine.execute(text("""
                UPDATE insurance_claims 
                SET description = 'Legacy claim - no description available',
                    estimated_loss = 0.00
                WHERE description IS NULL OR estimated_loss IS NULL
            """))
            
            # Alter reason column to be shorter since we're now using predefined categories
            db.engine.execute(text("""
                ALTER TABLE insurance_claims 
                ALTER COLUMN reason TYPE VARCHAR(100)
            """))
            
            print("Insurance claims table migration completed successfully!")
            
        except Exception as e:
            print(f"Migration error: {e}")
            print("Some changes may have already been applied or there may be compatibility issues.")

if __name__ == "__main__":
    migrate_insurance_claims()
