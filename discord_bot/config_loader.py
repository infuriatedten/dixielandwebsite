import os
from dotenv import load_dotenv

# Load environment variables from a .env file if it exists
# Useful for development. In production (like Render), these will be set in the environment.
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

class BotConfig:
    DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
    DISCORD_SERVER_ID = os.getenv("DISCORD_SERVER_ID")
    MARKETPLACE_CHANNEL_ID = os.getenv("MARKETPLACE_CHANNEL_ID")
    MARKETPLACE_WEBHOOK_URL = os.getenv("MARKETPLACE_WEBHOOK_URL")
    DATABASE_URL = os.getenv("DATABASE_URL")
    WEB_APP_BASE_URL = os.getenv("WEB_APP_BASE_URL", "http://localhost:5000") # Default for local dev
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

    @staticmethod
    def validate():
        required_vars = [
            "DISCORD_BOT_TOKEN",
            "DISCORD_SERVER_ID",
            "MARKETPLACE_CHANNEL_ID",
            "MARKETPLACE_WEBHOOK_URL",
            "DATABASE_URL"
        ]
        missing_vars = [var for var in required_vars if not getattr(BotConfig, var)]
        if missing_vars:
            raise ValueError(f"Missing required environment variables for the bot: {', '.join(missing_vars)}")

        print("Bot configuration loaded and validated successfully.")
        print(f"  Marketplace Channel ID: {BotConfig.MARKETPLACE_CHANNEL_ID}")
        print(f"  Marketplace Webhook URL: {'Configured' if BotConfig.MARKETPLACE_WEBHOOK_URL else 'Not Configured'}")
        print(f"  Web App Base URL: {BotConfig.WEB_APP_BASE_URL}")


if __name__ == "__main__":
    # This is for testing the config loader itself
    try:
        BotConfig.validate()
        print(f"Token: {BotConfig.DISCORD_BOT_TOKEN[:5]}...") # Print part of token for confirmation
    except ValueError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
