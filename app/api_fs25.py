# api.py
from flask import Blueprint, request, jsonify
from models import db, Farmer, BankAccount, BalanceHistory, FarmerStats
from datetime import datetime

api = Blueprint('api', __name__)

@api.route('/api/fs25/update_balance', methods=['POST'])
def update_balance():
    data = request.json
    farmer_id = data.get('farmer_id')
    new_balance = float(data.get('balance', 0))
    description = data.get('description', 'Synced from FS25')

    farmer = Farmer.query.get(farmer_id)
    if not farmer or not farmer.bank_account:
        return jsonify({"error": "Farmer account not found"}), 404

    account = farmer.bank_account
    change = new_balance - account.balance
    account.balance = new_balance
    account.updated_at = datetime.utcnow()

    history = BalanceHistory(
        account_id=account.id,
        change=change,
        balance_after=new_balance,
        description=description,
        source='FS25'
    )
    db.session.add(history)
    db.session.commit()

    return jsonify({"status": "success"}), 200


@api.route('/api/fs25/update_stats', methods=['POST'])
def update_stats():
    data = request.json
    farmer_id = data.get('farmer_id')

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
