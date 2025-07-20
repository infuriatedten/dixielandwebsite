import unittest
import asyncio
from unittest.mock import MagicMock, AsyncMock
from discord.ext import commands
from app import create_app, db
from app.models import User, Contract, ContractStatus
from discord_bot.cogs.contracts_cog import ContractsCog
from config import Config
import discord

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

class ContractsCogTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        intents = discord.Intents.default()
        self.bot = commands.Bot(command_prefix='!', intents=intents)
        self.cog = ContractsCog(self.bot)

        # Create a user
        self.user = User(username='testuser', email='test@example.com', discord_user_id='12345')
        self.user.set_password('password')
        db.session.add(self.user)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_claim_contract(self):
        async def run_test():
            # Create a contract
            contract = Contract(title='Test Contract', description='Test Description', reward=100.0, creator_id=self.user.id)
            db.session.add(contract)
            db.session.commit()

            # Mock the context
            ctx = AsyncMock()
            ctx.author.id = 12345

            # Call the command
            await self.cog.claim_contract.callback(self.cog, ctx, contract.id)

            # Assertions
            ctx.send.assert_called_once_with(f"You have successfully claimed contract {contract.id}: {contract.title}.")
            claimed_contract = Contract.query.get(contract.id)
            self.assertEqual(claimed_contract.status, ContractStatus.CLAIMED)
            self.assertEqual(claimed_contract.claimant_id, self.user.id)

        asyncio.run(run_test())

if __name__ == '__main__':
    unittest.main()
