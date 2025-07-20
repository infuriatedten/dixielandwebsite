import requests
import json
from flask import current_app

def _post_to_discord(webhook_url, payload):
    """Helper function to post a payload to a given Discord webhook URL."""
    if not webhook_url:
        current_app.logger.warning("Discord webhook URL not provided. Cannot post to Discord.")
        return None
    try:
        response = requests.post(webhook_url, data=json.dumps(payload), headers={'Content-Type': 'application/json'})
        response.raise_for_status()
        current_app.logger.info(f"Successfully posted to Discord. Status: {response.status_code}")
        return True
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Error posting to Discord: {e}")
        if e.response is not None:
            current_app.logger.error(f"Discord response content: {e.response.text}")
        return None

def post_store_sale_to_discord(listing):
    """Posts a new store sale to the store sales Discord channel."""
    webhook_url = current_app.config.get('DISCORD_STORE_SALES_WEBHOOK_URL')
    if not webhook_url:
        current_app.logger.warning("DISCORD_STORE_SALES_WEBHOOK_URL not configured.")
        return

    seller_name = listing.seller.discord_username if listing.seller.discord_username else listing.seller.username
    currency_symbol = "GDC"
    if listing.seller.accounts.first():
        currency_symbol = listing.seller.accounts.first().currency

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
        },
        "timestamp": listing.creation_date.isoformat()
    }
    payload = {"embeds": [embed]}
    return _post_to_discord(webhook_url, payload)

def post_product_update_to_discord(listing):
    """Posts a product update to the product updates Discord channel."""
    webhook_url = current_app.config.get('DISCORD_PRODUCT_UPDATES_WEBHOOK_URL')
    if not webhook_url:
        current_app.logger.warning("DISCORD_PRODUCT_UPDATES_WEBHOOK_URL not configured.")
        return

    seller_name = listing.seller.discord_username if listing.seller.discord_username else listing.seller.username
    currency_symbol = "GDC"
    if listing.seller.accounts.first():
        currency_symbol = listing.seller.accounts.first().currency

    embed = {
        "title": f"📦 Product Update: {listing.item_name} (ID: {listing.id})",
        "description": f"Status: **{listing.status.value}**",
        "color": 0xFFC107 if listing.status.name == 'SOLD_MORE_AVAILABLE' else 0xDC3545 if listing.status.name == 'SOLD_OUT' else 0x17A2B8,
        "fields": [
            {"name": "Original Item", "value": listing.item_name, "inline": True},
            {"name": "Seller", "value": seller_name, "inline": True},
        ],
        "footer": {
            "text": f"Listing ID: {listing.id} | Updated: {listing.last_update_date.strftime('%Y-%m-%d %H:%M UTC')}"
        },
        "timestamp": listing.last_update_date.isoformat()
    }

    if listing.status == "AVAILABLE": # If it was edited and still available
        embed["fields"].append({"name": "Price", "value": f"{listing.price:.2f} {currency_symbol}", "inline": True})
        embed["fields"].append({"name": "Quantity", "value": f"{listing.quantity} {listing.unit}", "inline": True})
        embed["description"] = listing.description or "No description provided."

    payload = {"embeds": [embed]}
    return _post_to_discord(webhook_url, payload)

def post_listing_to_discord(listing):
    """
    Posts a marketplace listing to Discord via a configured webhook.
    `listing` is an instance of the MarketplaceListing model.
    """
    return post_store_sale_to_discord(listing)

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
    return post_product_update_to_discord(listing)


def post_auction_to_discord(auction):
    """Posts a new auction to the auctions Discord channel."""
    webhook_url = current_app.config.get('DISCORD_AUCTIONS_WEBHOOK_URL')
    if not webhook_url:
        current_app.logger.warning("DISCORD_AUCTIONS_WEBHOOK_URL not configured.")
        return

    embed = {
        "title": f"New Auction: {auction.item_name}",
        "description": auction.item_description or "No description provided.",
        "color": 0x7289DA, # Discord Blue
        "fields": [
            {"name": "Starting Bid", "value": f"{auction.actual_starting_bid:.2f}", "inline": True},
            {"name": "End Time", "value": f"<t:{int(auction.current_end_time.timestamp())}:R>", "inline": True},
        ],
        "url": url_for('auction.view_auction', auction_id=auction.id, _external=True),
        "footer": {
            "text": f"Auction ID: {auction.id}"
        },
        "timestamp": auction.start_time.isoformat()
    }
    if auction.image_url:
        embed["image"] = {"url": auction.image_url}

    payload = {"embeds": [embed]}
    return _post_to_discord(webhook_url, payload)

