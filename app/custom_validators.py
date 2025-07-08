# app/custom_validators.py

from wtforms.validators import ValidationError

def must_be_positive(form, field):
    if field.data is None or field.data <= 0:
        raise ValidationError('Value must be positive')
