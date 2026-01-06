from app import create_app, db
from app.models import User, UserRole

app = create_app()

with app.app_context():
    new_admin = User(
        username='new_admin',
        email='new_admin@example.com',
        role=UserRole.ADMIN
    )
    new_admin.set_password('password')
    db.session.add(new_admin)
    db.session.commit()
    print("New admin user created successfully.")
