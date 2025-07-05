from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import current_user, login_required
from app import db
from app.models import UserVehicle, VehicleRegion # User model is available via current_user
from app.forms import RegisterVehicleForm
from app.services import vehicle_service # Import your service
from app.decorators import login_required # Assuming this is flask_login's

vehicle_bp = Blueprint('vehicle', __name__)

@vehicle_bp.route('/register', methods=['GET', 'POST'])
@login_required
def register_vehicle_route(): # Renamed to avoid conflict
    form = RegisterVehicleForm()
    if form.validate_on_submit():
        # The service function now takes region_name_from_form (string)
        new_vehicle, error_message = vehicle_service.register_vehicle(
            user_id=current_user.id,
            make=form.vehicle_make.data,
            model=form.vehicle_model.data,
            description=form.vehicle_description.data, # This is now TextArea for details
            vehicle_type_from_form=form.vehicle_type.data, # This is the main type string
            region_name_from_form=form.region_format.data
        )

        if new_vehicle:
            flash(f'Vehicle "{new_vehicle.vehicle_make} {new_vehicle.vehicle_model}" registered successfully with license plate: {new_vehicle.license_plate}.', 'success')
            return redirect(url_for('vehicle.my_vehicles'))
        else:
            flash(f'Vehicle registration failed: {error_message}', 'danger')

    return render_template('vehicle/register_vehicle.html', title='Register New Vehicle', form=form)


@vehicle_bp.route('/my_vehicles')
@login_required
def my_vehicles():
    page = request.args.get('page', 1, type=int)
    vehicles_pagination = vehicle_service.get_user_vehicles_paginated(current_user.id, page=page, per_page=10)
    return render_template('vehicle/my_vehicles.html', title='My Registered Vehicles',
                           vehicles_pagination=vehicles_pagination)


@vehicle_bp.route('/<int:vehicle_id>/view') # More RESTful
@login_required
def view_vehicle(vehicle_id):
    vehicle = UserVehicle.query.filter_by(id=vehicle_id, user_id=current_user.id, is_active=True).first_or_404()
    # TODO: Later, admins/officers might be able to view vehicles not their own.
    return render_template('vehicle/view_vehicle.html', title=f'Vehicle: {vehicle.license_plate}', vehicle=vehicle)


@vehicle_bp.route('/<int:vehicle_id>/deactivate', methods=['POST'])
@login_required
def deactivate_vehicle_route(vehicle_id): # Renamed
    success, message = vehicle_service.deactivate_vehicle(vehicle_id, current_user.id)
    if success:
        flash(message, 'success')
    else:
        flash(message, 'danger')
    return redirect(url_for('vehicle.my_vehicles'))

# Placeholder for form pre-filling logic using registered vehicles:
# This would typically be done in the routes for Tickets and Permits.
# Example (conceptual, to be integrated into dot.py routes):
#
# In dot.py, when rendering IssueTicketForm or ApplyPermitForm:
# if current_user.is_authenticated:
#     user_vehicles = UserVehicle.query.filter_by(user_id=current_user.id, is_active=True).all()
#     # For officer issuing ticket, they might search for user, then fetch that user's vehicles
#     # For user applying for permit, it's their own vehicles.
#     vehicle_choices = [(v.license_plate, f"{v.license_plate} ({v.make} {v.model})") for v in user_vehicles]
#     # Then pass vehicle_choices to the form if it has a SelectField for vehicles.
#     # Or, if pre-filling a text field, have a way for user to select from their vehicles.
#
# If a specific vehicle is selected (e.g., via query param from another page):
# selected_vehicle_plate = request.args.get('vehicle_plate')
# if selected_vehicle_plate:
#    vehicle = UserVehicle.query.filter_by(license_plate=selected_vehicle_plate, user_id=current_user.id).first()
#    if vehicle:
#        form.vehicle_id.data = vehicle.license_plate # For ticket's vehicle_id field
#        form.vehicle_type.data = vehicle.vehicle_type # For permit's vehicle_type field
#
# This pre-filling logic will be added in the respective DOT routes later as per full plan.
# For now, this blueprint focuses on vehicle registration and viewing.
