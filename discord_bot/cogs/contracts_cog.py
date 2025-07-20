from discord.ext import commands
from app.models import Contract, User, ContractStatus
from app import db

class ContractsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='claim')
    async def claim_contract(self, ctx, contract_id: int):
        """Claims a contract by its ID."""
        user = User.query.filter_by(discord_user_id=str(ctx.author.id)).first()
        if not user:
            await ctx.send("Your Discord account is not linked to a website account.")
            return

        contract = Contract.query.get(contract_id)
        if not contract:
            await ctx.send(f"Contract with ID {contract_id} not found.")
            return

        if contract.status != ContractStatus.AVAILABLE:
            await ctx.send("This contract is not available to be claimed.")
            return

        contract.status = ContractStatus.CLAIMED
        contract.claimant_id = user.id
        db.session.commit()

        await ctx.send(f"You have successfully claimed contract {contract.id}: {contract.title}.")

def setup(bot):
    bot.add_cog(ContractsCog(bot))
