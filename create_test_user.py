
import os
import sys
from dotenv import load_dotenv

# Add the app directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

load_dotenv()

from app import create_app, db
from app.models import User, UserRole

app = create_app()

def create_test_user():
    with app.app_context():
        # Check if the user already exists
        if User.query.filter_by(email='test@example.com').first() is None:
            # Create a new user
            user = User(
                username='testuser',
                email='test@example.com',
                role=UserRole.ADMIN
            )
            user.set_password('password')
            db.session.add(user)
            db.session.commit()
            print("Test user created successfully.")
        else:
            print("Test user already exists.")

if __name__ == '__main__':
    create_test_user()
