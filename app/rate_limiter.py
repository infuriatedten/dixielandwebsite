
from flask import request, jsonify
from functools import wraps
from collections import defaultdict
import time

# Simple in-memory rate limiter (use Redis in production)
request_counts = defaultdict(list)

def rate_limit(max_requests=60, window=60):
    """Rate limit decorator: max_requests per window seconds"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
            now = time.time()
            
            # Clean old requests
            request_counts[client_ip] = [
                timestamp for timestamp in request_counts[client_ip]
                if now - timestamp < window
            ]
            
            # Check if limit exceeded
            if len(request_counts[client_ip]) >= max_requests:
                return jsonify({'error': 'Rate limit exceeded'}), 429
            
            # Add current request
            request_counts[client_ip].append(now)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator
