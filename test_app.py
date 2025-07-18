import unittest
from flask import url_for
from app import create_app, db
from app.models import MarketplaceListingStatus, User, MarketplaceListing
from config import Config
from sqlalchemy import select


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SERVER_NAME = 'localhost'


class TestApp(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestingConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        # Create a dummy user
        user = User(username='testuser', email='test@test.com')
        user.set_password('password')
        db.session.add(user)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_marketplace_enum(self):
        # Query the user
        user = db.session.execute(select(User).filter_by(username='testuser')).scalar_one()

        # Create a dummy listing
        listing = MarketplaceListing(
            seller_user_id=user.id,
            item_name="Test Item",
            description="Test Description",
            price=10.00,
            quantity=1,
            unit="unit",
            status=MarketplaceListingStatus.AVAILABLE
        )
        db.session.add(listing)
        db.session.commit()

        # Query the listing
        retrieved_listing = db.session.execute(select(MarketplaceListing).filter_by(id=listing.id)).scalar_one()

        # Check the status
        self.assertEqual(retrieved_listing.status, MarketplaceListingStatus.AVAILABLE)

    def test_admin_dashboard(self):
        with self.app.test_client() as client:
            # First, login as an admin user
            from app.models import UserRole
            from flask_login import login_user
            from flask import url_for
            user = User(username='admin', email='admin@admin.com', role=UserRole.ADMIN)
            user.set_password('password')
            db.session.add(user)
            db.session.commit()

            with self.app.test_request_context():
                login_user(user)

            # Then, access the admin dashboard
            response = client.get('/admin/', follow_redirects=True)
            self.assertEqual(response.status_code, 200)

    def test_delete_user_with_relations(self):
        with self.app.test_client() as client:
            # First, login as an admin user
            from app.models import UserRole, Account
            from flask_login import login_user
            user = User(username='admin', email='admin@admin.com', role=UserRole.ADMIN)
            user.set_password('password')
            db.session.add(user)
            db.session.commit()

            # Create a user with an account
            user_with_account = User(username='testuser2', email='test2@test.com')
            user_with_account.set_password('password')
            db.session.add(user_with_account)
            db.session.commit()
            account = Account(user_id=user_with_account.id, balance=100)
            db.session.add(account)
            db.session.commit()

            with self.app.test_request_context():
                login_user(user)

            # Then, try to delete the user
            response = client.post(f'/admin/user/{user_with_account.id}/delete', follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'Cannot delete user with related objects.', response.data)

    def test_admin_list_all_conversations(self):
        with self.app.test_client() as client:
            # First, login as an admin user
            from app.models import UserRole
            from flask_login import login_user
            user = User(username='admin2', email='admin2@admin.com', role=UserRole.ADMIN)
            user.set_password('password')
            db.session.add(user)
            db.session.commit()

            with self.app.test_request_context():
                login_user(user)

            # Then, access the admin conversations list
            response = client.get(url_for('admin.admin_list_all_conversations'), follow_redirects=True)
            self.assertEqual(response.status_code, 200)

    def test_edit_tax_bracket_invalid(self):
        with self.app.test_client() as client:
            # First, login as an admin user
            from app.models import UserRole
            from flask_login import login_user
            user = User(username='admin', email='admin@admin.com', role=UserRole.ADMIN)
            user.set_password('password')
            db.session.add(user)
            db.session.commit()

            with self.app.test_request_context():
                login_user(user)

            # Then, try to edit a tax bracket with invalid data
            from app.models import TaxBracket
            tax_bracket = TaxBracket(name='test', min_balance=100, max_balance=50, tax_rate=10)
            db.session.add(tax_bracket)
            db.session.commit()
            response = client.post(f'/admin/tax_bracket/{tax_bracket.id}/edit', data=dict(
                name='test',
                min_balance=100,
                max_balance=50,
                tax_rate=10
            ), follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'Max Balance must be greater than Min Balance.', response.data)

    def test_view_ticket_detail_no_account(self):
        with self.app.test_client() as client:
            # First, login as a user
            from app.models import UserRole, Ticket, TicketStatus
            from flask_login import login_user
            user = User(username='testuser3', email='test3@test.com', role=UserRole.USER)
            user.set_password('password')
            db.session.add(user)
            db.session.commit()

            # Create a ticket for the user
            from datetime import datetime, timedelta
            ticket = Ticket(issued_to_user_id=user.id, issued_by_officer_id=user.id, violation_details='test', fine_amount=100, status=TicketStatus.OUTSTANDING, due_date=datetime.utcnow() + timedelta(days=1))
            db.session.add(ticket)
            db.session.commit()

            with self.app.test_request_context():
                login_user(user)

            # Then, access the ticket details page
            response = client.get(f'/dot/ticket/{ticket.id}', follow_redirects=True)
            self.assertEqual(response.status_code, 200)

    def test_farmers_no_farmer(self):
        with self.app.test_client() as client:
            # First, login as a user
            from app.models import UserRole
            from flask_login import login_user
            user = User(username='testuser4', email='test4@test.com', role=UserRole.USER)
            user.set_password('password')
            db.session.add(user)
            db.session.commit()

            with self.app.test_request_context():
                login_user(user)

            # Then, access the farmers page
            response = client.get('/farmers', follow_redirects=True)
            self.assertEqual(response.status_code, 200)

    def test_company_no_company(self):
        with self.app.test_client() as client:
            # First, login as a user
            from app.models import UserRole
            from flask_login import login_user
            user = User(username='testuser5', email='test5@test.com', role=UserRole.USER)
            user.set_password('password')
            db.session.add(user)
            db.session.commit()

            with self.app.test_request_context():
                login_user(user)

            # Then, access the company page
            response = client.get('/company', follow_redirects=True)
            self.assertEqual(response.status_code, 200)

    def test_edit_account_balance(self):
        with self.app.test_client() as client:
            # First, login as an admin user
            from app.models import UserRole, Account
            from flask_login import login_user
            user = User(username='admin5', email='admin5@admin.com', role=UserRole.ADMIN)
            user.set_password('password')
            db.session.add(user)
            db.session.commit()

            # Create an account
            account = Account(user_id=user.id, balance=100)
            db.session.add(account)
            db.session.commit()

            with self.app.test_request_context():
                login_user(user)

            # Then, edit the account balance
            response = client.post(url_for('admin.edit_account_balance', account_id=account.id), data=dict(
                amount=50,
                description='test description'
            ), follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'Account balance updated successfully.', response.data)
            self.assertEqual(account.balance, 150)

    def test_edit_user_existing_username(self):
        with self.app.test_client() as client:
            # First, login as an admin user
            from app.models import UserRole
            from flask_login import login_user
            admin = User(username='admin9', email='admin9@admin.com', role=UserRole.ADMIN)
            admin.set_password('password')
            db.session.add(admin)
            db.session.commit()

            # Create a user to edit
            user_to_edit = User(username='user_to_edit4', email='user_to_edit4@test.com')
            user_to_edit.set_password('password')
            db.session.add(user_to_edit)
            db.session.commit()

            # Create another user with the username we're trying to use
            existing_user = User(username='existing_user4', email='existing_user4@test.com')
            existing_user.set_password('password')
            db.session.add(existing_user)
            db.session.commit()

            with self.app.test_request_context():
                login_user(admin)

            # Then, try to edit the user
            response = client.post(url_for('admin.edit_user', user_id=user_to_edit.id), data=dict(
                username='existing_user4',
                email='new_email4@test.com',
                role='USER',
                discord_user_id='',
                region='US'
            ), follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'Please use a different username.', response.data)


if __name__ == '__main__':
    unittest.main()
