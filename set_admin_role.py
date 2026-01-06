from app import create_app, db
from app.models import User, UserRole

app = create_app()

with app.app_context():
    user = User.query.filter_by(username='admin').first()
    if user:
        print(f"User '{user.username}' found. Current role: {user.role}")
        if user.role != UserRole.ADMIN:
            print("Updating role to ADMIN.")
            user.role = UserRole.ADMIN
            db.session.commit()
            print("Role updated successfully.")
        else:
            print("User already has ADMIN role.")
    else:
        print("User 'admin' not found.")
