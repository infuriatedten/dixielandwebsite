from flask import Blueprint, render_template, redirect, url_for, flash
from app.models import StoreItem

store_bp = Blueprint('store', __name__)

@store_bp.route('/store')
def view_store():
    items = StoreItem.query.order_by(StoreItem.brand, StoreItem.name).all()
    return render_template('store/index.html', title='Store', items=items)

@store_bp.route('/store/purchase/<int:item_id>', methods=['POST'])
def purchase_item(item_id):
    flash('Vehicle purchases must be made in-game.', 'info')
    return redirect(url_for('store.view_store'))
