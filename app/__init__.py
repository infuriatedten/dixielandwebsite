from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_apscheduler import APScheduler # Import APScheduler
from config import Config
from app.scheduler_config import SchedulerConfig # Import scheduler config
import os

db = SQLAlchemy()
login_manager = LoginManager()
scheduler = APScheduler() # Initialize scheduler
login_manager.login_view = 'auth.login' # The route for login
login_manager.login_message_category = 'info' # Flash message category

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Check if DATABASE_URL is the placeholder, and if so, use SQLite for sandbox.
    # This is a more robust check for the placeholder scenario.
    db_uri = app.config.get('SQLALCHEMY_DATABASE_URI')
    if not db_uri or 'user:password@host/dbname' in db_uri or 'sqlite:///:memory:' in db_uri:
        # Fallback for sandbox if DATABASE_URL is not properly set for MySQL
        # This ensures the app can run in a constrained environment for testing basic structure
        # In a real deployment (like Render), DATABASE_URL would be correctly set.
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        print("INFO: Using in-memory SQLite for application initialization in sandbox mode.")

    if app.config['SECRET_KEY'] == 'your_secret_key':
        print("WARNING: Using default SECRET_KEY. Set a strong SECRET_KEY in your environment or config.py for production.")


    db.init_app(app)
    login_manager.init_app(app)

    # Configure and start the scheduler - REMOVED as we are using Render Cron Jobs
    # app.config.from_object(SchedulerConfig)
    # scheduler.init_app(app)

    # Import models here to ensure they are known to SQLAlchemy before create_all or job imports
    from app.models import User, Account, Transaction, TransactionType, TaxBracket, AutomatedTaxDeductionLog, Ticket, TicketStatus, PermitApplication, PermitApplicationStatus, MarketplaceListing, MarketplaceListingStatus, Inspection

    # Start scheduler only if not in reloader process (to avoid starting it twice in debug mode) - REMOVED
    # if not app.debug or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
    #     if not scheduler.running: # Check if scheduler is already running
    #         # from app.jobs.taxes import add_tax_job_to_scheduler # Import here to avoid circularity
    #         # add_tax_job_to_scheduler(scheduler) # Add the job before starting
    #         scheduler.start()
    #         print("Scheduler started and tax job configured.")
    #     else:
    #         print("Scheduler already running.")
    # else:
    #     print("Scheduler not started in Werkzeug reloader process or already started by main process.")

    # Add WhiteNoise for static file serving in production
    from whitenoise import WhiteNoise
    # Serve static files from the 'static' directory under 'app'
    # The second argument is the prefix for the static URLs, e.g. /static/css/style.css
    app.wsgi_app = WhiteNoise(app.wsgi_app, root=os.path.join(os.path.dirname(__file__), 'static'), prefix='static/')
    # If your static files are at the root of the project (e.g. project_root/static)
    # and your app is in project_root/app, you might need:
    # static_root = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static')
    # app.wsgi_app = WhiteNoise(app.wsgi_app, root=static_root, prefix='static/')
    # For now, assuming static folder is app/static which is typical for Flask Blueprints.
    # The url_for('static', filename='css/style.css') should work with this.

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Import and register blueprints
    from app.routes.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from app.routes.main import bp as main_bp
    app.register_blueprint(main_bp)

    from app.routes.admin import bp as admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')

    from app.routes.banking import bp as banking_bp
    app.register_blueprint(banking_bp, url_prefix='/banking')

    from app.routes.taxes import bp as taxes_bp
    app.register_blueprint(taxes_bp, url_prefix='/taxes')

    from app.routes.dot import bp as dot_bp
    app.register_blueprint(dot_bp, url_prefix='/dot')

    from app.routes.marketplace import bp as marketplace_bp
    app.register_blueprint(marketplace_bp, url_prefix='/market')

    from app.routes.marketplace import bp as marketplace_bp
    app.register_blueprint(marketplace_bp, url_prefix='/marketplace')

    from app.routes.livemap import livemap_bp
    app.register_blueprint(livemap_bp, url_prefix='/livemap')

    from app.routes.auction import auction_bp
    app.register_blueprint(auction_bp, url_prefix='/auctions')

    from app.routes.messaging import messaging_bp
    app.register_blueprint(messaging_bp, url_prefix='/messages') # For user messages
    # Admin messaging routes are also in messaging_bp with /admin/messages prefix

    from app.routes.notifications import notifications_bp
    app.register_blueprint(notifications_bp, url_prefix='/notifications')

    # Create database tables if they don't exist
    # This is suitable for development/testing. For production, migrations (e.g. Alembic) are better.
    with app.app_context():
        print(f"Current DB URI for table creation: {app.config['SQLALCHEMY_DATABASE_URI']}")
        # For SQLite, create_all is generally safe.
        # For MySQL, ensure the database itself exists. create_all() will then create tables if they don't exist.
        # In a production setup with Render/MySQL, you'd typically use Alembic migrations.
        try:
            db.create_all()
            print("INFO: db.create_all() called. Tables created if they didn't exist (check logs for details).")
        except Exception as e:
            print(f"ERROR during db.create_all(): {e}")
            print("INFO: This might be an issue with database connection or permissions if using MySQL.")
            print("INFO: For MySQL, ensure the database specified in SQLALCHEMY_DATABASE_URI exists.")


    return app
