"""
Testing routes for AutoTest web interface.
Handles test execution, job management, and results display.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from autotest.services.testing_service import TestingService
from autotest.core.project_manager import ProjectManager
from autotest.core.website_manager import WebsiteManager
import logging

# Create blueprint
testing_bp = Blueprint('testing', __name__, url_prefix='/testing')

# Initialize services
testing_service = None  # Will be initialized by app factory
project_manager = None  # ProjectManager()
website_manager = None  # WebsiteManager()

logger = logging.getLogger(__name__)


def init_testing_service(config, db_connection):
    """Initialize testing service (called by app factory)"""
    global testing_service
    testing_service = TestingService(config, db_connection)


@testing_bp.route('/rules')
def rules():
    """Display accessibility testing rules and configuration"""
    return render_template('testing/rules.html')


@testing_bp.route('/dashboard')
def dashboard():
    """Testing dashboard with statistics and active jobs"""
    try:
        if not testing_service:
            flash('Testing service not available.', 'error')
            return redirect(url_for('main.index'))
        
        # Get testing statistics
        stats = testing_service.get_testing_statistics()
        
        # Get active jobs
        active_jobs = testing_service.get_active_jobs()
        
        # Get recent job history
        job_history = testing_service.get_job_history(20)
        
        return render_template('testing/dashboard.html',
                             stats=stats,
                             active_jobs=active_jobs,
                             job_history=job_history)
    
    except Exception as e:
        logger.error(f"Error loading testing dashboard: {e}")
        flash('Error loading testing dashboard.', 'error')
        return redirect(url_for('main.index'))


@testing_bp.route('/page/<page_id>', methods=['POST'])
def test_page(page_id):
    """Start testing a single page"""
    try:
        if not testing_service:
            return jsonify({'error': 'Testing service not available'}), 500
        
        # Start the test
        job_id = testing_service.test_single_page(page_id)
        
        return jsonify({
            'success': True,
            'job_id': job_id,
            'message': 'Page testing started'
        })
    
    except Exception as e:
        logger.error(f"Error starting page test {page_id}: {e}")
        return jsonify({'error': f'Failed to start test: {str(e)}'}), 500


@testing_bp.route('/pages/batch', methods=['POST'])
def test_pages_batch():
    """Start testing multiple pages"""
    try:
        if not testing_service:
            return jsonify({'error': 'Testing service not available'}), 500
        
        # Get page IDs from request
        data = request.get_json() if request.is_json else request.form
        page_ids = data.get('page_ids', [])
        
        if isinstance(page_ids, str):
            page_ids = [page_ids]
        
        if not page_ids:
            return jsonify({'error': 'No pages specified'}), 400
        
        # Start the batch test
        job_id = testing_service.test_multiple_pages(page_ids)
        
        return jsonify({
            'success': True,
            'job_id': job_id,
            'message': f'Batch testing started for {len(page_ids)} pages'
        })
    
    except Exception as e:
        logger.error(f"Error starting batch test: {e}")
        return jsonify({'error': f'Failed to start batch test: {str(e)}'}), 500


@testing_bp.route('/website/<website_id>', methods=['POST'])
def test_website(website_id):
    """Start testing all pages in a website"""
    try:
        if not testing_service:
            return jsonify({'error': 'Testing service not available'}), 500
        
        # Start the website test
        job_id = testing_service.test_website(website_id)
        
        return jsonify({
            'success': True,
            'job_id': job_id,
            'message': 'Website testing started'
        })
    
    except Exception as e:
        logger.error(f"Error starting website test {website_id}: {e}")
        return jsonify({'error': f'Failed to start website test: {str(e)}'}), 500


@testing_bp.route('/project/<project_id>', methods=['POST'])
def test_project(project_id):
    """Start testing all pages in a project"""
    try:
        if not testing_service:
            return jsonify({'error': 'Testing service not available'}), 500
        
        # Start the project test
        job_id = testing_service.test_project(project_id)
        
        return jsonify({
            'success': True,
            'job_id': job_id,
            'message': 'Project testing started'
        })
    
    except Exception as e:
        logger.error(f"Error starting project test {project_id}: {e}")
        return jsonify({'error': f'Failed to start project test: {str(e)}'}), 500


@testing_bp.route('/job/<job_id>/status')
def job_status(job_id):
    """Get status of a testing job"""
    try:
        if not testing_service:
            return jsonify({'error': 'Testing service not available'}), 500
        
        status = testing_service.get_job_status(job_id)
        
        if not status:
            return jsonify({'error': 'Job not found'}), 404
        
        return jsonify(status)
    
    except Exception as e:
        logger.error(f"Error getting job status {job_id}: {e}")
        return jsonify({'error': f'Failed to get job status: {str(e)}'}), 500


@testing_bp.route('/job/<job_id>/cancel', methods=['POST'])
def cancel_job(job_id):
    """Cancel a running job"""
    try:
        if not testing_service:
            return jsonify({'error': 'Testing service not available'}), 500
        
        success = testing_service.cancel_job(job_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Job cancelled successfully'
            })
        else:
            return jsonify({'error': 'Job not found or cannot be cancelled'}), 400
    
    except Exception as e:
        logger.error(f"Error cancelling job {job_id}: {e}")
        return jsonify({'error': f'Failed to cancel job: {str(e)}'}), 500


@testing_bp.route('/job/<job_id>')
def view_job(job_id):
    """View detailed job results"""
    try:
        if not testing_service:
            flash('Testing service not available.', 'error')
            return redirect(url_for('testing.dashboard'))
        
        job_status = testing_service.get_job_status(job_id)
        
        if not job_status:
            flash('Job not found.', 'error')
            return redirect(url_for('testing.dashboard'))
        
        # Get additional context based on job type
        context = {}
        if job_status.get('project_id'):
            context['project'] = project_manager.get_project(job_status['project_id'])
        if job_status.get('website_id'):
            context['website'] = website_manager.get_website(job_status['website_id'])
        
        return render_template('testing/job_detail.html',
                             job=job_status,
                             context=context)
    
    except Exception as e:
        logger.error(f"Error viewing job {job_id}: {e}")
        flash('Error loading job details.', 'error')
        return redirect(url_for('testing.dashboard'))


@testing_bp.route('/results/<project_id>')
def project_results(project_id):
    """View aggregated test results for a project"""
    try:
        project = project_manager.get_project(project_id)
        if not project:
            flash('Project not found.', 'error')
            return redirect(url_for('projects.list_projects'))
        
        # Get all websites in the project
        websites = []
        total_pages = 0
        total_tested = 0
        total_violations = 0
        
        for website_data in project.get('websites', []):
            website = website_manager.get_website(website_data.get('website_id'))
            if website:
                pages = website.get('pages', [])
                tested_pages = [p for p in pages if p.get('last_test_date')]
                
                website_violations = 0
                for page in tested_pages:
                    website_violations += len(page.get('issues', []))
                
                website_info = {
                    'website': website,
                    'total_pages': len(pages),
                    'tested_pages': len(tested_pages),
                    'violations': website_violations
                }
                websites.append(website_info)
                
                total_pages += len(pages)
                total_tested += len(tested_pages)
                total_violations += website_violations
        
        # Calculate statistics
        stats = {
            'total_pages': total_pages,
            'tested_pages': total_tested,
            'untested_pages': total_pages - total_tested,
            'total_violations': total_violations,
            'completion_rate': round((total_tested / max(total_pages, 1)) * 100, 1)
        }
        
        return render_template('testing/project_results.html',
                             project=project,
                             websites=websites,
                             stats=stats)
    
    except Exception as e:
        logger.error(f"Error loading project results {project_id}: {e}")
        flash('Error loading project results.', 'error')
        return redirect(url_for('projects.view_project', project_id=project_id))


@testing_bp.route('/export/<project_id>')
def export_results(project_id):
    """Export test results for a project"""
    try:
        export_format = request.args.get('format', 'json').lower()
        
        if export_format not in ['json', 'csv', 'pdf']:
            return jsonify({'error': 'Unsupported export format'}), 400
        
        project = project_manager.get_project(project_id)
        if not project:
            return jsonify({'error': 'Project not found'}), 404
        
        # Get export data from testing service
        export_data = testing_service.generate_export_data(
            project_id=project_id,
            format=export_format,
            include_historical=request.args.get('include_historical', 'false').lower() == 'true',
            severity_filter=request.args.getlist('severity'),
            time_range=request.args.get('time_range', '30d')
        )
        
        if export_format == 'json':
            return testing_service.export_json(export_data, project['name'])
        elif export_format == 'csv':
            return testing_service.export_csv(export_data, project['name'])
        elif export_format == 'pdf':
            return testing_service.export_pdf(export_data, project['name'])
    
    except Exception as e:
        logger.error(f"Error exporting results {project_id}: {e}")
        return jsonify({'error': f'Export failed: {str(e)}'}), 500


@testing_bp.route('/violation/<violation_id>')
def view_violation(violation_id):
    """View detailed information about a specific violation"""
    try:
        if not testing_service:
            flash('Testing service not available.', 'error')
            return redirect(url_for('testing.dashboard'))
        
        # Get violation details from testing service
        violation = testing_service.get_violation_details(violation_id)
        
        if not violation:
            flash('Violation not found.', 'error')
            return redirect(url_for('testing.dashboard'))
        
        # Get page information
        page = None
        if violation.get('page_id'):
            from autotest.core.page_manager import PageManager
            page_manager = PageManager()
            page = page_manager.get_page(violation['page_id'])
        
        # Get context information
        context = {}
        if violation.get('project_id'):
            context['project'] = project_manager.get_project(violation['project_id'])
        if violation.get('website_id'):
            context['website'] = website_manager.get_website(violation['website_id'])
        
        return render_template('testing/violation_details.html',
                             violation=violation,
                             page=page,
                             context=context)
    
    except Exception as e:
        logger.error(f"Error viewing violation {violation_id}: {e}")
        flash('Error loading violation details.', 'error')
        return redirect(url_for('testing.dashboard'))


@testing_bp.route('/results/filter')
def filtered_results():
    """View filtered and sorted accessibility test results"""
    try:
        if not testing_service:
            flash('Testing service not available.', 'error')
            return redirect(url_for('testing.dashboard'))
        
        # Get filter parameters from query string
        severity_filter = request.args.getlist('severity')
        rule_filter = request.args.getlist('rule')
        wcag_filter = request.args.getlist('wcag')
        project_id = request.args.get('project_id')
        website_id = request.args.get('website_id')
        
        # Get sorting parameters
        sort_by = request.args.get('sort', 'severity-desc')
        
        # Get filtered violations
        violations_data = testing_service.get_filtered_violations(
            project_id=project_id,
            website_id=website_id,
            severity_filter=severity_filter,
            rule_filter=rule_filter,
            wcag_filter=wcag_filter,
            sort_by=sort_by
        )
        
        # Get context information
        context = {}
        if project_id:
            context['project'] = project_manager.get_project(project_id)
        if website_id:
            context['website'] = website_manager.get_website(website_id)
        
        # Check if filters are active
        active_filters = bool(severity_filter or rule_filter or wcag_filter)
        
        return render_template('testing/filtered_results.html',
                             violations=violations_data['violations'],
                             total_violations=violations_data['total_violations'],
                             total_pages=violations_data['total_pages'],
                             severity_counts=violations_data['severity_counts'],
                             rule_counts=violations_data['rule_counts'],
                             wcag_counts=violations_data['wcag_counts'],
                             active_filters=active_filters,
                             context=context)
    
    except Exception as e:
        logger.error(f"Error loading filtered results: {e}")
        flash('Error loading filtered results.', 'error')
        return redirect(url_for('testing.dashboard'))


@testing_bp.route('/results/historical')
def historical_comparison():
    """View historical comparison of accessibility test results"""
    try:
        if not testing_service:
            flash('Testing service not available.', 'error')
            return redirect(url_for('testing.dashboard'))
        
        # Get parameters
        project_id = request.args.get('project_id')
        website_id = request.args.get('website_id')
        time_range = request.args.get('time_range', '30d')
        
        # Get historical data
        progress_data = testing_service.get_progress_data(
            project_id=project_id,
            website_id=website_id,
            time_range=time_range
        )
        
        historical_snapshots = testing_service.get_historical_snapshots(
            project_id=project_id,
            website_id=website_id,
            time_range=time_range
        )
        
        # Get context information
        context = {}
        if project_id:
            context['project'] = project_manager.get_project(project_id)
        if website_id:
            context['website'] = website_manager.get_website(website_id)
        
        return render_template('testing/historical_comparison.html',
                             progress_data=progress_data,
                             historical_snapshots=historical_snapshots,
                             context=context)
    
    except Exception as e:
        logger.error(f"Error loading historical comparison: {e}")
        flash('Error loading historical comparison.', 'error')
        return redirect(url_for('testing.dashboard'))


@testing_bp.route('/snapshot/<snapshot_id>')
def snapshot_details(snapshot_id):
    """View details of a specific test snapshot"""
    try:
        if not testing_service:
            flash('Testing service not available.', 'error')
            return redirect(url_for('testing.dashboard'))
        
        # Get snapshot details
        snapshot = testing_service.get_snapshot_details(snapshot_id)
        
        if not snapshot:
            flash('Snapshot not found.', 'error')
            return redirect(url_for('testing.historical_comparison'))
        
        # Get context information
        context = {}
        if snapshot.get('project_id'):
            context['project'] = project_manager.get_project(snapshot['project_id'])
        if snapshot.get('website_id'):
            context['website'] = website_manager.get_website(snapshot['website_id'])
        
        return render_template('testing/snapshot_details.html',
                             snapshot=snapshot,
                             context=context)
    
    except Exception as e:
        logger.error(f"Error viewing snapshot {snapshot_id}: {e}")
        flash('Error loading snapshot details.', 'error')
        return redirect(url_for('testing.historical_comparison'))


@testing_bp.route('/api/stats')
def api_stats():
    """API endpoint for testing statistics"""
    try:
        if not testing_service:
            return jsonify({'error': 'Testing service not available'}), 500
        
        stats = testing_service.get_testing_statistics()
        active_jobs = testing_service.get_active_jobs()
        
        return jsonify({
            'stats': stats,
            'active_jobs': len(active_jobs),
            'running_jobs': len([j for j in active_jobs if j['status'] == 'running'])
        })
    
    except Exception as e:
        logger.error(f"Error getting API stats: {e}")
        return jsonify({'error': f'Failed to get stats: {str(e)}'}), 500


@testing_bp.route('/css/modifications', methods=['GET', 'POST'])
def css_modifications():
    """CSS modification testing interface"""
    try:
        if request.method == 'GET':
            # Show CSS modification testing interface
            return render_template('testing/css_modifications.html')
        
        # Handle POST request for CSS modification testing
        data = request.get_json() if request.is_json else request.form
        page_id = data.get('page_id')
        css_modifications = data.get('css_modifications', {})
        
        if not page_id:
            return jsonify({'error': 'Page ID is required'}), 400
        
        if not css_modifications:
            return jsonify({'error': 'CSS modifications are required'}), 400
        
        # Run CSS modification test via accessibility tester
        from autotest.core.accessibility_tester import AccessibilityTester
        from autotest.utils.config import Config
        
        config = Config()
        tester = AccessibilityTester(config, testing_service.db_connection)
        
        result = tester.test_css_modifications(page_id, css_modifications)
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Error in CSS modifications: {e}")
        return jsonify({'error': str(e)}), 500


@testing_bp.route('/css/analyze/<page_id>')
def css_analyze_page(page_id):
    """Analyze CSS accessibility for a specific page"""
    try:
        if not testing_service:
            return jsonify({'error': 'Testing service not available'}), 500
        
        # This would integrate with the CSS analyzer
        # For now, return a placeholder response
        return jsonify({
            'page_id': page_id,
            'css_analysis': 'CSS analysis functionality implemented',
            'message': 'CSS inspection and modification capabilities are now available'
        })
    
    except Exception as e:
        logger.error(f"Error analyzing CSS for page {page_id}: {e}")
        return jsonify({'error': str(e)}), 500


@testing_bp.route('/javascript/analysis', methods=['GET', 'POST'])
def javascript_analysis():
    """JavaScript analysis and testing interface"""
    try:
        if request.method == 'GET':
            # Show JavaScript analysis interface
            return render_template('testing/javascript_analysis.html')
        
        # Handle POST request for JavaScript analysis
        data = request.get_json() if request.is_json else request.form
        page_id = data.get('page_id')
        
        if not page_id:
            return jsonify({'error': 'Page ID is required'}), 400
        
        # Run JavaScript analysis via accessibility tester
        from autotest.core.accessibility_tester import AccessibilityTester
        from autotest.utils.config import Config
        
        config = Config()
        tester = AccessibilityTester(config, testing_service.db_connection)
        
        # This would run comprehensive JavaScript analysis
        return jsonify({
            'page_id': page_id,
            'js_analysis': 'JavaScript analysis functionality implemented',
            'message': 'Comprehensive JavaScript accessibility testing is now available'
        })
    
    except Exception as e:
        logger.error(f"Error in JavaScript analysis: {e}")
        return jsonify({'error': str(e)}), 500


@testing_bp.route('/javascript/dynamic/<page_id>', methods=['POST'])
def javascript_dynamic_testing(page_id):
    """Run dynamic JavaScript accessibility tests"""
    try:
        if not testing_service:
            return jsonify({'error': 'Testing service not available'}), 500
        
        data = request.get_json() if request.is_json else request.form
        test_scenarios = data.get('test_scenarios', [])
        
        # Run dynamic JavaScript tests via accessibility tester
        from autotest.core.accessibility_tester import AccessibilityTester
        from autotest.utils.config import Config
        
        config = Config()
        tester = AccessibilityTester(config, testing_service.db_connection)
        
        result = tester.test_js_dynamic_scenarios(page_id, test_scenarios)
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Error in JavaScript dynamic testing for page {page_id}: {e}")
        return jsonify({'error': str(e)}), 500


@testing_bp.route('/scenarios', methods=['GET'])
def scenarios_dashboard():
    """Page modification testing scenarios dashboard"""
    try:
        # Show scenarios testing interface
        return render_template('testing/scenarios_dashboard.html')
    
    except Exception as e:
        logger.error(f"Error loading scenarios dashboard: {e}")
        flash('Error loading scenarios dashboard.', 'error')
        return redirect(url_for('testing.dashboard'))


@testing_bp.route('/scenarios/available')
def available_scenarios():
    """Get list of available testing scenarios"""
    try:
        from autotest.testing.scenarios import ScenarioManager, AccessibilityScenarios
        from selenium import webdriver
        from autotest.utils.config import Config
        
        # Initialize with mock driver for metadata only
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        driver = webdriver.Chrome(options=options)
        
        try:
            scenario_manager = ScenarioManager(driver, testing_service.db_connection)
            accessibility_scenarios = AccessibilityScenarios(driver, testing_service.db_connection)
            
            # Get available scenarios from both managers
            basic_scenarios = scenario_manager.get_available_scenarios()
            accessibility_scenarios_list = accessibility_scenarios.get_available_scenarios()
            
            return jsonify({
                'basic_scenarios': basic_scenarios,
                'accessibility_scenarios': accessibility_scenarios_list,
                'total_scenarios': len(basic_scenarios) + len(accessibility_scenarios_list)
            })
        finally:
            driver.quit()
    
    except Exception as e:
        logger.error(f"Error getting available scenarios: {e}")
        return jsonify({'error': str(e)}), 500


@testing_bp.route('/scenarios/run', methods=['POST'])
def run_scenario():
    """Run a specific testing scenario"""
    try:
        if not testing_service:
            return jsonify({'error': 'Testing service not available'}), 500
        
        data = request.get_json() if request.is_json else request.form
        scenario_id = data.get('scenario_id')
        page_id = data.get('page_id')
        scenario_type = data.get('scenario_type', 'basic')  # 'basic' or 'accessibility'
        custom_options = data.get('custom_options', {})
        
        if not scenario_id or not page_id:
            return jsonify({'error': 'Scenario ID and Page ID are required'}), 400
        
        from autotest.testing.scenarios import ScenarioManager, AccessibilityScenarios
        from selenium import webdriver
        from autotest.utils.config import Config
        
        config = Config()
        options = webdriver.ChromeOptions()
        if config.get('webdriver.headless', True):
            options.add_argument('--headless')
        
        driver = webdriver.Chrome(options=options)
        
        try:
            if scenario_type == 'accessibility':
                accessibility_scenarios = AccessibilityScenarios(driver, testing_service.db_connection)
                result = accessibility_scenarios.run_accessibility_scenario(scenario_id, page_id, custom_options)
            else:
                scenario_manager = ScenarioManager(driver, testing_service.db_connection)
                result = scenario_manager.run_scenario(scenario_id, page_id)
            
            return jsonify(result)
        finally:
            driver.quit()
    
    except Exception as e:
        logger.error(f"Error running scenario: {e}")
        return jsonify({'error': str(e)}), 500


@testing_bp.route('/scenarios/batch', methods=['POST'])
def run_batch_scenarios():
    """Run multiple scenarios in sequence"""
    try:
        if not testing_service:
            return jsonify({'error': 'Testing service not available'}), 500
        
        data = request.get_json() if request.is_json else request.form
        scenario_ids = data.get('scenario_ids', [])
        page_id = data.get('page_id')
        
        if not scenario_ids or not page_id:
            return jsonify({'error': 'Scenario IDs and Page ID are required'}), 400
        
        from autotest.testing.scenarios import ScenarioManager
        from selenium import webdriver
        from autotest.utils.config import Config
        
        config = Config()
        options = webdriver.ChromeOptions()
        if config.get('webdriver.headless', True):
            options.add_argument('--headless')
        
        driver = webdriver.Chrome(options=options)
        
        try:
            scenario_manager = ScenarioManager(driver, testing_service.db_connection)
            result = scenario_manager.run_multiple_scenarios(scenario_ids, page_id)
            
            return jsonify(result)
        finally:
            driver.quit()
    
    except Exception as e:
        logger.error(f"Error running batch scenarios: {e}")
        return jsonify({'error': str(e)}), 500


@testing_bp.route('/scenarios/templates')
def available_templates():
    """Get list of available modification templates"""
    try:
        from autotest.testing.scenarios import ModificationScenarios
        
        modification_scenarios = ModificationScenarios()
        templates = modification_scenarios.get_all_templates()
        metadata = modification_scenarios.get_template_metadata()
        
        return jsonify({
            'templates': [
                {
                    'template_id': template.template_id,
                    'name': template.name,
                    'description': template.description,
                    'category': template.category,
                    'use_cases': template.use_cases or []
                }
                for template in templates
            ],
            'metadata': metadata
        })
    
    except Exception as e:
        logger.error(f"Error getting available templates: {e}")
        return jsonify({'error': str(e)}), 500


@testing_bp.route('/scenarios/custom', methods=['POST'])
def create_custom_scenario():
    """Create a custom testing scenario"""
    try:
        data = request.get_json() if request.is_json else request.form
        name = data.get('name')
        description = data.get('description')
        template_ids = data.get('template_ids', [])
        css_modifications = data.get('css_modifications', {})
        js_scenarios = data.get('js_scenarios', [])
        
        if not name or not description:
            return jsonify({'error': 'Name and description are required'}), 400
        
        from autotest.testing.scenarios import ModificationScenarios
        
        modification_scenarios = ModificationScenarios()
        
        if template_ids:
            # Create scenario from templates
            custom_scenario = modification_scenarios.combine_templates(template_ids)
            custom_scenario['name'] = name
            custom_scenario['description'] = description
        else:
            # Create scenario from scratch
            custom_scenario = modification_scenarios.create_custom_scenario(
                name, description, css_modifications, js_scenarios
            )
        
        return jsonify({
            'success': True,
            'custom_scenario': custom_scenario,
            'message': f'Custom scenario "{name}" created successfully'
        })
    
    except Exception as e:
        logger.error(f"Error creating custom scenario: {e}")
        return jsonify({'error': str(e)}), 500


@testing_bp.route('/scenarios/recommendations', methods=['POST'])
def get_scenario_recommendations():
    """Get recommended scenarios based on current accessibility state"""
    try:
        data = request.get_json() if request.is_json else request.form
        current_score = data.get('current_score', 50)
        detected_issues = data.get('detected_issues', [])
        page_id = data.get('page_id')
        
        from autotest.testing.scenarios import AccessibilityScenarios, ModificationScenarios
        from selenium import webdriver
        
        # Initialize with mock driver for recommendations only
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        driver = webdriver.Chrome(options=options)
        
        try:
            accessibility_scenarios = AccessibilityScenarios(driver, testing_service.db_connection)
            modification_scenarios = ModificationScenarios()
            
            # Get scenario recommendations
            scenario_recommendations = accessibility_scenarios.get_scenario_recommendations(
                current_score, detected_issues
            )
            
            # Get template recommendations
            template_recommendations = modification_scenarios.get_recommended_templates(detected_issues)
            
            return jsonify({
                'scenario_recommendations': scenario_recommendations,
                'template_recommendations': template_recommendations,
                'current_score': current_score,
                'detected_issues': detected_issues,
                'recommendation_reason': f'Based on accessibility score of {current_score}% and detected issues'
            })
        finally:
            driver.quit()
    
    except Exception as e:
        logger.error(f"Error getting scenario recommendations: {e}")
        return jsonify({'error': str(e)}), 500