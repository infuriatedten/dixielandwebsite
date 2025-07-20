import unittest
from unittest.mock import patch, MagicMock
from app import create_app, db
from app.models import User, MarketplaceListing, MarketplaceListingStatus, Account
from config import Config
from flask_login import login_user

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    DISCORD_STORE_SALES_WEBHOOK_URL = 'https://discord.com/api/webhooks/123/test-store-sales'
    DISCORD_PRODUCT_UPDATES_WEBHOOK_URL = 'https://discord.com/api/webhooks/456/test-product-updates'
    SERVER_NAME = 'localhost'

class DiscordIntegrationTestCase(unittest.TestCase):
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

    @patch('app.services.discord_webhook_service._post_to_discord')
    def test_create_listing_sends_store_sale_notification(self, mock_post_to_discord):
        mock_post_to_discord.return_value = True

        listing_data = {
            'item_name': 'Test Item',
            'description': 'Test Description',
            'price': 100.0,
            'quantity': 1,
            'unit': 'pcs'
        }

        response = self.client.post('/marketplace/new', data=listing_data, follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        mock_post_to_discord.assert_called_once()
        webhook_url_called = mock_post_to_discord.call_args[0][0]
        self.assertEqual(webhook_url_called, TestConfig.DISCORD_STORE_SALES_WEBHOOK_URL)

    @patch('app.services.discord_webhook_service._post_to_discord')
    def test_update_listing_sends_product_update_notification(self, mock_post_to_discord):
        mock_post_to_discord.return_value = True

        # Create a listing first
        listing = MarketplaceListing(
            seller_user_id=self.user.id,
            item_name='Original Item',
            description='Original Description',
            price=50.0,
            quantity=2,
            unit='pcs',
            status=MarketplaceListingStatus.AVAILABLE
        )
        db.session.add(listing)
        db.session.commit()

        updated_data = {
            'item_name': 'Updated Item',
            'description': 'Updated Description',
            'price': 75.0,
            'quantity': 1,
            'unit': 'pcs'
        }

        response = self.client.post(f'/marketplace/listing/{listing.id}/edit', data=updated_data, follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        mock_post_to_discord.assert_called_once()
        webhook_url_called = mock_post_to_discord.call_args[0][0]
        self.assertEqual(webhook_url_called, TestConfig.DISCORD_PRODUCT_UPDATES_WEBHOOK_URL)

if __name__ == '__main__':
    unittest.main()
