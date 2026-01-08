
from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models import Vehicle
from app.forms import VehicleForm

vehicles_bp = Blueprint('vehicles', __name__)

@vehicles_bp.route('/vehicles', methods=['GET', 'POST'])
@login_required
def locations():
    form = VehicleForm()
    if form.validate_on_submit():
        vehicle = Vehicle(
            name=form.name.data,
            location=form.location.data,
            notes=form.notes.data,
            user_id=current_user.id
        )
        db.session.add(vehicle)
        db.session.commit()
        flash('Vehicle location has been saved.', 'success')
        return redirect(url_for('vehicles.locations'))

    vehicles = Vehicle.query.order_by(Vehicle.timestamp.desc()).all()
    return render_template('vehicles/locations.html', title='Vehicle Locations', form=form, vehicles=vehicles)
