import unittest
from app import create_app, db
from app.models import User, Contract, ContractStatus
from config import Config
from flask_login import login_user

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    SERVER_NAME = 'localhost'

class ContractRoutesTestCase(unittest.TestCase):
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

    def test_contracts_page(self):
        response = self.client.get('/contracts')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'<h1>Contracts</h1>', response.data)

    def test_claim_contract(self):
        # Create a contract
        contract = Contract(title='Test Contract', description='Test Description', reward=100.0, creator_id=self.user.id)
        db.session.add(contract)
        db.session.commit()

        response = self.client.post(f'/contract/{contract.id}/claim', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Contract claimed successfully!', response.data)

        # Verify the contract status is updated
        claimed_contract = Contract.query.get(contract.id)
        self.assertEqual(claimed_contract.status, ContractStatus.CLAIMED)
        self.assertEqual(claimed_contract.claimant_id, self.user.id)

if __name__ == '__main__':
    unittest.main()
