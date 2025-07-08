import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_apscheduler import APScheduler
from whitenoise import WhiteNoise

from config import Config

# Initialize extensions globally (so they can be imported elsewhere)
db = SQLAlchemy()
login_manager = LoginManager()
scheduler = APScheduler()

# Configure login manager defaults
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Check and fallback for placeholder or missing DATABASE_URL
    db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
    if not db_uri or 'user:password@host/dbname' in db_uri or 'sqlite:///:memory:' in db_uri:
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        print("INFO: Using in-memory SQLite for application initialization in sandbox mode.")

    # Warn if SECRET_KEY is default or missing
    if app.config.get('SECRET_KEY') in (None, '', 'your_secret_key'):
        print("WARNING: Using default or missing SECRET_KEY. Set a strong SECRET_KEY in your environment or config.py for production.")

    # Initialize Flask extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    scheduler.init_app(app)  # If you plan to use scheduler

    # Import models here to register with SQLAlchemy
    from app.models import (
        User, Account, Transaction, TransactionType,
        TaxBracket, AutomatedTaxDeductionLog,
        Ticket, TicketStatus,
        PermitApplication, PermitApplicationStatus,
        MarketplaceListing, MarketplaceItemStatus,
        Inspection,
        UserRole  # For injecting into templates
    )

    # Inject UserRole enum/class into all Jinja templates
    @app.context_processor
    def inject_user_role():
        return dict(UserRole=UserRole)

    # Setup WhiteNoise for static file serving
    static_dir = os.path.join(os.path.dirname(__file__), 'static')
    app.wsgi_app = WhiteNoise(app.wsgi_app, root=static_dir, prefix='static/')

    # User loader callback for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register Blueprints with URL prefixes where needed
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
    app.register_blueprint(marketplace_bp, url_prefix='/marketplace')

    from app.routes.livemap import livemap_bp
    app.register_blueprint(livemap_bp, url_prefix='/livemap')

    from app.routes.auction import auction_bp
    app.register_blueprint(auction_bp, url_prefix='/auctions')

    from app.routes.messaging import messaging_bp
    app.register_blueprint(messaging_bp, url_prefix='/messages')

    from app.routes.notifications import notifications_bp
    app.register_blueprint(notifications_bp, url_prefix='/notifications')

    # Create tables on startup (handle exceptions gracefully)
    with app.app_context():
        print(f"Current DB URI for table creation: {app.config['SQLALCHEMY_DATABASE_URI']}")
        try:
            db.create_all()
            print("INFO: Database tables created or already exist.")
        except Exception as e:
            print(f"ERROR during db.create_all(): {e}")
            print("INFO: Check your database connection and permissions.")

    return app
