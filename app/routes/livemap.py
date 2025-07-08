from flask import Blueprint, render_template, current_app, flash
from flask_login import login_required
from app.services import livemap_service # Assuming __init__.py in services makes functions available
from flask_login import login_required

livemap_bp = Blueprint('livemap', __name__)

@livemap_bp.route('/status')
@login_required # Protect this route
def server_status():
    """
    Displays the current live server status by fetching and parsing
    the livemap_dynamic.xml file.
    """
    status_data = None
    error_message = None

    try:
        # This function now encapsulates fetching and parsing based on config
        status_data = livemap_service.get_live_server_status()
        if status_data and status_data.get('error'):
            error_message = status_data['error']
            current_app.logger.error(f"Error fetching live server status: {error_message}")
            status_data = None # Clear data if there was an error reported by the service
        elif not status_data:
             error_message = "Could not retrieve server status data. The source might be unavailable or an internal error occurred."
             current_app.logger.warning("get_live_server_status returned None without explicit error.")

    except Exception as e:
        current_app.logger.error(f"Unexpected error in /livemap/status route: {e}", exc_info=True)
        error_message = "An unexpected error occurred while trying to fetch server status."
        # flash("An unexpected error occurred. Please try again later or contact an admin.", "danger") # Optional user flash

    if error_message and not status_data: # Only flash if no data is to be shown at all
         flash(f"Could not load live server status: {error_message}", "danger")

    return render_template('livemap/server_status.html',
                           title='Live Server Status',
                           status_data=status_data,
                           error_message=error_message) # Pass error message for template to display if needed

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
