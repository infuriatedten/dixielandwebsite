from functools import wraps
from flask import abort
from flask_login import current_user
from app.models import UserRole  # Adjust import path as needed

import logging

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != UserRole.ADMIN:
            logging.warning(
                f"Admin access denied for user {current_user.id if current_user.is_authenticated else 'Anonymous'}. "
                f"Role: {current_user.role if hasattr(current_user, 'role') else 'N/A'}"
            )
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def officer_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            abort(403)
        # Check if current_user.role has a 'value' attribute before accessing it
        if not hasattr(current_user, 'role') or not hasattr(current_user.role, 'value'):
            abort(403)
        
        allowed_roles = [UserRole.OFFICER.value, UserRole.ADMIN.value]
        if current_user.role.value not in allowed_roles:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function
