"""
Flask web application for AutoTest accessibility testing tool
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from typing import Dict, Any, Optional
import os

from autotest.utils.config import Config
from autotest.utils.logger import setup_logger, get_logger
from autotest.core.database import DatabaseConnection
from autotest.core.project_manager import ProjectManager
from autotest.core.website_manager import WebsiteManager
from autotest.core.scraper import WebScraper
from autotest.core.accessibility_tester import AccessibilityTester
from autotest.testing.rules.rule_engine import RuleEngine
from autotest.testing.reporters.severity_manager import SeverityManager
from autotest.services.scheduler_service import SchedulerService
from autotest.services.testing_service import TestingService
from autotest.services.history_service import HistoryService
from autotest.services.reporting_service import ReportingService


def create_app(config: Optional[Config] = None) -> Flask:
    """
    Create and configure Flask application
    
    Args:
        config: Application configuration (optional)
    
    Returns:
        Configured Flask application
    """
    app = Flask(__name__)
    
    # Load configuration
    if config is None:
        config = Config()
    
    app.config['SECRET_KEY'] = os.urandom(24)
    app.config['AUTOTEST_CONFIG'] = config
    
    # Setup logging
    logger = get_logger(__name__)
    
    # Initialize database connection
    db_connection = DatabaseConnection(config)
    
    try:
        db_connection.connect()
        logger.info("Database connection established")
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        raise
    
    # Initialize managers
    project_manager = ProjectManager(db_connection)
    website_manager = WebsiteManager(db_connection)
    web_scraper = WebScraper(config, db_connection)
    accessibility_tester = AccessibilityTester(config, db_connection)
    rule_engine = RuleEngine(config)
    severity_manager = SeverityManager()
    
    # Initialize services
    testing_service = TestingService(config, db_connection)
    scheduler_service = SchedulerService(config, db_connection, testing_service)
    history_service = HistoryService(config, db_connection)
    reporting_service = ReportingService(config, db_connection)
    
    # Store managers in app context
    app.config['DB_CONNECTION'] = db_connection
    app.config['PROJECT_MANAGER'] = project_manager
    app.config['WEBSITE_MANAGER'] = website_manager
    app.config['WEB_SCRAPER'] = web_scraper
    app.config['ACCESSIBILITY_TESTER'] = accessibility_tester
    app.config['RULE_ENGINE'] = rule_engine
    app.config['SEVERITY_MANAGER'] = severity_manager
    app.config['TESTING_SERVICE'] = testing_service
    app.config['SCHEDULER_SERVICE'] = scheduler_service
    app.config['HISTORY_SERVICE'] = history_service
    app.config['REPORTING_SERVICE'] = reporting_service
    
    # Register blueprints
    from autotest.web.routes.main import main_bp
    from autotest.web.routes.projects import projects_bp
    from autotest.web.routes.websites import websites_bp
    from autotest.web.routes.testing import testing_bp
    from autotest.web.routes.scheduler import scheduler_bp
    from autotest.web.routes.history import history_bp
    from autotest.web.routes.reports import reports_bp
    from autotest.web.routes.api import api_bp
    
    # Initialize blueprint services
    from autotest.web.routes.testing import init_testing_service
    from autotest.web.routes.scheduler import init_scheduler_service
    from autotest.web.routes.history import init_history_service
    from autotest.web.routes.reports import init_reporting_service
    
    init_testing_service(config, db_connection)
    init_scheduler_service(config, db_connection, testing_service)
    init_history_service(config, db_connection)
    init_reporting_service(config, db_connection)
    
    app.register_blueprint(main_bp)
    app.register_blueprint(projects_bp, url_prefix='/projects')
    app.register_blueprint(websites_bp, url_prefix='/websites')
    app.register_blueprint(testing_bp, url_prefix='/testing')
    app.register_blueprint(scheduler_bp, url_prefix='/scheduler')
    app.register_blueprint(history_bp, url_prefix='/history')
    app.register_blueprint(reports_bp, url_prefix='/reports')
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        """Handle 404 errors with accessible error page"""
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors with accessible error page"""
        logger.error(f"Internal server error: {error}")
        return render_template('errors/500.html'), 500
    
    # Template filters
    @app.template_filter('severity_badge')
    def severity_badge_filter(severity: str) -> str:
        """Generate HTML badge for severity level"""
        badges = {
            'critical': '<span class="badge badge-critical" aria-label="Critical severity">Critical</span>',
            'serious': '<span class="badge badge-serious" aria-label="Serious severity">Serious</span>',
            'moderate': '<span class="badge badge-moderate" aria-label="Moderate severity">Moderate</span>',
            'minor': '<span class="badge badge-minor" aria-label="Minor severity">Minor</span>'
        }
        return badges.get(severity, f'<span class="badge badge-unknown">{severity}</span>')
    
    @app.template_filter('format_datetime')
    def format_datetime_filter(datetime_obj):
        """Format datetime for display"""
        if not datetime_obj:
            return 'Never'
        return datetime_obj.strftime('%Y-%m-%d %H:%M')
    
    @app.template_filter('pluralize')
    def pluralize_filter(count: int, singular: str, plural: str = None) -> str:
        """Pluralize words based on count"""
        if plural is None:
            plural = singular + 's'
        return singular if count == 1 else plural
    
    # Template globals
    @app.template_global()
    def get_severity_color(severity: str) -> str:
        """Get CSS color class for severity"""
        colors = {
            'critical': 'text-critical',
            'serious': 'text-serious', 
            'moderate': 'text-moderate',
            'minor': 'text-minor'
        }
        return colors.get(severity, 'text-secondary')
    
    @app.template_global()
    def get_severity_icon(severity: str) -> str:
        """Get icon class for severity"""
        icons = {
            'critical': 'icon-alert-triangle',
            'serious': 'icon-alert-circle',
            'moderate': 'icon-info',
            'minor': 'icon-check-circle'
        }
        return icons.get(severity, 'icon-help-circle')
    
    # Context processors
    @app.context_processor
    def inject_globals():
        """Inject global variables into templates"""
        return {
            'app_name': 'AutoTest',
            'app_version': '1.0.0',
            'accessibility_enabled': True
        }
    
    # Cleanup on app teardown
    @app.teardown_appcontext
    def close_db(error):
        """Close database connection and scheduler on app teardown"""
        # Stop scheduler service
        if hasattr(app.config, 'SCHEDULER_SERVICE'):
            try:
                app.config['SCHEDULER_SERVICE'].stop_scheduler()
            except Exception as e:
                logger.warning(f"Error stopping scheduler service: {e}")
        
        # Close database connection
        if hasattr(app.config, 'DB_CONNECTION'):
            try:
                app.config['DB_CONNECTION'].disconnect()
            except Exception as e:
                logger.warning(f"Error closing database connection: {e}")
    
    logger.info("Flask application created successfully")
    return app


def run_app():
    """Run the Flask application in development mode"""
    config = Config()
    app = create_app(config)
    
    host = config.get('server.host', '127.0.0.1')
    port = config.get('server.port', 5000)
    debug = config.get('server.debug', True)
    
    app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    run_app()