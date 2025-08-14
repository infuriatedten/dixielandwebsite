
from flask import Blueprint, jsonify
from app import db
from app.models import User

health_bp = Blueprint('health', __name__)

@health_bp.route('/health')
def health_check():
    """System health check endpoint"""
    try:
        # Test database connection
        user_count = User.query.count()
        
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'user_count': user_count,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500
