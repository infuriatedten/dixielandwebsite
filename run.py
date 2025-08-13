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
    Inspection, Fine
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
        'Inspection': Inspection,
        'Fine': Fine
    }

def seed_fines():
    from app.models import Fine
    from decimal import Decimal

    fines_to_seed = [
        {'name': 'Speeding (1-15 mph over)', 'description': 'Exceeding the speed limit by 1-15 mph.', 'amount': Decimal('75.00')},
        {'name': 'Speeding (16-30 mph over)', 'description': 'Exceeding the speed limit by 16-30 mph.', 'amount': Decimal('150.00')},
        {'name': 'Speeding (31+ mph over)', 'description': 'Exceeding the speed limit by 31 or more mph.', 'amount': Decimal('300.00')},
        {'name': 'Illegal Parking', 'description': 'Parking in a restricted area.', 'amount': Decimal('50.00')},
        {'name': 'Running a Red Light', 'description': 'Failing to stop at a red light.', 'amount': Decimal('100.00')},
        {'name': 'Reckless Driving', 'description': 'Driving with willful or wanton disregard for the safety of persons or property.', 'amount': Decimal('500.00')},
        {'name': 'Expired Vehicle Registration', 'description': 'Operating a vehicle with an expired registration.', 'amount': Decimal('60.00')},
        {'name': 'No Proof of Insurance', 'description': 'Operating a vehicle without proof of insurance.', 'amount': Decimal('200.00')},
    ]

    existing_fines = {fine.name for fine in Fine.query.all()}
    new_fines_added = 0

    for fine_data in fines_to_seed:
        if fine_data['name'] not in existing_fines:
            new_fine = Fine(
                name=fine_data['name'],
                description=fine_data['description'],
                amount=fine_data['amount']
            )
            db.session.add(new_fine)
            new_fines_added += 1

    if new_fines_added > 0:
        db.session.commit()

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

        logger.info("Seeding insurance rates...")
        seed_insurance_rates()
        logger.info("Insurance rates seeded.")

        logger.info("Seeding fines...")
        seed_fines()
        logger.info("Fines seeded.")

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

    with app.app_context():
        logger.info("Creating all tables...")
        db.create_all()
        logger.info("All tables created.")

    # Start Flask dev server
    logger.info("Starting Flask dev server...")
    app.run(host='0.0.0.0', port=port, debug=True)