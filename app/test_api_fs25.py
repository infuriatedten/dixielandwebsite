import unittest
import json
from app import create_app, db
from app.models import User, Farmer, Account, FarmerStats, Notification, Conversation
from config import Config

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    SERVER_NAME = 'localhost'

class ApiFs25TestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = self.app.test_client()

        # Create initial data for testing
        # 1. A user
        user = User(username='testfarmer', email='test@example.com')
        user.set_password('password')
        db.session.add(user)
        db.session.commit()

        # 2. A farmer profile linked to the user
        farmer = Farmer(user_id=user.id)
        db.session.add(farmer)
        db.session.commit()
        self.farmer_id = farmer.id

        # 3. A bank account for the user, starting with 1000
        account = Account(user_id=user.id, balance=1000.00)
        db.session.add(account)
        db.session.commit()

        # 4. An unread notification
        notification = Notification(user_id=user.id, message_text="Test notification", is_read=False)
        db.session.add(notification)

        # 5. A conversation with unread messages
        convo = Conversation(user_id=user.id, admin_id=user.id, user_unread_count=3) # admin can be same for test
        db.session.add(convo)
        db.session.commit()


    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_update_balance_success(self):
        """Test successful balance update."""
        response = self.client.post('/api/fs25/update_balance',
                                     data=json.dumps({'farmer_id': self.farmer_id, 'balance': 1500.50}),
                                     content_type='application/json')
        self.assertEqual(response.status_code, 200)
        json_response = response.get_json()
        self.assertEqual(json_response['status'], 'success')
        self.assertEqual(json_response['new_balance'], 1500.50)

        # Verify the balance in the database
        account = Account.query.first()
        self.assertEqual(float(account.balance), 1500.50)

    def test_update_balance_missing_farmer(self):
        """Test balance update with a non-existent farmer."""
        response = self.client.post('/api/fs25/update_balance',
                                     data=json.dumps({'farmer_id': 999, 'balance': 1500.50}),
                                     content_type='application/json')
        self.assertEqual(response.status_code, 404)

    def test_update_stats_create(self):
        """Test creating new farmer stats."""
        response = self.client.post('/api/fs25/update_stats',
                                     data=json.dumps({
                                         'farmer_id': self.farmer_id,
                                         'fields_owned': 5,
                                         'total_yield': 1234.5
                                     }),
                                     content_type='application/json')
        self.assertEqual(response.status_code, 200)

        stats = FarmerStats.query.filter_by(farmer_id=self.farmer_id).first()
        self.assertIsNotNone(stats)
        self.assertEqual(stats.fields_owned, 5)
        self.assertEqual(stats.total_yield, 1234.5)
        self.assertEqual(stats.equipment_owned, 0) # Should default to 0

    def test_update_stats_update(self):
        """Test updating existing farmer stats."""
        # First, create stats
        initial_stats = FarmerStats(farmer_id=self.farmer_id, fields_owned=2, equipment_owned=10)
        db.session.add(initial_stats)
        db.session.commit()

        # Now, update them
        response = self.client.post('/api/fs25/update_stats',
                                     data=json.dumps({
                                         'farmer_id': self.farmer_id,
                                         'fields_owned': 3,
                                         'equipment_owned': 12
                                     }),
                                     content_type='application/json')
        self.assertEqual(response.status_code, 200)

        stats = FarmerStats.query.filter_by(farmer_id=self.farmer_id).first()
        self.assertEqual(stats.fields_owned, 3)
        self.assertEqual(stats.equipment_owned, 12)

    def test_get_notifications(self):
        """Test fetching notifications and unread message counts."""
        response = self.client.get(f'/api/fs25/get_notifications?farmer_id={self.farmer_id}')
        self.assertEqual(response.status_code, 200)

        json_response = response.get_json()
        self.assertEqual(json_response['farmer_id'], str(self.farmer_id))
        self.assertEqual(json_response['unread_notifications'], 1)
        self.assertEqual(json_response['unread_messages'], 3)

    def test_get_notifications_no_farmer(self):
        """Test fetching notifications for a non-existent farmer."""
        response = self.client.get('/api/fs25/get_notifications?farmer_id=999')
        self.assertEqual(response.status_code, 404)

if __name__ == '__main__':
    unittest.main()
