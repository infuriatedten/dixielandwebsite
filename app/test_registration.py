import unittest
from app import create_app, db
from app.models import User, Farmer, Company
from config import Config

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    SERVER_NAME = 'localhost'

class RegistrationTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_register_farmer(self):
        user_data = {
            'username': 'testfarmer',
            'email': 'farmer@example.com',
            'password': 'password',
            'password2': 'password',
            'account_type': 'farmer'
        }

        response = self.client.post('/auth/register', data=user_data, follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        # Verify the user and farmer are created
        user = User.query.filter_by(username='testfarmer').first()
        self.assertIsNotNone(user)
        farmer = Farmer.query.filter_by(user_id=user.id).first()
        self.assertIsNotNone(farmer)

    def test_register_company(self):
        user_data = {
            'username': 'testcompany',
            'email': 'company@example.com',
            'password': 'password',
            'password2': 'password',
            'account_type': 'company'
        }

        response = self.client.post('/auth/register', data=user_data, follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        # Verify the user and company are created
        user = User.query.filter_by(username='testcompany').first()
        self.assertIsNotNone(user)
        company = Company.query.filter_by(user_id=user.id).first()
        self.assertIsNotNone(company)
        self.assertEqual(company.name, "testcompany's Company")

if __name__ == '__main__':
    unittest.main()
