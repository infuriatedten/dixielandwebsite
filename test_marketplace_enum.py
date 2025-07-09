import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from sqlalchemy import select
from app import create_app, db
from app.models import MarketplaceListing, MarketplaceListingStatus

app = create_app()

def test_marketplace_enum():
    with app.app_context():
        try:
            listings = db.session.execute(
                select(MarketplaceListing).where(MarketplaceListing.status == MarketplaceListingStatus.AVAILABLE)
            ).scalars().all()

            print(f"Found {len(listings)} listings with status AVAILABLE")
            for listing in listings:
                print(f"- {listing.item_name} (Status: {listing.status})")

        except Exception as e:
            print("Error during query:", e)

if __name__ == "__main__":
    test_marketplace_enum()