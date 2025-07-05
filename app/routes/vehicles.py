from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import current_user, login_required
from app import db
from app.models import UserVehicle, VehicleRegion # User already imported by other blueprints typically
from app.forms import RegisterVehicleForm
from app.services import vehicle_service # Use the new service
from app.decorators import login_required

vehicle_bp = Blueprint('vehicle', __name__) # Singular for consistency

# --- User Vehicle Routes ---
@vehicle_bp.route('/register', methods=['GET', 'POST'])
@login_required
def register_vehicle():
    form = RegisterVehicleForm()
    if form.validate_on_submit():
        new_vehicle, error = vehicle_service.register_vehicle_for_user(
            user_id=current_user.id,
            vehicle_make=form.vehicle_make.data,
            vehicle_model=form.vehicle_model.data,
            vehicle_description=form.vehicle_description.data,
            region_format_str=form.region_format.data # This is 'US' or 'EURO' string from form
        )

        if error:
            flash(f'Error registering vehicle: {error}', 'danger')
        else:
            flash(f'Vehicle "{new_vehicle.vehicle_description}" registered successfully with license plate: {new_vehicle.license_plate}!', 'success')
            return redirect(url_for('vehicle.my_vehicles'))

    return render_template('vehicles/register_vehicle.html', title='Register New Vehicle', form=form)


@vehicle_bp.route('/my_vehicles')
@login_required
def my_vehicles():
    page = request.args.get('page', 1, type=int)
    vehicles_pagination = UserVehicle.query.filter_by(user_id=current_user.id, is_active=True)\
                                      .order_by(UserVehicle.registration_date.desc())\
                                      .paginate(page=page, per_page=10) # Configurable

    return render_template('vehicles/my_vehicles.html', title='My Registered Vehicles',
                           vehicles_pagination=vehicles_pagination)

@vehicle_bp.route('/<int:vehicle_id>')
@login_required
def view_vehicle_detail(vehicle_id):
    vehicle = UserVehicle.query.get_or_404(vehicle_id)
    if vehicle.user_id != current_user.id and current_user.role != UserRole.ADMIN: # Admin can view any
        flash("You are not authorized to view this vehicle's details.", "danger")
        return redirect(url_for('vehicle.my_vehicles'))

    # TODO: In future, could list associated tickets/permits for this vehicle.
    return render_template('vehicles/view_vehicle_detail.html', title=f"Vehicle: {vehicle.license_plate}", vehicle=vehicle)


@vehicle_bp.route('/<int:vehicle_id>/deactivate', methods=['POST'])
@login_required
def deactivate_vehicle(vehicle_id):
    vehicle = UserVehicle.query.get_or_404(vehicle_id)
    if vehicle.user_id != current_user.id:
        flash("You are not authorized to deactivate this vehicle.", "danger")
    elif not vehicle.is_active:
        flash("This vehicle is already inactive.", "info")
    else:
        vehicle.is_active = False
        db.session.commit()
        flash(f"Vehicle {vehicle.license_plate} has been deactivated.", "success")
    return redirect(url_for('vehicle.my_vehicles'))

# Admin routes for managing all vehicles could go here or in admin_bp if preferred.
# For now, keeping user-focused vehicle management here.
```
