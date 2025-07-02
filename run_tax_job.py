# This script is intended to be run by a Render Cron Job.
# It initializes the Flask app context and calls the tax collection function.

from app import create_app
from app.jobs.taxes import apply_weekly_taxes
import os

if __name__ == "__main__":
    # Create a Flask app instance
    # It needs to be configured to connect to the database, so environment variables
    # like DATABASE_URL must be available in the Cron Job's environment.
    app = create_app()

    # The apply_weekly_taxes function already uses app.app_context(),
    # but for standalone scripts, it's good practice to ensure an app context.
    with app.app_context():
        print("Starting manual run of weekly tax collection job...")
        try:
            apply_weekly_taxes()
            print("Weekly tax collection job completed successfully.")
        except Exception as e:
            # Use app.logger if configured and desired, or just print for cron job logs
            app.logger.error(f"Error during scheduled tax collection: {e}", exc_info=True)
            # print(f"ERROR during scheduled tax collection: {e}") # Simpler for direct cron output
            # Consider more robust error reporting here if needed (e.g., Sentry, email)

    print("Tax job script finished.")
