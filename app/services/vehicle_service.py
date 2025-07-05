from app import db
from app.models import UserVehicle, VehicleRegion, User
from datetime import datetime
import random
import string
from flask import current_app

def generate_license_plate_number(region_enum):
    """
    Generates a license plate number based on the region.
    US: 123-ABC
    EURO: ABC-123
    Ensures basic uniqueness attempt by checking existing plates.
    """
    MAX_TRIES = 100 # Max attempts to find a unique plate
    for _ in range(MAX_TRIES):
        if region_enum == VehicleRegion.US:
            numbers = ''.join(random.choices(string.digits, k=3))
            letters = ''.join(random.choices(string.ascii_uppercase, k=3))
            plate = f"{numbers}-{letters}"
        elif region_enum == VehicleRegion.EURO:
            letters = ''.join(random.choices(string.ascii_uppercase, k=3))
            numbers = ''.join(random.choices(string.digits, k=3))
            plate = f"{letters}-{numbers}"
        else:
            # Fallback for OTHER_DEFAULT or any unexpected region
            # Generic format: LLLNNN (L=Letter, N=Number)
            letters = ''.join(random.choices(string.ascii_uppercase, k=3))
            numbers = ''.join(random.choices(string.digits, k=3))
            plate = f"{letters}{numbers}" # e.g., XYZ123

        if not UserVehicle.query.filter_by(license_plate=plate).first():
            return plate

    current_app.logger.error("Could not generate a unique license plate after max tries.")
    # Fallback to a more robust unique string if simple random generation fails repeatedly
    # This indicates a very high number of plates or a flaw in the random generation for the namespace size.
    timestamp_ms = int(datetime.utcnow().timestamp() * 1000)
    random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"ERR-{timestamp_ms}-{random_suffix}"[:20] # Ensure it fits in DB field

def register_vehicle(user_id, make, model, description, vehicle_type_from_form, region_name_from_form):
    """
    Registers a new vehicle for a user, generating a license plate.
    region_name_from_form is the string name of the enum member (e.g., "US", "EURO").
    """
    user = User.query.get(user_id)
    if not user:
        current_app.logger.error(f"Attempt to register vehicle for non-existent user ID: {user_id}")
        return None, "User not found."

    try:
        # Ensure region_name_from_form is a valid key in VehicleRegion enum
        if not hasattr(VehicleRegion, region_name_from_form.upper()):
            raise KeyError # Or handle more gracefully depending on how form passes it
        region_enum = VehicleRegion[region_name_from_form.upper()]
    except KeyError:
        current_app.logger.error(f"Invalid vehicle region specified: {region_name_from_form}")
        return None, "Invalid vehicle region specified."

    license_plate = generate_license_plate_number(region_enum)
    if "ERR-" in license_plate:
         return None, "Failed to generate a unique license plate. System may be under high load. Please try again."

    new_vehicle = UserVehicle(
        user_id=user_id,
        vehicle_make=make,
        vehicle_model=model,
        vehicle_description=description, # This was vehicle_type in plan, but form has description
        vehicle_type=vehicle_type_from_form, # Add vehicle_type from form as per new plan
        license_plate=license_plate,
        region_format=region_enum,
        registration_date=datetime.utcnow()
    )
    db.session.add(new_vehicle)
    try:
        db.session.commit()
        current_app.logger.info(f"Vehicle registered for User {user_id} with plate {license_plate}.")
        return new_vehicle, None
    except Exception as e:
        db.session.rollback()
        # More specific check for unique constraint violation
        error_str = str(e).lower()
        if ('unique constraint failed' in error_str and 'user_vehicles.license_plate' in error_str) or \
           ('duplicate entry' in error_str and 'for key' in error_str and 'user_vehicles.license_plate' in error_str) or \
           ('duplicate key value violates unique constraint' in error_str and 'user_vehicles_license_plate_key' in error_str): # PostgreSQL
            current_app.logger.warning(f"License plate collision during commit for User {user_id}: {license_plate}. Error: {e}")
            return None, "Failed to register vehicle due to a license plate conflict (very rare). Please try again."

        current_app.logger.error(f"Error registering vehicle for User {user_id}: {e}", exc_info=True)
        return None, f"An unexpected error occurred while registering the vehicle."


def get_user_vehicles_paginated(user_id, page=1, per_page=10):
    """Gets paginated active vehicles for a specific user."""
    return UserVehicle.query.filter_by(user_id=user_id, is_active=True)\
                            .order_by(UserVehicle.registration_date.desc())\
                            .paginate(page=page, per_page=per_page, error_out=False)

def get_vehicle_by_plate(license_plate_str):
    """Finds an active vehicle by its license plate."""
    return UserVehicle.query.filter(UserVehicle.license_plate.ilike(license_plate_str), UserVehicle.is_active==True).first()

def deactivate_vehicle(vehicle_id, user_id_requesting):
    """Deactivates a vehicle if the requesting user is the owner."""
    vehicle = UserVehicle.query.get(vehicle_id)
    if vehicle and vehicle.user_id == user_id_requesting:
        if not vehicle.is_active:
            return True, "Vehicle already inactive." # Or some other status
        vehicle.is_active = False
        try:
            db.session.commit()
            current_app.logger.info(f"Vehicle {vehicle_id} deactivated for User {user_id_requesting}.")
            return True, "Vehicle deactivated successfully."
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error deactivating vehicle {vehicle_id}: {e}", exc_info=True)
            return False, "Error deactivating vehicle."
    elif not vehicle:
        return False, "Vehicle not found."
    else: # vehicle.user_id != user_id_requesting
        return False, "You are not authorized to deactivate this vehicle."
