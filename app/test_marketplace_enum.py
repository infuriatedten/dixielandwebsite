import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from sqlalchemy import select
from dixielandwebsite import db
from dixielandwebsite.models import MarketplaceListing, MarketplaceListingStatus

def test_marketplace_enum():
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
