import unittest
from app import create_app, db
from app.models import User, Contract
from config import Config
from flask_login import login_user

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    SERVER_NAME = 'localhost'

class CreateContractTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = self.app.test_client()

        # Create a user and log in
        self.user = User(username='testuser', email='test@example.com')
        self.user.set_password('password')
        db.session.add(self.user)
        db.session.commit()

        with self.app.test_request_context():
            login_user(self.user)

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_create_contract_page(self):
        response = self.client.get('/contracts/create')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'<h1>Create Contract</h1>', response.data)

    def test_create_contract(self):
        contract_data = {
            'title': 'Test Contract',
            'description': 'Test Description',
            'reward': 100.0
        }

        response = self.client.post('/contracts/create', data=contract_data, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Contract created successfully!', response.data)

        # Verify the contract is created
        contract = Contract.query.filter_by(title='Test Contract').first()
        self.assertIsNotNone(contract)
        self.assertEqual(contract.creator_id, self.user.id)

if __name__ == '__main__':
    unittest.main()
