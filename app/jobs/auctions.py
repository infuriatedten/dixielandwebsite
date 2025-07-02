from app import db # Assuming scheduler is initialized in create_app and db is accessible
# If using Render Cron job, app context needs to be handled by the calling script (e.g. run_auction_job.py)
# from flask import current_app
from app.models import AuctionItem, AuctionBid, AuctionStatus
from datetime import datetime, timedelta

def close_completed_auctions_job():
    """
    Scheduled job to find auctions that have ended and determine winners.
    Payment processing will be handled in Phase 2 of Auction House development.
    This job primarily updates statuses to SOLD_AWAITING_PAYMENT or EXPIRED_NO_BIDS.
    """
    # If run by an external script (like run_auction_job.py), that script should create an app_context.
    # If run by APScheduler integrated with Flask, scheduler.app.app_context() is used.
    # For simplicity here, assuming context is handled by caller or by Flask's @scheduler.task decorator if used.

    # from flask import current_app as app_flask # Use if not using 'with app.app_context()' from caller
    # with app_flask.app_context(): # Ensure app context if needed here

    print(f"[{datetime.utcnow()}] Running job: Close Completed Auctions...")

    auctions_to_close = AuctionItem.query.filter(
        AuctionItem.status == AuctionStatus.ACTIVE,
        AuctionItem.current_end_time <= datetime.utcnow()
    ).all()

    closed_count = 0
    expired_count = 0

    if not auctions_to_close:
        print("No active auctions have reached their end time.")
        return

    for auction in auctions_to_close:
        print(f"Processing auction ID: {auction.id} ('{auction.item_name}') which ended at {auction.current_end_time}")
        highest_bid = auction.bids.order_by(AuctionBid.bid_amount.desc(), AuctionBid.bid_time.asc()).first()

        if highest_bid:
            auction.status = AuctionStatus.SOLD_AWAITING_PAYMENT # Phase 1: Mark for payment processing
            auction.winning_bid_id = highest_bid.id
            auction.winner_user_id = highest_bid.bidder_user_id
            print(f"  Auction ID {auction.id} won by User ID {highest_bid.bidder_user_id} with bid {highest_bid.bid_amount}.")
            # TODO Phase 2: Initiate payment deduction.
            # TODO Phase 2: Initiate seller payout.
            closed_count += 1
        else:
            auction.status = AuctionStatus.EXPIRED_NO_BIDS
            print(f"  Auction ID {auction.id} expired with no bids.")
            expired_count += 1

        try:
            db.session.add(auction) # Add to session to save changes
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            # Use app.logger if available and configured
            print(f"  ERROR updating auction {auction.id}: {str(e)}")
            # current_app.logger.error(f"Error updating auction {auction.id} status: {e}", exc_info=True)


    print(f"Auction closing job finished. Auctions marked for payment: {closed_count}. Auctions expired: {expired_count}.")


# Example of how this might be called from a Render Cron Job script (run_auction_job.py)
if __name__ == '__main__':
    # This part is for direct testing of the job logic.
    # In production, run_auction_job.py would set up the app context.
    # from app import create_app # Assuming create_app is accessible
    # app_instance = create_app()
    # with app_instance.app_context():
    #     close_completed_auctions_job()
    print("This script (app/jobs/auctions.py) is intended to be called by a scheduler or a wrapper script like run_auction_job.py.")
