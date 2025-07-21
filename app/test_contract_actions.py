import unittest
from app import create_app, db
from app.models import User, Contract, ContractStatus, Account, Transaction
from config import Config
from flask_login import login_user

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    SERVER_NAME = 'localhost'

class ContractActionsTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = self.app.test_client()

        # Create users and log in
        self.user1 = User(username='user1', email='user1@example.com')
        self.user1.set_password('password')
        self.user2 = User(username='user2', email='user2@example.com')
        self.user2.set_password('password')
        db.session.add_all([self.user1, self.user2])
        db.session.commit()

        with self.app.test_request_context():
            login_user(self.user1)

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_delete_contract(self):
        # Create a contract
        contract = Contract(title='Test Contract', description='Test Description', reward=100.0, creator_id=self.user1.id)
        db.session.add(contract)
        db.session.commit()

        response = self.client.post(f'/contract/{contract.id}/delete', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Contract deleted successfully!', response.data)

        # Verify the contract is deleted
        deleted_contract = Contract.query.get(contract.id)
        self.assertIsNone(deleted_contract)

    def test_complete_contract(self):
        # Create a contract and an account for the claimant
        contract = Contract(title='Test Contract', description='Test Description', reward=100.0, creator_id=self.user1.id, claimant_id=self.user2.id, status=ContractStatus.CLAIMED)
        account = Account(user_id=self.user2.id, balance=0)
        db.session.add_all([contract, account])
        db.session.commit()

        # Log in as the claimant
        with self.app.test_request_context():
            login_user(self.user2)

        response = self.client.post(f'/contract/{contract.id}/complete', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Contract completed successfully!', response.data)

        # Verify the contract is completed and the reward is transferred
        completed_contract = Contract.query.get(contract.id)
        self.assertEqual(completed_contract.status, ContractStatus.COMPLETED)
        self.assertEqual(account.balance, 100.0)
        transaction = Transaction.query.filter_by(account_id=account.id).first()
        self.assertIsNotNone(transaction)
        self.assertEqual(transaction.amount, 100.0)

if __name__ == '__main__':
    unittest.main()
