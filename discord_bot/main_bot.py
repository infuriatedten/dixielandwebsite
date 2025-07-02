import discord
from discord.ext import commands
import os # For loading cogs
import asyncio # For bot.load_extension if it's async

from discord_bot.config_loader import BotConfig
from discord_bot.database import init_db as init_bot_db # Renamed to avoid clash if Flask app also has init_db

# --- Bot Configuration & Intents ---
try:
    BotConfig.validate() # Validate config early
except ValueError as e:
    print(f"CRITICAL: Bot configuration error: {e}")
    exit(1) # Exit if essential config is missing

# Initialize database for the bot (models should be shared from Flask app)
try:
    init_bot_db(BotConfig.DATABASE_URL)
except Exception as e:
    print(f"CRITICAL: Bot failed to initialize database connection: {e}")
    exit(1)


intents = discord.Intents.default()
intents.message_content = True # Required for reading message content for commands
intents.members = True # Optional: If you need member presence or information beyond context
intents.guilds = True # Access to guild information

bot = commands.Bot(command_prefix='!', intents=intents)


# --- Event: Bot Ready ---
@bot.event
async def on_ready():
    print(f'Bot logged in as {bot.user.name} (ID: {bot.user.id})')
    print(f'Connected to {len(bot.guilds)} servers.')
    try:
        # Set presence (activity)
        await bot.change_presence(activity=discord.Game(name="the Market | !help"))
        print("Bot presence updated.")

        # Sync commands if using slash commands (not used here for prefix commands, but good practice)
        # This is more for application commands (slash commands). For prefix commands, cogs are loaded.
        # if BotConfig.DISCORD_SERVER_ID:
        #     guild = discord.Object(id=int(BotConfig.DISCORD_SERVER_ID))
        #     bot.tree.copy_global_to(guild=guild)
        #     await bot.tree.sync(guild=guild)
        #     print(f"Commands synced to server ID {BotConfig.DISCORD_SERVER_ID}")
        # else:
        # await bot.tree.sync() # Sync global commands if no specific server ID
        # print("Global commands synced.")

    except Exception as e:
        print(f"Error during on_ready tasks (presence/sync): {e}")

# --- Event: Command Error Handling ---
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        # await ctx.send(f"Sorry, I don't recognize that command. Try `!help`.")
        pass # Ignore command not found to keep chat clean, or send a subtle reply
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"You're missing some information for that command! Usage: `!{ctx.command.name} {ctx.command.signature}`")
    elif isinstance(error, commands.BadArgument):
        await ctx.send(f"Looks like you provided some invalid information. Please check the command usage with `!help {ctx.command.name}`.")
    elif isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"Woah there, slow down! Try again in {error.retry_after:.2f} seconds.")
    elif isinstance(error, commands.NotOwner):
        await ctx.send("Sorry, only the bot owner can use that command.")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("You don't have the required permissions to use this command.")
    elif isinstance(error, commands.BotMissingPermissions):
        await ctx.send("I don't have the necessary permissions to do that. Please check my roles.")
    elif isinstance(error, commands.NoPrivateMessage):
        await ctx.send("This command cannot be used in private messages.")
    elif isinstance(error, commands.PrivateMessageOnly):
        await ctx.send("This command can only be used in private messages (DM me).")
    else:
        print(f'Unhandled command error in {ctx.command}: {error}')
        # Consider logging the full traceback for unexpected errors
        # import traceback
        # traceback.print_exception(type(error), error, error.__traceback__)
        await ctx.send("An unexpected error occurred while running that command. The bot admin has been notified (hopefully!).")


# --- Load Cogs ---
async def load_cogs():
    """Loads all cogs from the 'cogs' directory."""
    cogs_path = os.path.join(os.path.dirname(__file__), 'cogs')
    for filename in os.listdir(cogs_path):
        if filename.endswith('.py') and not filename.startswith('_'):
            cog_name = f'discord_bot.cogs.{filename[:-3]}'
            try:
                await bot.load_extension(cog_name)
                print(f'Successfully loaded cog: {cog_name}')
            except Exception as e:
                print(f'Failed to load cog {cog_name}. Error: {e}')
                # import traceback
                # traceback.print_exc()


# --- Main Bot Execution ---
async def main():
    async with bot:
        await load_cogs()
        if not BotConfig.DISCORD_BOT_TOKEN:
            print("CRITICAL: DISCORD_BOT_TOKEN not found in environment. Bot cannot start.")
            return
        try:
            await bot.start(BotConfig.DISCORD_BOT_TOKEN)
        except discord.LoginFailure:
            print("CRITICAL: Failed to log in to Discord. Check your bot token.")
        except Exception as e:
            print(f"CRITICAL: Bot failed to start or encountered a runtime error: {e}")

if __name__ == '__main__':
    # For running the bot directly
    # Ensure you have a .env file in the discord_bot directory with necessary configs
    # or that environment variables are set.
    print("Starting Discord bot...")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot shutting down...")
    except Exception as e:
        print(f"Critical error running the bot: {e}")
        # import traceback
        # traceback.print_exc()
    finally:
        print("Bot process finished.")
