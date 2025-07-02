from app import create_app, db
from app.models import User, UserRole # Make sure UserRole is imported if you plan to use it here

app = create_app()

from app.models import Account, Transaction, TransactionType

@app.shell_context_processor
def make_shell_context():
    return {
        'db': db,
        'User': User,
        'UserRole': UserRole,
        'Account': Account,
        'Transaction': Transaction,
        'TransactionType': TransactionType,
        # 'TaxType': TaxType, # Replaced by TaxBracket
        # 'TaxPaymentLog': TaxPaymentLog, # Replaced by AutomatedTaxDeductionLog
        'TaxBracket': TaxBracket,
        'AutomatedTaxDeductionLog': AutomatedTaxDeductionLog,
        'Ticket': Ticket,
        'TicketStatus': TicketStatus,
        'PermitApplication': PermitApplication,
        'PermitApplicationStatus': PermitApplicationStatus,
        'MarketplaceListing': MarketplaceListing,
        'MarketplaceListingStatus': MarketplaceListingStatus, # Corrected Enum Name
        'Inspection': Inspection
    }

# Import new models for shell context
from app.models import TaxBracket, AutomatedTaxDeductionLog, Ticket, TicketStatus, PermitApplication, PermitApplicationStatus, MarketplaceListing, MarketplaceListingStatus, Inspection

if __name__ == '__main__':
    # For Render, it will use a Gunicorn command, e.g., gunicorn run:app
    # This __main__ block is mainly for local development.
    # Ensure the host is set to '0.0.0.0' to be accessible within a Docker container or similar environment if needed
    # The port can be specified by Render via the PORT environment variable.
    import os
    port = int(os.environ.get('PORT', 5000)) # Render sets PORT

    # Initialize database and create an admin user if it doesn't exist
    with app.app_context():
        print(f"Checking database at URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
        # The db.create_all() is in create_app for SQLite.
        # For MySQL, this should ideally be done via migrations.
        # However, for simplicity in this initial setup, if it's SQLite, it's already handled.
        # If it's MySQL, ensure the database itself is created. Tables might be created if not existing.
        if 'mysql' in app.config['SQLALCHEMY_DATABASE_URI']:
            try:
                # This will attempt to create tables if they don't exist.
                # It requires the database itself to be created and accessible.
                db.create_all()
                print("INFO: db.create_all() called for MySQL (tables created if not exist).")
            except Exception as e:
                print(f"ERROR: Could not connect to or create tables in MySQL: {e}")
                print("Please ensure your MySQL server is running, the database exists, and connection details in config.py are correct.")

        # Create a default admin user if one doesn't exist (for initial setup)
        if not User.query.filter_by(username='admin').first():
            print("Admin user not found, creating one...")
            try:
                admin_user = User(username='admin', email='admin@example.com', role=UserRole.ADMIN)
                admin_user.set_password('adminpassword') # Change in production!
                db.session.add(admin_user)
                db.session.commit()
                print("Admin user 'admin' with password 'adminpassword' created.")
            except Exception as e:
                db.session.rollback()
                print(f"Error creating admin user: {e}")
        else:
            print("Admin user already exists.")

    # The host='0.0.0.0' makes it accessible externally if run in a container/VM.
    # Render will manage the host and port via its environment.
    app.run(host='0.0.0.0', port=port, debug=True) # debug=True for development convenience. Set to False for production.
