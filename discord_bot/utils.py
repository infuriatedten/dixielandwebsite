import discord
import requests
from discord_bot.config_loader import BotConfig

def create_error_embed(title="Error", description="An unexpected error occurred.", color=discord.Color.red()):
    """Creates a Discord embed for error messages."""
    embed = discord.Embed(title=title, description=description, color=color)
    return embed

def create_success_embed(title="Success", description="Operation completed successfully.", color=discord.Color.green()):
    """Creates a Discord embed for success messages."""
    embed = discord.Embed(title=title, description=description, color=color)
    return embed

def create_info_embed(title="Information", description="Please note the following.", color=discord.Color.blue()):
    """Creates a Discord embed for informational messages."""
    embed = discord.Embed(title=title, description=description, color=color)
    return embed

def post_to_webhook(webhook_url: str, embed: discord.Embed = None, content: str = None, username: str = "Marketplace Bot"):
    """
    Posts a message or an embed to the specified Discord webhook URL.
    """
    if not webhook_url:
        print("ERROR: Webhook URL is not configured.")
        return False

    data = {}
    if content:
        data["content"] = content
    if embed:
        data["embeds"] = [embed.to_dict()]
    if username:
        data["username"] = username
        # data["avatar_url"] = "URL_TO_BOT_AVATAR_IF_NEEDED" # Optional

    if not data.get("content") and not data.get("embeds"):
        print("ERROR: No content or embed provided for webhook.")
        return False

    try:
        response = requests.post(webhook_url, json=data)
        response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)
        print(f"Successfully posted to webhook. Status: {response.status_code}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Failed to post to webhook: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Webhook Response Content: {e.response.text}")
        return False

if __name__ == "__main__":
    # Example usage (requires a valid webhook URL in .env for testing)
    BotConfig.validate() # Ensure config is loaded
    test_webhook_url = BotConfig.MARKETPLACE_WEBHOOK_URL

    if test_webhook_url:
        print(f"Testing webhook post to: {test_webhook_url}")

        # Test with content
        # success_content = post_to_webhook(test_webhook_url, content="Test message from bot utils (content).")
        # print(f"Content post successful: {success_content}")

        # Test with embed
        example_embed = create_info_embed(title="Webhook Test", description="This is a test embed from the bot utils.")
        example_embed.add_field(name="Field 1", value="Value 1", inline=False)
        example_embed.set_footer(text="Util Test Footer")

        success_embed = post_to_webhook(test_webhook_url, embed=example_embed)
        print(f"Embed post successful: {success_embed}")
    else:
        print("MARKETPLACE_WEBHOOK_URL not set in .env. Cannot run webhook test.")
