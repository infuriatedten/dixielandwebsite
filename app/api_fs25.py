# api_fs25.py
from flask import Blueprint, request, jsonify, current_app
from app.models import db, Farmer, Account, Transaction, TransactionType, FarmerStats, Notification, Conversation, SiloStorage, StoreItem, UserVehicle
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

@api_fs25_bp.route('/api/fs25/store/inventory', methods=['POST'])
def store_inventory():
    data = request.json
    if not isinstance(data, list):
        return jsonify({"error": "Expected a list of store items"}), 400

    try:
        # Clear existing store items
        db.session.query(StoreItem).delete()

        for item_data in data:
            new_item = StoreItem(
                name=item_data.get('name'),
                price=item_data.get('price'),
                brand=item_data.get('brand'),
                category=item_data.get('category'),
                xml_filename=item_data.get('xml_filename')
            )
            db.session.add(new_item)

        db.session.commit()
        return jsonify({"status": "success", "message": f"{len(data)} store items updated."}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating store inventory: {e}", exc_info=True)
        return jsonify({"error": "An unexpected error occurred."}), 500

@api_fs25_bp.route('/api/fs25/store/purchase', methods=['POST'])
def store_purchase():
    data = request.json
    xml_filename = data.get('xml')
    price = data.get('price')
    discord_id = data.get('discordId')

    if not all([xml_filename, price, discord_id]):
        return jsonify({"error": "Missing xml, price, or discordId"}), 400

    user = User.query.filter_by(discord_user_id=discord_id).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    account = user.accounts.first()
    if not account or account.balance < price:
        return jsonify({"error": "Insufficient funds"}), 400

    item = StoreItem.query.filter_by(xml_filename=xml_filename).first()
    if not item:
        return jsonify({"error": "Item not found"}), 404

    try:
        # Deduct funds
        account.balance -= price
        new_transaction = Transaction(
            account_id=account.id,
            type=TransactionType.MARKETPLACE_PURCHASE,
            amount=-price,
            description=f'Purchase of {item.name} from the store.'
        )
        db.session.add(new_transaction)

        # Add vehicle to user's garage
        new_vehicle = UserVehicle(
            user_id=user.id,
            vehicle_make=item.brand,
            vehicle_model=item.name,
            vehicle_type=item.category,
            license_plate=f"{user.username}-{item.name.replace(' ', '')[:5]}-{user.id}", # Generate a unique license plate
            region_format='US' # Default to US format
        )
        db.session.add(new_vehicle)

        db.session.commit()
        return jsonify({"status": "success"}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error processing purchase for user {user.id}: {e}", exc_info=True)
        return jsonify({"error": "An unexpected error occurred."}), 500
