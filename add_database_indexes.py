
from app import create_app, db
from sqlalchemy import Index

app = create_app()

with app.app_context():
    # Add indexes for better performance
    db.engine.execute('CREATE INDEX IF NOT EXISTS idx_tickets_status_date ON tickets(status, issue_date)')
    db.engine.execute('CREATE INDEX IF NOT EXISTS idx_transactions_type_timestamp ON transactions(type, timestamp)')
    db.engine.execute('CREATE INDEX IF NOT EXISTS idx_marketplace_status_creation ON marketplace_listings(status, creation_date)')
    db.engine.execute('CREATE INDEX IF NOT EXISTS idx_notifications_user_read ON notifications(user_id, is_read)')
    db.engine.execute('CREATE INDEX IF NOT EXISTS idx_auctions_status_end_time ON auction_items(status, current_end_time)')
    db.engine.execute('CREATE INDEX IF NOT EXISTS idx_permits_status_app_date ON permit_applications(status, application_date)')
    
    print("Database indexes added successfully!")
