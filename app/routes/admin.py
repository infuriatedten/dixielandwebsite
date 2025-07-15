from flask import Blueprint, render_template
from app.decorators import admin_required

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/')
@admin_required
def index():
    return render_template('admin/dashboard.html', title='Admin Dashboard')

@admin_bp.route('/tickets')
@admin_required
def tickets():
    # This is a placeholder. You'll need to implement the logic to fetch and display tickets.
    return render_template('admin/tickets.html', title='Manage Tickets')
