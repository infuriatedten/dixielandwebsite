import discord
from discord.ext import commands
from discord_bot.config_loader import BotConfig
from discord_bot.database import get_db_session
from discord_bot.utils import create_error_embed, create_success_embed, create_info_embed, post_to_webhook
from app.models import User, MarketplaceListing, MarketplaceItemStatus # Assuming models are accessible
from sqlalchemy.exc import SQLAlchemyError
from decimal import Decimal, InvalidOperation

class MarketplaceCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='linkaccount', help='Links your Discord account to your website user account. Usage: !linkaccount <website_username>')
    @commands.dm_only() # Recommend this command be DM only for privacy if password was involved. For username only, can be server.
    async def link_account(self, ctx, website_username: str):
        """Links Discord ID to an existing website username."""
        discord_id_to_link = str(ctx.author.id)
        session = get_db_session()
        if not session:
            await ctx.send(embed=create_error_embed(description="Database connection error. Please try again later."))
            return

        try:
            user = session.query(User).filter(User.username == website_username).first()

            if not user:
                await ctx.send(embed=create_error_embed(description=f"Website user '{website_username}' not found."))
                return

            if user.discord_user_id and user.discord_user_id == discord_id_to_link:
                await ctx.send(embed=create_info_embed(description="Your Discord account is already linked to this website account."))
                return

            if user.discord_user_id and user.discord_user_id != discord_id_to_link:
                # Potentially an admin action to unlink if someone is trying to overwrite, or disallow.
                await ctx.send(embed=create_error_embed(description=f"Website user '{website_username}' is already linked to a different Discord account. Contact an admin for help."))
                return

            # Check if this Discord ID is already linked to another user
            existing_link = session.query(User).filter(User.discord_user_id == discord_id_to_link).first()
            if existing_link and existing_link.id != user.id:
                 await ctx.send(embed=create_error_embed(description=f"Your Discord account is already linked to website user '{existing_link.username}'. Use `!unlinkaccount` first or contact an admin."))
                 return

            user.discord_user_id = discord_id_to_link
            session.commit()

            link_msg = (f"Successfully linked your Discord account ({ctx.author.name}) "
                        f"to website user '{website_username}'.\n"
                        f"You can now use marketplace commands like `!sell`.")
            await ctx.send(embed=create_success_embed(description=link_msg))
            print(f"User {website_username} (ID: {user.id}) linked Discord ID: {discord_id_to_link}")

        except SQLAlchemyError as e:
            session.rollback()
            print(f"Database error during account linking: {e}")
            await ctx.send(embed=create_error_embed(description="A database error occurred. Please try again."))
        except Exception as e:
            print(f"Unexpected error during account linking: {e}")
            await ctx.send(embed=create_error_embed(description="An unexpected error occurred."))
        finally:
            session.close()

    @commands.command(name='unlinkaccount', help='Unlinks your Discord account from your website user account.')
    @commands.dm_only()
    async def unlink_account(self, ctx):
        discord_id_to_unlink = str(ctx.author.id)
        session = get_db_session()
        if not session:
            await ctx.send(embed=create_error_embed(description="Database connection error."))
            return
        try:
            user = session.query(User).filter(User.discord_user_id == discord_id_to_unlink).first()
            if not user:
                await ctx.send(embed=create_info_embed(description="Your Discord account is not currently linked to any website account."))
                return

            username = user.username
            user.discord_user_id = None
            session.commit()
            await ctx.send(embed=create_success_embed(description=f"Successfully unlinked your Discord account from website user '{username}'."))
            print(f"Discord ID {discord_id_to_unlink} unlinked from user {username}")
        except SQLAlchemyError as e:
            session.rollback()
            print(f"Database error during account unlinking: {e}")
            await ctx.send(embed=create_error_embed(description="A database error occurred during unlinking."))
        finally:
            session.close()


    @commands.command(name='sell', help='Post an item for sale. Usage: !sell <ItemName> <Price> <Quantity> <Unit> [Description]')
    async def sell_item(self, ctx, item_name: str, price_str: str, quantity_str: str, unit: str, *, description: str = None):
        discord_user_id = str(ctx.author.id)
        session = get_db_session()
        if not session:
            await ctx.send(embed=create_error_embed(description="Database error. Try again later."))
            return

        try:
            user = session.query(User).filter(User.discord_user_id == discord_user_id).first()
            if not user:
                await ctx.send(embed=create_error_embed(description="Your Discord account is not linked to a website account. Use `!linkaccount <your_website_username>` first (in a DM to me)."))
                return

            try:
                price = Decimal(price_str)
                if price <= 0:
                    raise ValueError("Price must be positive.")
            except (InvalidOperation, ValueError):
                await ctx.send(embed=create_error_embed(description="Invalid price format. Please enter a valid number (e.g., 10.99)."))
                return

            try:
                quantity = Decimal(quantity_str)
                if quantity <= 0:
                    raise ValueError("Quantity must be positive.")
            except (InvalidOperation, ValueError):
                await ctx.send(embed=create_error_embed(description="Invalid quantity format. Please enter a valid number (e.g., 1 or 0.5)."))
                return

            if len(item_name) > 200 or len(unit) > 50 or (description and len(description) > 1000):
                await ctx.send(embed=create_error_embed(description="Input too long. Item name max 200, unit max 50, description max 1000 chars."))
                return

            new_listing = MarketplaceListing(
                seller_user_id=user.id,
                item_name=item_name,
                description=description,
                price=price,
                quantity=quantity,
                unit=unit,
                status=MarketplaceItemStatus.AVAILABLE
            )
            session.add(new_listing)
            session.commit() # Commit to get the new_listing.id

            # Post to Discord channel via Webhook
            embed_title = f"🛒 New Listing: {new_listing.item_name}"
            embed_desc = (
                f"**Seller:** {ctx.author.mention} ({user.username})\n"
                f"**Price:** {new_listing.price:.2f} {user.accounts.first().currency if user.accounts.first() else 'credits'}\n"
                f"**Quantity:** {new_listing.quantity} {new_listing.unit}\n"
            )
            if new_listing.description:
                embed_desc += f"**Description:** {new_listing.description}\n"
            embed_desc += f"\nListing ID: `{new_listing.id}` (Use this ID for `!sold` or `!cancel` commands)"

            listing_embed = discord.Embed(title=embed_title, description=embed_desc, color=discord.Color.blue())
            listing_embed.set_footer(text=f"Posted by {user.username} | Listing ID: {new_listing.id}")

            if BotConfig.MARKETPLACE_WEBHOOK_URL:
                post_successful = post_to_webhook(
                    BotConfig.MARKETPLACE_WEBHOOK_URL,
                    embed=listing_embed,
                    username=f"{user.username} (via Marketplace Bot)" # Webhook username
                )
                if post_successful:
                    await ctx.message.add_reaction("✅") # React to original command
                    # Optionally send a DM confirmation with listing ID
                    await ctx.author.send(embed=create_success_embed(title="Listing Created!", description=f"Your listing for '{item_name}' (ID: {new_listing.id}) has been posted to the marketplace channel."))
                else:
                    await ctx.send(embed=create_error_embed(description="Successfully saved listing to database, but failed to post to Discord channel via webhook."))
            else: # Fallback if webhook is not configured - post directly (less pretty)
                target_channel_id = int(BotConfig.MARKETPLACE_CHANNEL_ID)
                target_channel = self.bot.get_channel(target_channel_id)
                if target_channel:
                    msg_content = f"**New Listing by {ctx.author.mention} ({user.username})!**\n" + \
                                  f"**Item:** {item_name}\n**Price:** {price:.2f}\n**Quantity:** {quantity} {unit}\n" + \
                                  (f"**Description:** {description}\n" if description else "") + \
                                  f"Listing ID: `{new_listing.id}`"
                    await target_channel.send(msg_content)
                    await ctx.message.add_reaction("✅")
                else:
                     await ctx.send(embed=create_error_embed(description=f"Marketplace channel not found by bot (ID: {target_channel_id}). Listing saved to DB only."))


        except SQLAlchemyError as e:
            session.rollback()
            print(f"Database error during sell command: {e}")
            await ctx.send(embed=create_error_embed(description="A database error occurred. Please try again."))
        except Exception as e:
            print(f"Unexpected error during sell command: {e}")
            await ctx.send(embed=create_error_embed(description=f"An unexpected error occurred: {type(e).__name__}"))
        finally:
            session.close()

    @commands.command(name='sold', help='Mark a listing as sold. Usage: !sold <ListingID> [all_gone (optional)]')
    async def sold_item(self, ctx, listing_id_str: str, availability: str = "more"):
        discord_user_id = str(ctx.author.id)
        session = get_db_session()
        if not session:
            await ctx.send(embed=create_error_embed(description="Database error."))
            return

        try:
            user = session.query(User).filter(User.discord_user_id == discord_user_id).first()
            if not user:
                await ctx.send(embed=create_error_embed(description="Your Discord account is not linked. Use `!linkaccount` first."))
                return

            try:
                listing_id = int(listing_id_str)
            except ValueError:
                await ctx.send(embed=create_error_embed(description="Invalid Listing ID format. It should be a number."))
                return

            listing = session.query(MarketplaceListing).filter_by(id=listing_id, seller_user_id=user.id).first()

            if not listing:
                await ctx.send(embed=create_error_embed(description=f"Listing ID '{listing_id}' not found or you are not the seller."))
                return

            if listing.status == MarketplaceItemStatus.SOLD_OUT or listing.status == MarketplaceItemStatus.CANCELLED:
                 await ctx.send(embed=create_info_embed(description=f"Listing ID '{listing_id}' ({listing.item_name}) is already marked as {listing.status.value}."))
                 return

            new_status = MarketplaceItemStatus.SOLD_PENDING_RELIST
            if availability.lower() == "all" or availability.lower() == "all_gone" or availability.lower() == "out":
                new_status = MarketplaceItemStatus.SOLD_OUT

            listing.status = new_status
            session.commit()

            status_message = "more available (can be relisted)" if new_status == MarketplaceItemStatus.SOLD_PENDING_RELIST else "all stock sold out"

            # Notify in channel via webhook
            sold_embed = discord.Embed(
                title=f"🛍️ Listing Update: {listing.item_name} (ID: {listing.id})",
                description=f"Item **{listing.item_name}** listed by {ctx.author.mention} ({user.username}) has been marked as **SOLD** ({status_message}).",
                color=discord.Color.orange() if new_status == MarketplaceItemStatus.SOLD_PENDING_RELIST else discord.Color.dark_grey()
            )
            if BotConfig.MARKETPLACE_WEBHOOK_URL:
                post_to_webhook(BotConfig.MARKETPLACE_WEBHOOK_URL, embed=sold_embed, username=f"{user.username} (via Marketplace Bot)")

            await ctx.send(embed=create_success_embed(description=f"Listing ID '{listing.id}' ({listing.item_name}) updated to {new_status.value}."))

        except SQLAlchemyError as e:
            session.rollback()
            await ctx.send(embed=create_error_embed(description="Database error during sold command."))
        except Exception as e:
            await ctx.send(embed=create_error_embed(description=f"An unexpected error occurred: {e}"))
        finally:
            session.close()

    @commands.command(name='cancel', help='Cancel your active listing. Usage: !cancel <ListingID>')
    async def cancel_listing(self, ctx, listing_id_str: str):
        discord_user_id = str(ctx.author.id)
        session = get_db_session()
        if not session:
            await ctx.send(embed=create_error_embed(description="Database error."))
            return
        try:
            user = session.query(User).filter(User.discord_user_id == discord_user_id).first()
            if not user:
                await ctx.send(embed=create_error_embed(description="Your Discord account is not linked. Use `!linkaccount` first."))
                return
            try:
                listing_id = int(listing_id_str)
            except ValueError:
                await ctx.send(embed=create_error_embed(description="Invalid Listing ID format."))
                return

            listing = session.query(MarketplaceListing).filter_by(id=listing_id, seller_user_id=user.id).first()
            if not listing:
                await ctx.send(embed=create_error_embed(description=f"Listing ID '{listing_id}' not found or you are not the seller."))
                return

            if listing.status == MarketplaceItemStatus.CANCELLED:
                await ctx.send(embed=create_info_embed(description=f"Listing ID '{listing_id}' ({listing.item_name}) is already cancelled."))
                return
            if listing.status == MarketplaceItemStatus.SOLD_OUT: # Or other final states
                await ctx.send(embed=create_info_embed(description=f"Listing ID '{listing_id}' ({listing.item_name}) is already {listing.status.value} and cannot be cancelled."))
                return

            listing.status = MarketplaceItemStatus.CANCELLED
            session.commit()

            cancel_embed = discord.Embed(
                title=f"🚫 Listing Cancelled: {listing.item_name} (ID: {listing.id})",
                description=f"Item **{listing.item_name}** listed by {ctx.author.mention} ({user.username}) has been **CANCELLED** by the seller.",
                color=discord.Color.light_grey()
            )
            if BotConfig.MARKETPLACE_WEBHOOK_URL:
                 post_to_webhook(BotConfig.MARKETPLACE_WEBHOOK_URL, embed=cancel_embed, username=f"{user.username} (via Marketplace Bot)")

            await ctx.send(embed=create_success_embed(description=f"Listing ID '{listing.id}' ({listing.item_name}) has been cancelled."))
        except SQLAlchemyError as e:
            session.rollback()
            await ctx.send(embed=create_error_embed(description="Database error during cancel command."))
        finally:
            session.close()


async def setup(bot):
    await bot.add_cog(MarketplaceCog(bot))
    print("MarketplaceCog loaded.")
