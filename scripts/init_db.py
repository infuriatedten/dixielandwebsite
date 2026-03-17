import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db

print("Creating app...")
app = create_app()
print("App created.")

with app.app_context():
    print("Creating all tables...")
    db.create_all()
    print("All tables created.")
    print("Database initialized.")
