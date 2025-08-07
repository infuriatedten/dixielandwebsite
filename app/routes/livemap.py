from flask import Blueprint, render_template, current_app, flash
from flask_login import login_required
from app.services import livemap_service # Assuming __init__.py in services makes functions available
from flask_login import login_required

livemap_bp = Blueprint('livemap', __name__)


# Future routes for this blueprint could include:
# @livemap_bp.route('/players')
# @login_required
# def live_players(): ...

# @livemap_bp.route('/vehicles')
# @login_required
# def live_vehicles(): ...

# @livemap_bp.route('/weather')
# @login_required
# def live_weather(): ...
