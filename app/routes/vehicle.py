from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import current_user, login_required
from app import db
from app.models import UserVehicle, VehicleRegion
from app.forms import RegisterVehicleForm
from app.services import vehicle_service
from flask_login import login_required

bp = Blueprint('vehicle', __name__)

@bp.route('/register', methods=['GET', 'POST'])
@login_required
def register_vehicle_route():
    form = RegisterVehicleForm()
    if form.validate_on_submit():
        new_vehicle, error_message = vehicle_service.register_vehicle(
            user_id=current_user.id,
            make=form.vehicle_make.data,
            model=form.vehicle_model.data,
            description=form.vehicle_description.data,
            vehicle_type_from_form=form.vehicle_type.data,
            region_name_from_form=form.region_format.data
        )

        if new_vehicle:
            flash(f'Vehicle "{new_vehicle.vehicle_make} {new_vehicle.vehicle_model}" registered successfully with license plate: {new_vehicle.license_plate}.', 'success')
            return redirect(url_for('vehicle.my_vehicles'))
        else:
            flash(f'Vehicle registration failed: {error_message}', 'danger')

    return render_template('vehicles/register_vehicle.html', title='Register New Vehicle', form=form)


@bp.route('/my_vehicles')
@login_required
def my_vehicles():
    page = request.args.get('page', 1, type=int)
    vehicles_pagination = vehicle_service.get_user_vehicles_paginated(current_user.id, page=page, per_page=10)
    return render_template('vehicles/my_vehicles.html', title='My Registered Vehicles',
                           vehicles_pagination=vehicles_pagination)


@bp.route('/<int:vehicle_id>/view')
@login_required
def view_vehicle(vehicle_id):
    vehicle = UserVehicle.query.filter_by(id=vehicle_id, user_id=current_user.id, is_active=True).first_or_404()
    return render_template('vehicles/view_vehicle.html', title=f'Vehicle: {vehicle.license_plate}', vehicle=vehicle)


@bp.route('/<int:vehicle_id>/deactivate', methods=['POST'])
@login_required
def deactivate_vehicle_route(vehicle_id):
    success, message = vehicle_service.deactivate_vehicle(vehicle_id, current_user.id)
    if success:
        flash(message, 'success')
    else:
        flash(message, 'danger')
    return redirect(url_for('vehicle.my_vehicles'))
