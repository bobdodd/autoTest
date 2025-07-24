"""
Main routes for AutoTest web application
"""

from flask import Blueprint, render_template, current_app, request
from typing import Dict, Any

from autotest.utils.logger import get_logger

main_bp = Blueprint('main', __name__)
logger = get_logger(__name__)


@main_bp.route('/')
def index():
    """
    Home page with dashboard overview
    """
    try:
        project_manager = current_app.config['PROJECT_MANAGER']
        
        # Get projects summary
        projects_result = project_manager.list_projects()
        
        if projects_result['success']:
            projects = projects_result['projects']
            
            # Calculate dashboard statistics
            total_projects = len(projects)
            total_websites = sum(p.get('website_count', 0) for p in projects)
            total_pages = sum(p.get('page_count', 0) for p in projects)
            total_violations = sum(p.get('total_violations', 0) for p in projects)
            total_tests = sum(p.get('total_tests', 0) for p in projects)
            
            # Recent projects (last 5)
            recent_projects = sorted(projects, 
                                   key=lambda x: x.get('last_modified') or x.get('created_date'),
                                   reverse=True)[:5]
            
            dashboard_stats = {
                'total_projects': total_projects,
                'total_websites': total_websites,
                'total_pages': total_pages,
                'total_violations': total_violations,
                'total_tests': total_tests,
                'recent_projects': recent_projects
            }
        else:
            dashboard_stats = {
                'total_projects': 0,
                'total_websites': 0,
                'total_pages': 0,
                'total_violations': 0,
                'total_tests': 0,
                'recent_projects': []
            }
            logger.warning(f"Failed to load projects: {projects_result.get('error')}")
        
        return render_template('dashboard.html', stats=dashboard_stats)
        
    except Exception as e:
        logger.error(f"Error loading dashboard: {e}")
        return render_template('dashboard.html', stats={
            'total_projects': 0,
            'total_websites': 0, 
            'total_pages': 0,
            'total_violations': 0,
            'total_tests': 0,
            'recent_projects': []
        })


@main_bp.route('/about')
def about():
    """
    About page with application information
    """
    return render_template('about.html')


@main_bp.route('/help')
def help():
    """
    Help page with user documentation
    """
    return render_template('help.html')


@main_bp.route('/accessibility')
def accessibility():
    """
    Accessibility statement page
    """
    return render_template('accessibility.html')


@main_bp.route('/health')
def health_check():
    """
    Health check endpoint for monitoring
    """
    try:
        # Check database connection
        db_connection = current_app.config['DB_CONNECTION']
        db_connection.client.admin.command('ping')
        
        return {
            'status': 'healthy',
            'database': 'connected',
            'timestamp': '2025-01-24T00:00:00Z'
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            'status': 'unhealthy',
            'database': 'disconnected',
            'error': str(e),
            'timestamp': '2025-01-24T00:00:00Z'
        }, 500