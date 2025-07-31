import os
import logging
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

from app import create_app, db
from app.models import User, UserRole

# Initialize Flask app
app = create_app()

# Optional: Import additional models for shell context
from app.models import (
    Account, Transaction, TransactionType, TaxBracket,
    AutomatedTaxDeductionLog, Ticket, TicketStatus,
    PermitApplication, PermitApplicationStatus,
    MarketplaceListing, MarketplaceListingStatus,
    Inspection
)

# Flask shell context
@app.shell_context_processor
def make_shell_context():
    return {
        'db': db,
        'User': User,
        'UserRole': UserRole,
        'Account': Account,
        'Transaction': Transaction,
        'TransactionType': TransactionType,
        'TaxBracket': TaxBracket,
        'AutomatedTaxDeductionLog': AutomatedTaxDeductionLog,
        'Ticket': Ticket,
        'TicketStatus': TicketStatus,
        'PermitApplication': PermitApplication,
        'PermitApplicationStatus': PermitApplicationStatus,
        'MarketplaceListing': MarketplaceListing,
        'MarketplaceListingStatus': MarketplaceListingStatus,
        'Inspection': Inspection
    }

def seed_insurance_rates():
    from app.models import InsuranceRate, InsuranceRateType
    # Check if rates already exist
    if InsuranceRate.query.count() > 4:
        return

    rates = [
        InsuranceRate(rate_type=InsuranceRateType.FARM, name='Farm Liability', rate=500.00, description='General liability coverage for farm operations.'),
        InsuranceRate(rate_type=InsuranceRateType.CROP, name='Crop Hail', rate=100.00, description='Coverage for hail damage to crops.'),
        InsuranceRate(rate_type=InsuranceRateType.ANIMAL, name='Livestock', rate=50.00, description='Coverage for livestock mortality.')
    ]

    for rate in rates:
        db.session.add(rate)
    db.session.commit()


if __name__ == '__main__':
    # Setup logger
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    port = int(os.environ.get('PORT', 5000))

    with app.app_context():
        logger.info(f"Checking database at URI: {app.config['SQLALCHEMY_DATABASE_URI']}")

        # Create tables if using MySQL (or fallback to general creation)
        try:
            db.create_all()
            logger.info("Database tables ensured.")
        except Exception as e:
            logger.error("Failed to initialize database.")
            logger.exception(e)

        seed_insurance_rates()

        # Create default admin if it doesn't exist
        admin_username = 'admin'
        if not User.query.filter_by(username=admin_username).first():
            logger.info("Admin user not found, creating default admin user.")
            try:
                admin_user = User(
                    username=admin_username,
                    email='admin@example.com',
                    role=UserRole.ADMIN
                )
                admin_user.set_password('adminpassword')  # ✅ Change in production
                db.session.add(admin_user)
                db.session.commit()
                logger.info("Admin user created successfully: username=admin, password=adminpassword")
            except Exception as e:
                db.session.rollback()
                logger.error("Failed to create admin user.")
                logger.exception(e)
        else:
            logger.info("Admin user already exists.")
    db.create_all(app=app)
    # Start Flask dev server
    app.run(host='0.0.0.0', port=port, debug=True)
