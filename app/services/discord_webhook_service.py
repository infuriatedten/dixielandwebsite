import requests
import json
from flask import current_app

def post_listing_to_discord(listing):
    """
    Posts a marketplace listing to Discord via a configured webhook.
    `listing` is an instance of the MarketplaceListing model.
    """
    webhook_url = current_app.config.get('DISCORD_WEBHOOK_URL')
    if not webhook_url:
        current_app.logger.warning("DISCORD_WEBHOOK_URL not configured. Cannot post listing to Discord.")
        return None # Indicate failure or no action

    # Seller information - try to use Discord username if available, else website username
    seller_name = listing.seller.discord_username if listing.seller.discord_username else listing.seller.username
    if listing.seller.discord_user_id: # If discord ID is linked, can use mention if bot context allows (not for webhooks usually)
        # seller_name = f"<@{listing.seller.discord_user_id}>" # This would mention the user
        pass # For webhooks, plain name is better unless webhook is configured to allow mentions from specific users

    # Get currency from user's account if possible, else default
    currency_symbol = "GDC" # Default game currency
    if listing.seller.accounts.first(): # Assuming user has one account
        currency_symbol = listing.seller.accounts.first().currency


    # Construct the message payload for Discord
    # Using a simple text message first, can upgrade to embeds later for better formatting
    content = (
        f"🛒 **New Marketplace Listing!** (ID: {listing.id})\n\n"
        f"**Item:** {listing.item_name}\n"
        f"**Price:** {listing.price:.2f} {currency_symbol}\n"
        f"**Quantity:** {listing.quantity} {listing.unit}\n"
        f"**Seller:** {seller_name}\n"
        f"**Description:**\n{listing.description}\n\n"
        f"To purchase or inquire, contact the seller. Use Listing ID `{listing.id}` for Discord commands (e.g., `!sold_out {listing.id}`)."
    )

    # For richer formatting, use embeds:
    embed = {
        "title": f"🛒 New Listing: {listing.item_name}",
        "description": listing.description or "No description provided.",
        "color": 0x5865F2, # Discord blurple
        "fields": [
            {"name": "Price", "value": f"{listing.price:.2f} {currency_symbol}", "inline": True},
            {"name": "Quantity", "value": f"{listing.quantity} {listing.unit}", "inline": True},
            {"name": "Seller", "value": seller_name, "inline": True},
            {"name": "Listing ID", "value": f"`{listing.id}` (Use for `!sold` commands)", "inline": False}
        ],
        "footer": {
            "text": f"Listing created by {listing.seller.username} | {listing.creation_date.strftime('%Y-%m-%d %H:%M UTC')}"
            # "icon_url": "URL_to_your_site_logo_or_bot_avatar" # Optional
        },
        "timestamp": listing.creation_date.isoformat()
    }

    payload = {
        # "username": "Marketplace Bot", # Optional: Override webhook's default username
        # "avatar_url": "URL_to_your_bot_avatar", # Optional: Override webhook's default avatar
        # "content": content, # Use this for simple text messages
        "embeds": [embed] # Use this for rich embed messages
    }

    try:
        response = requests.post(webhook_url, data=json.dumps(payload), headers={'Content-Type': 'application/json'})
        response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)

        current_app.logger.info(f"Successfully posted listing {listing.id} to Discord. Status: {response.status_code}")

        # Try to get message ID from response if Discord returns it for webhooks (often it does in some capacity)
        # The exact structure of the response can vary.
        # For webhooks with `wait=true` parameter, it returns the message object.
        # If `wait=true` is not used (default), it's a 204 No Content and no message object.
        # To get message ID for editing, `wait=true` is needed.
        # Example: requests.post(webhook_url + "?wait=true", ...)
        # For now, let's assume we might not get it easily without `wait=true`

        # If you add `?wait=true` to your webhook_url when sending:
        # if response.status_code == 200:
        #     message_data = response.json()
        #     return message_data.get('id') # Return the Discord message ID

        return True # Indicate success
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Error posting listing {listing.id} to Discord: {e}")
        if e.response is not None:
            current_app.logger.error(f"Discord response content: {e.response.text}")
        return None # Indicate failure

# Example of how to update/edit a message if you have its ID (requires BOT TOKEN, not webhook)
# This would be part of Phase 2 with a full bot.
# def edit_discord_listing_message(message_id, new_content_or_embed):
#     bot_token = current_app.config.get('DISCORD_BOT_TOKEN')
#     channel_id = current_app.config.get('DISCORD_MARKETPLACE_CHANNEL_ID')
#     if not bot_token or not channel_id or not message_id:
#         current_app.logger.warning("Discord bot token, channel ID, or message ID not configured. Cannot edit message.")
#         return
#
#     url = f"https://discord.com/api/v9/channels/{channel_id}/messages/{message_id}"
#     headers = {
#         "Authorization": f"Bot {bot_token}",
#         "Content-Type": "application/json"
#     }
#     payload = new_content_or_embed # This would be a dict like {"content": "new text"} or {"embeds": [new_embed_obj]}
#
#     try:
#         response = requests.patch(url, data=json.dumps(payload), headers=headers)
#         response.raise_for_status()
#         current_app.logger.info(f"Successfully edited Discord message {message_id}.")
#     except requests.exceptions.RequestException as e:
#         current_app.logger.error(f"Error editing Discord message {message_id}: {e}")
#         if e.response is not None:
#             current_app.logger.error(f"Discord response content (edit): {e.response.text}")

def update_listing_on_discord(listing, action_text="Listing Updated"):
    """
    Posts an update about a marketplace listing to Discord.
    This could be a new message or an attempt to edit the original if message_id is stored and bot is used.
    For now, using webhook to post a NEW message indicating an update.
    """
    webhook_url = current_app.config.get('DISCORD_WEBHOOK_URL')
    if not webhook_url:
        current_app.logger.warning("DISCORD_WEBHOOK_URL not configured. Cannot post listing update to Discord.")
        return None

    seller_name = listing.seller.discord_username if listing.seller.discord_username else listing.seller.username
    currency_symbol = listing.seller.accounts.first().currency if listing.seller.accounts.first() else "GDC"

    embed = {
        "title": f"🛒 Listing Update: {listing.item_name} (ID: {listing.id})",
        "description": f"Status: **{listing.status.value}**",
        "color": 0xFFC107 if listing.status.name == 'SOLD_MORE_AVAILABLE' else 0xDC3545 if listing.status.name == 'SOLD_OUT' else 0x17A2B8, # Yellow, Red, Blue
        "fields": [
            {"name": "Original Item", "value": listing.item_name, "inline": True},
            {"name": "Seller", "value": seller_name, "inline": True},
        ],
        "footer": {
            "text": f"Listing ID: {listing.id} | Updated: {listing.last_update_date.strftime('%Y-%m-%d %H:%M UTC')}"
        },
        "timestamp": listing.last_update_date.isoformat()
    }

    if listing.status == MarketplaceListingStatus.AVAILABLE: # If it was edited and still available
        embed["fields"].append({"name": "Price", "value": f"{listing.price:.2f} {currency_symbol}", "inline": True})
        embed["fields"].append({"name": "Quantity", "value": f"{listing.quantity} {listing.unit}", "inline": True})
        embed["description"] = listing.description or "No description provided."


    payload = {"embeds": [embed]}

    try:
        response = requests.post(webhook_url, data=json.dumps(payload), headers={'Content-Type': 'application/json'})
        response.raise_for_status()
        current_app.logger.info(f"Successfully posted update for listing {listing.id} to Discord.")
        return True
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Error posting update for listing {listing.id} to Discord: {e}")
        return None
