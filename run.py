from dotenv import load_dotenv
load_dotenv()

from app import create_app, db
from app.models import User, UserRole  # Make sure UserRole is imported if you plan to use it here

app = create_app()

from app.models import (
    Account, Transaction, TransactionType,
    TaxBracket, AutomatedTaxDeductionLog,
    Ticket, TicketStatus,
    PermitApplication, PermitApplicationStatus,
    MarketplaceListing, MarketplaceItemStatus,
    Inspection,
    Company, Farmer, Parcel
)

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
        'MarketplaceItemStatus': MarketplaceItemStatus,
        'Inspection': Inspection,
        'Company': Company,
        'Farmer': Farmer,
        'Parcel': Parcel
    }

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5001))  # Render sets PORT

    with app.app_context():
        print(f"Checking database at URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
        if 'mysql' in app.config['SQLALCHEMY_DATABASE_URI']:
            try:
                db.create_all()
                print("INFO: db.create_all() called for MySQL (tables created if not exist).")
            except Exception as e:
                print(f"ERROR: Could not connect to or create tables in MySQL: {e}")
                print("Please ensure your MySQL server is running, the database exists, and connection details in config.py are correct.")

        if not User.query.filter_by(username='admin').first():
            print("Admin user not found, creating one...")
            try:
                admin_user = User(username='admin', email='admin@example.com', role=UserRole.ADMIN)
                admin_user.set_password('adminpassword')  # Change in production!
                db.session.add(admin_user)
                db.session.commit()
                print("Admin user 'admin' with password 'adminpassword' created.")
            except Exception as e:
                db.session.rollback()
                print(f"Error creating admin user: {e}")
        else:
            print("Admin user already exists.")

    app.run(host='0.0.0.0', port=port, debug=True, use_reloader=False)
