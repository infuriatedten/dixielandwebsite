from flask import Blueprint, render_template
from flask_login import current_user

bp = Blueprint('main', __name__)

@bp.route('/')
@bp.route('/index')
def index():
    return render_template('main/index.html', title='Home')
from flask import Blueprint, render_template
from flask_login import login_required, current_user

# main.py (line 13)
@bp.route('/')
@bp.route('/index')
def index():
    return render_template('main/index.html', title='Home')


@bp.route('/')
@login_required
def index():
    return render_template('admin/index.html', title='Admin Dashboard')
