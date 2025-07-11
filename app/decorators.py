from functools import wraps
from flask import abort
from flask_login import current_user
from app.models import UserRole  # Adjust import path as needed

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if user is authenticated and if their role's value matches UserRole.ADMIN's value.
        # This is more robust if current_user.role is sometimes a string and sometimes an enum.
        if not current_user.is_authenticated or \
           not hasattr(current_user, 'role') or \
           not hasattr(current_user.role, 'value') or \
           current_user.role.value != UserRole.ADMIN.value:
            # For debugging, you could add:
            # print(f"Admin access check failed. Auth: {current_user.is_authenticated}, Role: {getattr(current_user, 'role', 'N/A')}, Role Value: {getattr(current_user.role, 'value', 'N/A') if hasattr(current_user, 'role') else 'N/A'}")
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
