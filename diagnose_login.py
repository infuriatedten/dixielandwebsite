from app import create_app, db
from app.models import User

def check_admin_credentials():
    app = create_app()
    with app.app_context():
        user = User.query.filter_by(username='admin').first()
        if user:
            print(f"Admin user found: {user}")
            print(f"Password correct: {user.check_password('admin')}")
            print(f"User role: {user.role}")
        else:
            print("Admin user not found.")

if __name__ == '__main__':
    check_admin_credentials()
