
from flask import request

def get_page_args():
    """Get page number from request args"""
    return request.args.get('page', 1, type=int)

def paginate_query(query, per_page=10):
    """Helper to paginate any query"""
    page = get_page_args()
    return query.paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )

def format_currency(amount, currency='GDC'):
    """Format currency display"""
    return f"{amount:,.2f} {currency}"

def time_ago(timestamp):
    """Calculate time ago from timestamp"""
    from datetime import datetime
    now = datetime.utcnow()
    diff = now - timestamp
    
    if diff.days > 0:
        return f"{diff.days} days ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} hours ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} minutes ago"
    else:
        return "Just now"

import hmac
import hashlib
import json
from flask import current_app

def verify_signature(data):
    """Verify the signature of the request"""
    if not isinstance(data, dict):
        return False

    signature = data.pop("signature", None)
    if not signature:
        return False

    # Sort the dictionary by key to ensure consistent hash
    sorted_data = json.dumps(data, sort_keys=True)

    # Calculate the expected signature
    expected_signature = hmac.new(
        current_app.config['SECRET_KEY'].encode('utf-8'),
        sorted_data.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(expected_signature, signature)
