from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from app.models import Base # Import Base from your Flask app's models
from discord_bot.config_loader import BotConfig

# Ensure BotConfig is validated before using DATABASE_URL
try:
    BotConfig.validate()
except ValueError as e:
    print(f"CRITICAL: Bot configuration error: {e}")
    # Decide how to handle this - exit, or try to run with defaults that will fail?
    # For now, let it proceed and SQLAlchemy will likely fail if DATABASE_URL is missing.
    pass


engine = None
SessionLocal = None

def init_db(database_url=None):
    global engine, SessionLocal
    db_url = database_url or BotConfig.DATABASE_URL
    if not db_url:
        raise ValueError("DATABASE_URL is not configured for the bot. Cannot initialize database.")

    print(f"Bot attempting to connect to database: {db_url.split('@')[-1]}") # Avoid logging full URL with password

    engine = create_engine(db_url)

    # Create tables if they don't exist (useful if bot runs independently or first)
    # This assumes your Flask app's Base metadata is correctly imported.
    # Base.metadata.create_all(bind=engine)
    # It's generally better to let the main Flask app handle migrations/table creation.
    # The bot should primarily be a consumer of the existing schema.
    # If you must create tables from bot (e.g. for standalone testing), uncomment above.
    # For now, we assume tables are created by the Flask app.

    SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))
    print("Database engine and session configured for bot.")

def get_db_session():
    if not SessionLocal:
        # This might happen if init_db failed or wasn't called.
        # Attempt to initialize, but this could be problematic if BotConfig isn't fully loaded.
        print("WARNING: SessionLocal not initialized. Attempting to init_db() now.")
        try:
            init_db()
        except Exception as e:
            print(f"CRITICAL: Failed to initialize database session on demand: {e}")
            return None # Or raise an exception

    db = SessionLocal()
    try:
        # This is a simple check to see if the connection is alive.
        # db.execute("SELECT 1")
        # print("Database session obtained and connection seems live.")
        return db
    except Exception as e:
        print(f"Error obtaining or testing database session: {e}")
        db.close() # Ensure session is closed on error
        return None # Or raise an exception
    # finally:
        # The session should be closed by the caller, not here.
        # db.close()
        # print("DB Session closed by get_db_session (this should be done by caller)")


# Call init_db() once when this module is loaded if DATABASE_URL is available.
# This makes SessionLocal available for import elsewhere.
if BotConfig.DATABASE_URL:
    try:
        init_db()
    except ValueError as e:
        print(f"Database initialization failed: {e}")
    except Exception as e: # Catch other potential SQLAlchemy errors during init
        print(f"An unexpected error occurred during database initialization: {e}")
else:
    print("DATABASE_URL not set in BotConfig, bot database functions will not be available until initialized manually.")

if __name__ == "__main__":
    # Test database connection
    print("Testing bot's database connection...")
    if not SessionLocal:
        print("SessionLocal is None. init_db might have failed or DATABASE_URL is missing.")
    else:
        session = get_db_session()
        if session:
            print("Successfully obtained a database session.")
            try:
                # Example: Query for a user if User model is accessible
                from app.models import User
                user_count = session.query(User).count()
                print(f"Found {user_count} users in the database.")
            except Exception as e:
                print(f"Error querying database: {e}")
            finally:
                session.close()
                print("Test session closed.")
        else:
            print("Failed to obtain a database session.")
