# api_fs25.py
from flask import Blueprint, request, jsonify
from app.models import db, Farmer, Account, Transaction, TransactionType, FarmerStats, Notification, Conversation
from datetime import datetime

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
