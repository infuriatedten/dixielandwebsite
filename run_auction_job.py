# This script is intended to be run by a Render Cron Job (or similar scheduler).
# It initializes the Flask app context and calls the auction closing job function.

from app import create_app
from app.jobs.auctions import close_completed_auctions_job # Corrected import path
import os

if __name__ == "__main__":
    app = create_app()

    with app.app_context():
        print("Starting scheduled run of auction closing job...")
        try:
            close_completed_auctions_job()
            print("Auction closing job completed successfully.")
        except Exception as e:
            app.logger.error(f"Error during scheduled auction closing job: {e}", exc_info=True)
            # For Render Cron, output to stdout/stderr is logged.
            print(f"ERROR during scheduled auction closing: {e}")

    print("Auction job script finished.")
