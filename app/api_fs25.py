# api_fs25.py
from flask import Blueprint, request, jsonify, current_app
from app.models import db, Farmer, Account, Transaction, TransactionType, FarmerStats, Notification, Conversation, SiloStorage, Player, Purchase
from datetime import datetime
from app.utils import verify_signature

api_fs25_bp = Blueprint('api_fs25', __name__)

@api_fs25_bp.route('/api/fs25/update_balance', methods=['POST'])
def update_balance():
    data = request.json
    farmer_id = data.get('farmer_id')
    new_balance = data.get('balance')

    if farmer_id is None or new_balance is None:
        return jsonify({"error": "Missing farmer_id or balance"}), 400

    try:
        new_balance = float(new_balance)
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid balance format"}), 400

    farmer = Farmer.query.get(farmer_id)
    if not farmer:
        return jsonify({"error": "Farmer not found"}), 404

    # Assuming the farmer has one primary bank account associated with their user profile
    account = farmer.user.accounts.first()
    if not account:
        return jsonify({"error": "Bank account not found for this farmer"}), 404

    change = new_balance - float(account.balance)
    account.balance = new_balance

    history = Transaction(
        account_id=account.id,
        amount=change,
        description='Balance synced from FS25',
        type=TransactionType.FS25_SYNC
    )
    db.session.add(history)
    db.session.commit()

    return jsonify({"status": "success", "new_balance": float(account.balance)}), 200


@api_fs25_bp.route('/api/fs25/update_stats', methods=['POST'])
def update_stats():
    data = request.json
    farmer_id = data.get('farmer_id')

    if farmer_id is None:
        return jsonify({"error": "Missing farmer_id"}), 400

    farmer = Farmer.query.get(farmer_id)
    if not farmer:
        return jsonify({"error": "Farmer not found"}), 404

    stats = FarmerStats.query.filter_by(farmer_id=farmer_id).first()
    if not stats:
        stats = FarmerStats(farmer_id=farmer_id)

    stats.fields_owned = data.get('fields_owned', stats.fields_owned)
    stats.total_yield = data.get('total_yield', stats.total_yield)
    stats.equipment_owned = data.get('equipment_owned', stats.equipment_owned)
    stats.last_synced = datetime.utcnow()

    db.session.add(stats)
    db.session.commit()

    return jsonify({"status": "updated"}), 200

@api_fs25_bp.route('/api/fs25/get_notifications', methods=['GET'])
def get_notifications():
    farmer_id = request.args.get('farmer_id')

    if not farmer_id:
        return jsonify({"error": "farmer_id is required"}), 400

    farmer = Farmer.query.get(farmer_id)
    if not farmer:
        return jsonify({"error": "Farmer not found"}), 404

    user = farmer.user

    # Get count of unread notifications
    unread_notifications_count = Notification.query.filter_by(user_id=user.id, is_read=False).count()

    # Get count of unread messages from conversations
    unread_messages_count = db.session.query(db.func.sum(Conversation.user_unread_count)).filter(Conversation.user_id == user.id).scalar() or 0

    return jsonify({
        "farmer_id": farmer_id,
        "unread_notifications": unread_notifications_count,
        "unread_messages": int(unread_messages_count)
    }), 200


@api_fs25_bp.route('/api/fs25/update_silo', methods=['POST'])
def update_silo():
    data = request.json
    farmer_id = data.get('farmer_id')
    silo_contents = data.get('silo_contents') # Expecting a list of dicts

    if farmer_id is None or silo_contents is None:
        return jsonify({"error": "Missing farmer_id or silo_contents"}), 400

    if not isinstance(silo_contents, list):
        return jsonify({"error": "silo_contents should be a list"}), 400

    farmer = Farmer.query.get(farmer_id)
    if not farmer:
        return jsonify({"error": "Farmer not found"}), 404

    try:
        for item in silo_contents:
            crop_type = item.get('crop_type')
            quantity = float(item.get('quantity', 0))
            capacity = float(item.get('capacity', 200000)) # Default capacity

            if not crop_type:
                continue # Skip items without a crop type

            # Find existing silo record or create a new one
            silo_storage = SiloStorage.query.filter_by(farmer_id=farmer_id, crop_type=crop_type).first()
            if not silo_storage:
                silo_storage = SiloStorage(farmer_id=farmer_id, crop_type=crop_type)
                db.session.add(silo_storage)

            silo_storage.quantity = quantity
            silo_storage.capacity = capacity
            silo_storage.last_updated = datetime.utcnow()

        db.session.commit()
        return jsonify({"status": "success", "message": f"Silo contents updated for farmer {farmer_id}."}), 200

    except (ValueError, TypeError) as e:
        db.session.rollback()
        return jsonify({"error": "Invalid data format for quantity or capacity.", "details": str(e)}), 400
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating silo for farmer {farmer_id}: {e}", exc_info=True)
        return jsonify({"error": "An unexpected error occurred."}), 500

# ------------------------
# Player login/logout/heartbeat
# ------------------------
@api_fs25_bp.route("/api/fs25/heartbeat", methods=["POST"])
def heartbeat():
    data = request.get_json()
    if not verify_signature(data):
        return jsonify({"error": "invalid signature"}), 403

    discord_id = data.get("discord_id")
    event = data.get("event", "heartbeat")
    timestamp = datetime.fromisoformat(data.get("timestamp"))

    player = Player.query.filter_by(discord_id=discord_id).first()
    if not player:
        player = Player(discord_id=discord_id)
        db.session.add(player)

    if event == "login":
        player.last_login = timestamp
    elif event == "logout":
        player.last_logout = timestamp
        # Calculate session time
        if player.last_login:
            session_time = (timestamp - player.last_login).total_seconds()
            player.total_time += session_time
    elif event == "idle_logout":
        # Half rate time
        if player.last_login:
            session_time = (timestamp - player.last_login).total_seconds()
            player.half_rate_time += session_time / 2
            player.total_time += session_time / 2
    else:
        # heartbeat updates last_heartbeat
        player.last_heartbeat = timestamp

    db.session.commit()
    return jsonify({"status": "ok"})


# ------------------------
# Store purchase
# ------------------------
@api_fs25_bp.route("/api/fs25/store/purchase", methods=["POST"])
def store_purchase():
    data = request.get_json()
    if not verify_signature(data):
        return jsonify({"error": "invalid signature"}), 403

    discord_id = data.get("playerId") or data.get("discord_id")
    xml = data.get("xml")
    price = float(data.get("price", 0))

    player = Player.query.filter_by(discord_id=str(discord_id)).first()
    if not player:
        return jsonify({"error": "player not found"}), 404

    purchase = Purchase(player_id=player.id, xml_filename=xml, price=price)
    db.session.add(purchase)
    db.session.commit()

    return jsonify({"status": "ok"})


# ------------------------
# Admin endpoint to get stats
# ------------------------
@api_fs25_bp.route("/api/fs25/stats/<discord_id>", methods=["GET"])
def stats(discord_id):
    player = Player.query.filter_by(discord_id=discord_id).first()
    if not player:
        return jsonify({"error": "player not found"}), 404

    return jsonify({
        "discord_id": player.discord_id,
        "total_time": player.total_time,
        "half_rate_time": player.half_rate_time,
        "last_login": player.last_login.isoformat() if player.last_login else None,
        "last_logout": player.last_logout.isoformat() if player.last_logout else None,
        "last_heartbeat": player.last_heartbeat.isoformat() if player.last_heartbeat else None
    })
