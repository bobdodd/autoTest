"""
History routes for AutoTest web interface.
Handles test result history, trending analysis, and historical comparisons.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from autotest.services.history_service import HistoryService
from autotest.core.project_manager import ProjectManager
from autotest.core.website_manager import WebsiteManager
from datetime import datetime, timedelta
import logging

# Create blueprint
history_bp = Blueprint('history', __name__, url_prefix='/history')

# Initialize services
history_service = None  # Will be initialized by app factory
project_manager = None  # ProjectManager()
website_manager = None  # WebsiteManager()

logger = logging.getLogger(__name__)


def init_history_service(config, db_connection):
    """Initialize history service (called by app factory)"""
    global history_service, project_manager, website_manager
    history_service = HistoryService(config, db_connection)
    project_manager = ProjectManager(db_connection)
    website_manager = WebsiteManager(db_connection)


@history_bp.route('/dashboard')
def dashboard():
    """History and trending dashboard"""
    try:
        # Get overall statistics (mock data for now)
        stats = {
            'total_snapshots': 0,
            'projects_tracked': 0,
            'avg_compliance_score': 0,
            'trend_direction': 'stable'
        }
        
        # Get recent snapshots for overview (mock data for now)
        recent_snapshots = []
        
        return render_template('history/dashboard.html',
                             stats=stats,
                             recent_snapshots=recent_snapshots)
    
    except Exception as e:
        logger.error(f"Error loading history dashboard: {e}")
        flash('Error loading history dashboard.', 'error')
        return redirect(url_for('main.index'))


@history_bp.route('/trending')
def trending_analysis():
    """Trending analysis interface"""
    try:
        if not history_service:
            flash('History service not available.', 'error')
            return redirect(url_for('history.dashboard'))
        
        # Get filter parameters
        project_id = request.args.get('project_id')
        website_id = request.args.get('website_id')
        time_range = request.args.get('time_range', '30d')
        
        # Generate trending analysis
        analysis = history_service.generate_trending_analysis(
            project_id=project_id,
            website_id=website_id,
            time_range=time_range
        )
        
        # Get projects for filter dropdown
        projects_result = project_manager.list_projects()
        projects = projects_result.get('projects', []) if projects_result.get('success') else []
        
        # Get websites for selected project
        websites = []
        if project_id:
            project = project_manager.get_project(project_id)
            if project and 'websites' in project:
                for website_data in project['websites']:
                    website = website_manager.get_website(website_data.get('website_id'))
                    if website:
                        websites.append(website)
        
        return render_template('history/trending.html',
                             analysis=analysis,
                             projects=projects,
                             websites=websites,
                             current_filters={
                                 'project_id': project_id,
                                 'website_id': website_id,
                                 'time_range': time_range
                             })
    
    except Exception as e:
        logger.error(f"Error loading trending analysis: {e}")
        flash('Error loading trending analysis.', 'error')
        return redirect(url_for('history.dashboard'))


@history_bp.route('/snapshots')
def list_snapshots():
    """List historical snapshots with filtering"""
    try:
        if not history_service:
            flash('History service not available.', 'error')
            return redirect(url_for('history.dashboard'))
        
        # Get filter parameters
        project_id = request.args.get('project_id')
        website_id = request.args.get('website_id')
        page_id = request.args.get('page_id')
        time_range = request.args.get('time_range', '30d')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        
        # Get snapshots
        snapshots = history_service.get_historical_snapshots(
            project_id=project_id,
            website_id=website_id,
            page_id=page_id,
            time_range=time_range,
            limit=per_page
        )
        
        # Get additional context for each snapshot
        for snapshot in snapshots:
            if snapshot.get('project_id'):
                snapshot['project'] = project_manager.get_project(snapshot['project_id'])
            if snapshot.get('website_id'):
                snapshot['website'] = website_manager.get_website(snapshot['website_id'])
        
        # Get projects for filter dropdown
        projects_result = project_manager.list_projects()
        projects = projects_result.get('projects', []) if projects_result.get('success') else []
        
        return render_template('history/snapshots.html',
                             snapshots=snapshots,
                             projects=projects,
                             current_filters={
                                 'project_id': project_id,
                                 'website_id': website_id,
                                 'page_id': page_id,
                                 'time_range': time_range,
                                 'page': page,
                                 'per_page': per_page
                             })
    
    except Exception as e:
        logger.error(f"Error listing snapshots: {e}")
        flash('Error loading snapshots.', 'error')
        return redirect(url_for('history.dashboard'))


@history_bp.route('/comparison')
def comparison_tool():
    """Historical comparison tool interface"""
    try:
        if not history_service:
            flash('History service not available.', 'error')
            return redirect(url_for('history.dashboard'))
        
        # Get projects for dropdown
        projects_result = project_manager.list_projects()
        projects = projects_result.get('projects', []) if projects_result.get('success') else []
        
        return render_template('history/comparison.html', projects=projects)
    
    except Exception as e:
        logger.error(f"Error loading comparison tool: {e}")
        flash('Error loading comparison tool.', 'error')
        return redirect(url_for('history.dashboard'))


@history_bp.route('/comparison/generate', methods=['POST'])
def generate_comparison():
    """Generate historical comparison report"""
    try:
        if not history_service:
            return jsonify({'error': 'History service not available'}), 500
        
        data = request.get_json() if request.is_json else request.form
        
        project_id = data.get('project_id')
        comparison_dates = data.get('comparison_dates', [])
        
        if not project_id:
            return jsonify({'error': 'Project ID is required'}), 400
        
        if len(comparison_dates) < 2:
            return jsonify({'error': 'At least 2 dates are required for comparison'}), 400
        
        # Generate comparison report
        comparison_report = history_service.get_comparison_report(
            project_id, comparison_dates
        )
        
        return jsonify(comparison_report)
    
    except Exception as e:
        logger.error(f"Error generating comparison: {e}")
        return jsonify({'error': str(e)}), 500


@history_bp.route('/snapshots/create', methods=['POST'])
def create_snapshot():
    """Create a manual snapshot of current test results"""
    try:
        if not history_service:
            return jsonify({'error': 'History service not available'}), 500
        
        data = request.get_json() if request.is_json else request.form
        
        # Get current test results for the project to populate snapshot
        project_id = data.get('project_id')
        if not project_id:
            return jsonify({'error': 'Project ID is required'}), 400
            
        # Calculate current metrics from test results
        from autotest.models.test_result import TestResultRepository
        test_result_repo = TestResultRepository(history_service.db_connection)
        
        # Get violation summary for the project
        summary = test_result_repo.get_violation_summary_by_project(project_id)
        
        # Calculate accessibility score (simplified)
        total_violations = summary.get('total_violations', 0)
        critical = summary.get('violations_by_impact', {}).get('critical', 0)
        serious = summary.get('violations_by_impact', {}).get('serious', 0) 
        moderate = summary.get('violations_by_impact', {}).get('moderate', 0)
        minor = summary.get('violations_by_impact', {}).get('minor', 0)
        
        # Simple scoring algorithm
        score_deductions = (critical * 10) + (serious * 5) + (moderate * 2) + (minor * 1)
        accessibility_score = max(0, 100 - score_deductions)
        
        # WCAG compliance rate (no critical/serious = higher compliance)
        wcag_compliance_rate = max(0, 100 - (critical * 5) - (serious * 2))
        
        snapshot_data = {
            'project_id': project_id,
            'website_id': data.get('website_id'),
            'page_id': data.get('page_id'),
            'accessibility_score': accessibility_score,
            'total_violations': total_violations,
            'critical_violations': critical,
            'serious_violations': serious,
            'moderate_violations': moderate,
            'minor_violations': minor,
            'pages_tested': summary.get('total_tests', 0),
            'wcag_compliance_rate': wcag_compliance_rate,
            'test_type': data.get('test_type', 'manual'),
            'metadata': {
                'created_by': data.get('created_by', 'manual'),
                'notes': data.get('notes', '')
            }
        }
        
        snapshot_id = history_service.create_snapshot(snapshot_data)
        
        return jsonify({
            'success': True,
            'snapshot_id': snapshot_id,
            'message': 'Snapshot created successfully'
        })
    
    except Exception as e:
        logger.error(f"Error creating snapshot: {e}")
        return jsonify({'error': str(e)}), 500


@history_bp.route('/api/trending/<project_id>')
def api_trending_data(project_id):
    """API endpoint for trending data"""
    try:
        if not history_service:
            return jsonify({'error': 'History service not available'}), 500
        
        time_range = request.args.get('time_range', '30d')
        website_id = request.args.get('website_id')
        
        analysis = history_service.generate_trending_analysis(
            project_id=project_id,
            website_id=website_id,
            time_range=time_range
        )
        
        return jsonify(analysis)
    
    except Exception as e:
        logger.error(f"Error getting trending data for {project_id}: {e}")
        return jsonify({'error': str(e)}), 500


@history_bp.route('/api/snapshots/<project_id>')
def api_project_snapshots(project_id):
    """API endpoint for project snapshots"""
    try:
        if not history_service:
            return jsonify({'error': 'History service not available'}), 500
        
        time_range = request.args.get('time_range', '30d')
        limit = int(request.args.get('limit', 50))
        
        snapshots = history_service.get_historical_snapshots(
            project_id=project_id,
            time_range=time_range,
            limit=limit
        )
        
        return jsonify({
            'project_id': project_id,
            'snapshots': snapshots,
            'total_snapshots': len(snapshots)
        })
    
    except Exception as e:
        logger.error(f"Error getting snapshots for {project_id}: {e}")
        return jsonify({'error': str(e)}), 500


@history_bp.route('/api/chart-data/<project_id>')
def api_chart_data(project_id):
    """API endpoint for chart data"""
    try:
        if not history_service:
            return jsonify({'error': 'History service not available'}), 500
        
        time_range = request.args.get('time_range', '30d')
        metric = request.args.get('metric', 'accessibility_score')
        
        snapshots = history_service.get_historical_snapshots(
            project_id=project_id,
            time_range=time_range,
            limit=100
        )
        
        # Format data for charts
        chart_data = []
        for snapshot in reversed(snapshots):  # Chronological order
            if snapshot.get(metric) is not None:
                chart_data.append({
                    'date': snapshot.get('snapshot_date'),
                    'value': snapshot.get(metric),
                    'snapshot_id': snapshot.get('snapshot_id')
                })
        
        return jsonify({
            'project_id': project_id,
            'metric': metric,
            'time_range': time_range,
            'data': chart_data
        })
    
    except Exception as e:
        logger.error(f"Error getting chart data for {project_id}: {e}")
        return jsonify({'error': str(e)}), 500


@history_bp.route('/api/stats')
def api_history_stats():
    """API endpoint for history statistics"""
    try:
        if not history_service:
            return jsonify({'error': 'History service not available'}), 500
        
        project_id = request.args.get('project_id')
        stats = history_service.get_history_statistics(project_id)
        
        return jsonify(stats)
    
    except Exception as e:
        logger.error(f"Error getting history stats: {e}")
        return jsonify({'error': str(e)}), 500


@history_bp.route('/export/<project_id>')
def export_history(project_id):
    """Export historical data"""
    try:
        if not history_service:
            return jsonify({'error': 'History service not available'}), 500
        
        export_format = request.args.get('format', 'json').lower()
        time_range = request.args.get('time_range', '30d')
        
        if export_format not in ['json', 'csv']:
            return jsonify({'error': 'Unsupported export format'}), 400
        
        # Get historical data
        snapshots = history_service.get_historical_snapshots(
            project_id=project_id,
            time_range=time_range,
            limit=1000
        )
        
        # Get trending analysis
        trending_analysis = history_service.generate_trending_analysis(
            project_id=project_id,
            time_range=time_range
        )
        
        export_data = {
            'export_date': datetime.now().isoformat(),
            'project_id': project_id,
            'time_range': time_range,
            'snapshots': snapshots,
            'trending_analysis': trending_analysis
        }
        
        if export_format == 'json':
            from flask import Response
            import json
            
            response = Response(
                json.dumps(export_data, indent=2, default=str),
                mimetype='application/json',
                headers={
                    'Content-Disposition': f'attachment; filename=history_{project_id}_{time_range}.json'
                }
            )
            return response
        
        elif export_format == 'csv':
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow([
                'snapshot_id', 'snapshot_date', 'accessibility_score',
                'total_violations', 'critical_violations', 'serious_violations',
                'moderate_violations', 'minor_violations', 'wcag_compliance_rate'
            ])
            
            # Write data
            for snapshot in snapshots:
                writer.writerow([
                    snapshot.get('snapshot_id', ''),
                    snapshot.get('snapshot_date', ''),
                    snapshot.get('accessibility_score', ''),
                    snapshot.get('total_violations', ''),
                    snapshot.get('critical_violations', ''),
                    snapshot.get('serious_violations', ''),
                    snapshot.get('moderate_violations', ''),
                    snapshot.get('minor_violations', ''),
                    snapshot.get('wcag_compliance_rate', '')
                ])
            
            from flask import Response
            response = Response(
                output.getvalue(),
                mimetype='text/csv',
                headers={
                    'Content-Disposition': f'attachment; filename=history_{project_id}_{time_range}.csv'
                }
            )
            return response
    
    except Exception as e:
        logger.error(f"Error exporting history for {project_id}: {e}")
        return jsonify({'error': str(e)}), 500


@history_bp.route('/reports')
def history_reports():
    """Historical reports interface"""
    try:
        if not history_service:
            flash('History service not available.', 'error')
            return redirect(url_for('history.dashboard'))
        
        # Get projects for report generation
        projects_result = project_manager.list_projects()
        projects = projects_result.get('projects', []) if projects_result.get('success') else []
        
        return render_template('history/reports.html', projects=projects)
    
    except Exception as e:
        logger.error(f"Error loading history reports: {e}")
        flash('Error loading history reports.', 'error')
        return redirect(url_for('history.dashboard'))


@history_bp.route('/reports/generate', methods=['POST'])
def generate_history_report():
    """Generate comprehensive history report"""
    try:
        if not history_service:
            return jsonify({'error': 'History service not available'}), 500
        
        data = request.get_json() if request.is_json else request.form
        
        project_id = data.get('project_id')
        report_type = data.get('report_type', 'summary')
        time_range = data.get('time_range', '30d')
        include_trending = data.get('include_trending', True)
        include_comparisons = data.get('include_comparisons', False)
        
        if not project_id:
            return jsonify({'error': 'Project ID is required'}), 400
        
        # Generate comprehensive report
        report = {
            'report_date': datetime.now().isoformat(),
            'project_id': project_id,
            'report_type': report_type,
            'time_range': time_range
        }
        
        # Get basic statistics
        report['statistics'] = history_service.get_history_statistics(project_id)
        
        # Get historical snapshots
        report['snapshots'] = history_service.get_historical_snapshots(
            project_id=project_id,
            time_range=time_range,
            limit=100
        )
        
        # Include trending analysis if requested
        if include_trending:
            report['trending_analysis'] = history_service.generate_trending_analysis(
                project_id=project_id,
                time_range=time_range
            )
        
        # Include comparisons if requested
        if include_comparisons and len(report['snapshots']) >= 2:
            # Compare first and last snapshots
            comparison_dates = [
                report['snapshots'][-1].get('snapshot_date'),  # Oldest
                report['snapshots'][0].get('snapshot_date')    # Newest
            ]
            
            report['comparison'] = history_service.get_comparison_report(
                project_id, [d.isoformat() if hasattr(d, 'isoformat') else str(d) for d in comparison_dates]
            )
        
        return jsonify(report)
    
    except Exception as e:
        logger.error(f"Error generating history report: {e}")
        return jsonify({'error': str(e)}), 500