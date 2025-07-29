"""
API routes for AutoTest web interface.
RESTful API endpoints for programmatic access.
"""

from flask import Blueprint, jsonify

# Create blueprint
api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/status')
def status():
    """API status endpoint"""
    return jsonify({
        'status': 'ok',
        'service': 'AutoTest API',
        'version': '1.0.0'
    })

@api_bp.route('/')
def api_info():
    """API information endpoint"""
    return jsonify({
        'name': 'AutoTest API',
        'version': '1.0.0',
        'description': 'RESTful API for accessibility testing',
        'endpoints': {
            'status': '/api/status',
            'projects': '/api/projects',
            'testing': '/api/testing'
        }
    })