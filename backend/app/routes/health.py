from flask import Blueprint, jsonify

# Create a Blueprint for health-related routes
# Blueprints let us group related routes together
# 'health' is the blueprint name, __name__ helps Flask find resources
health_bp = Blueprint('health', __name__)

@health_bp.route('/api/health')
def health_check():
    """Simple health check endpoint.
    
    This route returns a JSON response to confirm the server is running.
    When you visit /api/health in your browser, you'll see this JSON.
    
    Returns:
        JSON object with status, message, and server info
    """
    return jsonify({
        'status': 'healthy',
        'message': 'Server is running!',
        'database': 'SQLite (via SQLAlchemy)',
        'note': 'This is your first working endpoint!'
    })

@health_bp.route('/api/hello')
def hello_world():
    """Another test endpoint to show how simple routes work."""
    return jsonify({
        'message': 'Hello from Flask!',
        'tip': 'Try changing this message and see it update instantly in development mode.'
    })