import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_apscheduler import APScheduler
from flask_migrate import Migrate
from whitenoise import WhiteNoise

from config import Config

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
scheduler = APScheduler()
migrate = Migrate()

import re
from jinja2 import pass_context
from markupsafe import Markup, escape

_paragraph_re = re.compile(r'(?:\r\n|\r|\n){2,}')

@pass_context
def nl2br(context, value):
    result = u'\n\n'.join(u'<p>%s</p>' % p.replace('\n', '<br>\n') \
        for p in _paragraph_re.split(escape(value)))
    if context.environment.autoescape:
        result = Markup(result)
    return result

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    app.jinja_env.filters['nl2br'] = nl2br

    # Fallback for placeholder or missing DB URI
    if not app.config.get('SQLALCHEMY_DATABASE_URI') or 'user:password@host/dbname' in app.config['SQLALCHEMY_DATABASE_URI']:
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        print("INFO: Using in-memory SQLite for app initialization (sandbox mode).")

    # Warn if using a default or missing SECRET_KEY
    if app.config.get('SECRET_KEY') in (None, '', 'your_secret_key'):
        print("WARNING: Using default or missing SECRET_KEY. Set a strong key in production!")

    # Setup WhiteNoise for static files
    static_dir = os.path.join(os.path.dirname(__file__), 'static')
    app.wsgi_app = WhiteNoise(app.wsgi_app, root=static_dir, prefix='static/')

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    scheduler.init_app(app)
    migrate.init_app(app, db)

    # Import models for SQLAlchemy
    from app.models import (
        User, Account, Transaction, TransactionType,
        TaxBracket, AutomatedTaxDeductionLog,
        Ticket, TicketStatus,
        PermitApplication, PermitApplicationStatus,
        MarketplaceListing, MarketplaceItemStatus,
        Inspection, UserRole
    )

    # Inject UserRole into templates
    @app.context_processor
    def inject_user_role():
        return dict(UserRole=UserRole)

    # User loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    with app.app_context():
        # Import and register blueprints
        from app.routes.auth import bp as auth_bp
        from app.routes.main import main_bp
        from app.routes.admin import admin_bp
        from app.routes.banking import bp as banking_bp
        from app.routes.taxes import bp as taxes_bp
        from app.routes.dot import bp as dot_bp
        from app.routes.marketplace import bp as marketplace_bp
        from app.routes.livemap import livemap_bp
        from app.routes.auction import auction_bp
        from app.routes.messaging import messaging_bp
        from app.routes.notifications import notifications_bp
        from app.routes.vehicle import bp as vehicle_bp

        app.register_blueprint(auth_bp, url_prefix='/auth')
        app.register_blueprint(main_bp)
        app.register_blueprint(admin_bp)
        app.register_blueprint(vehicle_bp, url_prefix='/vehicle')
        app.register_blueprint(banking_bp, url_prefix='/banking')
        app.register_blueprint(taxes_bp, url_prefix='/taxes')
        app.register_blueprint(dot_bp, url_prefix='/dot')
        app.register_blueprint(marketplace_bp, url_prefix='/marketplace')
        app.register_blueprint(livemap_bp, url_prefix='/livemap')
        app.register_blueprint(auction_bp, url_prefix='/auctions')
        app.register_blueprint(messaging_bp, url_prefix='/messages')
        app.register_blueprint(notifications_bp, url_prefix='/notifications')

        # Auto-create tables (dev only — use migrations in prod)
        print(f"Current DB URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
        try:
            db.create_all()
            print("INFO: Database tables created or already exist.")
        except Exception as e:
            print(f"ERROR during db.create_all(): {e}")

    return app
