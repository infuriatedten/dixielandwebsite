import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your_secret_key' # Replace with a real secret key in production
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'mysql+pymysql://user:password@host/dbname' # Replace with your MySQL connection string
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True # For CSRF protection with Flask-WTF if we add forms
    # For Render.com, DATABASE_URL will be set by Render's MySQL service
    # Example for local development: 'mysql+pymysql://root:your_local_password@localhost/game_website_db'
    # Ensure the database 'game_website_db' (or your chosen name) is created in MySQL first.
    # For Render, it will look something like: 'mysql+pymysql://USERNAME:PASSWORD@HOST/DATABASE_NAME' provided by Render

    # Example for a local setup, replace with your actual credentials and database name
    # SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:root@localhost/game_website_db'
    # Remember to create the database in MySQL: CREATE DATABASE game_website_db;
    # And set your actual root password or a dedicated user/password.

    # For Render, you'll set DATABASE_URL in the environment variables on the Render dashboard.
    # For local testing, you might set it in your shell:
    # export DATABASE_URL='mysql+pymysql://your_user:your_password@your_host/your_db'
    # export SECRET_KEY='a_very_strong_random_secret_key_here'

    # For now, I will use a placeholder that needs to be configured.
    # To run locally, you'd uncomment and set the local URI or set DATABASE_URL in your environment.
    # For this agent environment, these will be placeholders.
    if not SQLALCHEMY_DATABASE_URI or 'user:password@host/dbname' in SQLALCHEMY_DATABASE_URI:
        print("WARNING: DATABASE_URL is not configured or using default placeholder. Please set it for proper operation.")
        # Fallback for sandbox if not set, though this won't actually connect.
        SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:' # Use in-memory SQLite if no real DB is configured for sandbox. This is NOT for production.
        print("Fell back to in-memory SQLite for sandbox mode.")

    if SECRET_KEY == 'your_secret_key':
        print("WARNING: SECRET_KEY is not configured or using default placeholder. Please set a strong secret key.")

    # Discord Integration Settings
    DISCORD_WEBHOOK_URL = os.environ.get('DISCORD_WEBHOOK_URL') # For marketplace listings
    DISCORD_BOT_TOKEN = os.environ.get('DISCORD_BOT_TOKEN') # For bot commands (Phase 2)
    DISCORD_MARKETPLACE_CHANNEL_ID = os.environ.get('DISCORD_MARKETPLACE_CHANNEL_ID') # For bot reference (Phase 2)

    # Example Webhook URL (replace with your actual webhook)
    # DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/your_webhook_id/your_webhook_token"

    if not DISCORD_WEBHOOK_URL:
        print("WARNING: DISCORD_WEBHOOK_URL is not set. Marketplace listings will not be posted to Discord.")

    # Livemap XML Access Configuration
    LIVEMAP_XML_ACCESS_METHOD = os.environ.get('LIVEMAP_XML_ACCESS_METHOD', 'SCP') # 'SCP', 'FTP', or 'LOCAL_PATH'

    # For SCP/FTP
    LIVEMAP_REMOTE_HOST = os.environ.get('LIVEMAP_REMOTE_HOST', 'your_game_server_ip_or_hostname')
    LIVEMAP_REMOTE_PORT = int(os.environ.get('LIVEMAP_REMOTE_PORT', 22)) # Default SSH port for SCP
    LIVEMAP_REMOTE_USER = os.environ.get('LIVEMAP_REMOTE_USER', 'your_scp_ftp_user')
    LIVEMAP_REMOTE_PASSWORD = os.environ.get('LIVEMAP_REMOTE_PASSWORD', None) # Set as env var for security
    LIVEMAP_SSH_KEY_PATH = os.environ.get('LIVEMAP_SSH_KEY_PATH', None) # Path to private key file if using key auth for SCP
                                                                    # For Render, content of key might be stored in env var, then written to temp file.

    # Paths to XML files (remote if SCP/FTP, local if LOCAL_PATH)
    LIVEMAP_REMOTE_PATH_DYNAMIC = os.environ.get('LIVEMAP_REMOTE_PATH_DYNAMIC', '/path/on/game/server/modSettings/livemap_dynamic.xml')
    LIVEMAP_REMOTE_PATH_STATIC = os.environ.get('LIVEMAP_REMOTE_PATH_STATIC', '/path/on/game/server/modSettings/livemap_static.xml')

    # For LOCAL_PATH method (if files are synced to where Flask app can read them directly)
    LIVEMAP_LOCAL_PATH_DYNAMIC = os.environ.get('LIVEMAP_LOCAL_PATH_DYNAMIC', 'data/livemap_dynamic.xml') # Example local path
    LIVEMAP_LOCAL_PATH_STATIC = os.environ.get('LIVEMAP_LOCAL_PATH_STATIC', 'data/livemap_static.xml')   # Example local path

    # Warning if essential SCP/FTP details are missing and method is SCP/FTP
    if LIVEMAP_XML_ACCESS_METHOD in ['SCP', 'FTP']:
        if 'your_game_server_ip_or_hostname' in LIVEMAP_REMOTE_HOST or \
           'your_scp_ftp_user' in LIVEMAP_REMOTE_USER or \
           (not LIVEMAP_REMOTE_PASSWORD and not LIVEMAP_SSH_KEY_PATH and LIVEMAP_XML_ACCESS_METHOD == 'SCP'): # Password or key needed for SCP
            print(f"WARNING: Livemap access method is {LIVEMAP_XML_ACCESS_METHOD}, but remote host, user, or credentials seem to be placeholders or missing.")
    elif LIVEMAP_XML_ACCESS_METHOD == 'LOCAL_PATH':
        # Could add a check here if local paths are expected to exist, but might be noisy.
        pass

    # Auction House Configuration
    AUCTION_DEFAULT_DURATION_HOURS = int(os.environ.get('AUCTION_DEFAULT_DURATION_HOURS', 24))
    AUCTION_ANTI_SNIPE_THRESHOLD_MINUTES = int(os.environ.get('AUCTION_ANTI_SNIPE_THRESHOLD_MINUTES', 2))
    AUCTION_ANTI_SNIPE_EXTENSION_MINUTES = int(os.environ.get('AUCTION_ANTI_SNIPE_EXTENSION_MINUTES', 5))
    AUCTION_DEFAULT_MIN_BID_INCREMENT = float(os.environ.get('AUCTION_DEFAULT_MIN_BID_INCREMENT', 1.00))
    # AUCTION_HOUSE_COMMISSION_PERCENT = float(os.environ.get('AUCTION_HOUSE_COMMISSION_PERCENT', 0)) # No commission as per user
    AUCTION_JOB_RUN_INTERVAL_SECONDS = int(os.environ.get('AUCTION_JOB_RUN_INTERVAL_SECONDS', 60)) # How often auction closing job runs


# To generate a good secret key, you can use:
# import secrets
# secrets.token_hex(16)
