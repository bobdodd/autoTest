# AutoTest - Accessibility Testing Platform
# Copyright (C) 2025 Bob Dodd
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

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