import os
import secrets
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    # Security
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(32)

    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        'sqlite:///:memory:'  # Fallback for dev/testing
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # CSRF Protection
    WTF_CSRF_ENABLED = True

    # Discord Integration
    DISCORD_WEBHOOK_URL = os.environ.get('DISCORD_WEBHOOK_URL')
    DISCORD_MARKETPLACE_CHANNEL_ID = os.environ.get('DISCORD_MARKETPLACE_CHANNEL_ID')
    DISCORD_BOT_TOKEN = os.environ.get('DISCORD_BOT_TOKEN')

    # Livemap Settings
    LIVEMAP_XML_ACCESS_METHOD = os.environ.get('LIVEMAP_XML_ACCESS_METHOD', 'SCP')
    LIVEMAP_REMOTE_HOST = os.environ.get('LIVEMAP_REMOTE_HOST')
    LIVEMAP_REMOTE_PORT = int(os.environ.get('LIVEMAP_REMOTE_PORT', 22))
    LIVEMAP_REMOTE_USER = os.environ.get('LIVEMAP_REMOTE_USER')
    LIVEMAP_REMOTE_PASSWORD = os.environ.get('LIVEMAP_REMOTE_PASSWORD')
    LIVEMAP_SSH_KEY_PATH = os.environ.get('LIVEMAP_SSH_KEY_PATH')

    LIVEMAP_REMOTE_PATH_DYNAMIC = os.environ.get(
        'LIVEMAP_REMOTE_PATH_DYNAMIC',
        '/path/on/game/server/modSettings/livemap_dynamic.xml'
    )
    LIVEMAP_REMOTE_PATH_STATIC = os.environ.get(
        'LIVEMAP_REMOTE_PATH_STATIC',
        '/path/on/game/server/modSettings/livemap_static.xml'
    )
    LIVEMAP_LOCAL_PATH_DYNAMIC = os.environ.get(
        'LIVEMAP_LOCAL_PATH_DYNAMIC',
        'data/livemap_dynamic.xml'
    )
    LIVEMAP_LOCAL_PATH_STATIC = os.environ.get(
        'LIVEMAP_LOCAL_PATH_STATIC',
        'data/livemap_static.xml'
    )

    # Auction House Settings
    AUCTION_DEFAULT_DURATION_HOURS = int(os.environ.get('AUCTION_DEFAULT_DURATION_HOURS', 24))
    AUCTION_ANTI_SNIPE_THRESHOLD_MINUTES = int(os.environ.get('AUCTION_ANTI_SNIPE_THRESHOLD_MINUTES', 2))
    AUCTION_ANTI_SNIPE_EXTENSION_MINUTES = int(os.environ.get('AUCTION_ANTI_SNIPE_EXTENSION_MINUTES', 5))
    AUCTION_DEFAULT_MIN_BID_INCREMENT = float(os.environ.get('AUCTION_DEFAULT_MIN_BID_INCREMENT', 1.0))
    AUCTION_JOB_RUN_INTERVAL_SECONDS = int(os.environ.get('AUCTION_JOB_RUN_INTERVAL_SECONDS', 60))
