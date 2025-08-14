
from wtforms.validators import ValidationError
from app.models import User, UserVehicle
import re

def unique_username(form, field):
    """Validate username is unique"""
    user = User.query.filter_by(username=field.data).first()
    if user:
        raise ValidationError('Username already exists.')

def unique_email(form, field):
    """Validate email is unique"""
    user = User.query.filter_by(email=field.data).first()
    if user:
        raise ValidationError('Email already registered.')

def unique_license_plate(form, field):
    """Validate license plate is unique"""
    vehicle = UserVehicle.query.filter_by(license_plate=field.data).first()
    if vehicle:
        raise ValidationError('License plate already registered.')

def strong_password(form, field):
    """Validate password strength"""
    password = field.data
    if len(password) < 8:
        raise ValidationError('Password must be at least 8 characters long.')
    
    if not re.search(r'[A-Z]', password):
        raise ValidationError('Password must contain at least one uppercase letter.')
    
    if not re.search(r'[a-z]', password):
        raise ValidationError('Password must contain at least one lowercase letter.')
    
    if not re.search(r'\d', password):
        raise ValidationError('Password must contain at least one number.')
