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
project_manager = ProjectManager()
website_manager = WebsiteManager()

logger = logging.getLogger(__name__)


def init_testing_service(config, db_connection):
    """Initialize testing service (called by app factory)"""
    global testing_service
    testing_service = TestingService(config, db_connection)


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