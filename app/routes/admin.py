from flask import Blueprint, render_template
from app.decorators import admin_required

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/')
@admin_required
def index():
    return render_template('admin/dashboard.html', title='Admin Dashboard')
