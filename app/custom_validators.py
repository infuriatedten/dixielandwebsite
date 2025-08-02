# app/custom_validators.py

from wtforms.validators import ValidationError
import re

def must_be_positive(form, field):
    if field.data is None or field.data <= 0:
        raise ValidationError('Value must be positive')

def password_complexity(form, field):
    password = field.data
    if not re.search(r'[A-Z]', password):
        raise ValidationError('Password must contain at least one uppercase letter.')
    if not re.search(r'[a-z]', password):
        raise ValidationError('Password must contain at least one lowercase letter.')
    if not re.search(r'[0-9]', password):
        raise ValidationError('Password must contain at least one number.')
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        raise ValidationError('Password must contain at least one special character.')
