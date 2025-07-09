from functools import wraps
from flask import abort
from flask_login import current_user
from app.models import UserRole  # Adjust import path as needed

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != UserRole.ADMIN:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def officer_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role not in [UserRole.OFFICER, UserRole.ADMIN]:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function
