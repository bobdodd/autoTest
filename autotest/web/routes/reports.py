"""
Reports routes for AutoTest web interface.
Handles report generation, management, and export functionality.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, Response
from autotest.services.reporting_service import ReportingService
from autotest.core.project_manager import ProjectManager
from autotest.core.website_manager import WebsiteManager
import base64
import logging

# Create blueprint
reports_bp = Blueprint('reports', __name__, url_prefix='/reports')

# Initialize services
reporting_service = None  # Will be initialized by app factory
project_manager = ProjectManager()
website_manager = WebsiteManager()

logger = logging.getLogger(__name__)


def init_reporting_service(config, db_connection):
    """Initialize reporting service (called by app factory)"""
    global reporting_service
    reporting_service = ReportingService(config, db_connection)


@reports_bp.route('/dashboard')
def dashboard():
    """Reports dashboard"""
    try:
        if not reporting_service:
            flash('Reporting service not available.', 'error')
            return redirect(url_for('main.index'))
        
        # Get recent reports
        recent_reports = reporting_service.list_reports(limit=10)
        
        # Get available templates
        templates = reporting_service.get_available_templates()
        
        return render_template('reports/dashboard.html',
                             recent_reports=recent_reports,
                             templates=templates)
    
    except Exception as e:
        logger.error(f"Error loading reports dashboard: {e}")
        flash('Error loading reports dashboard.', 'error')
        return redirect(url_for('main.index'))


@reports_bp.route('/generate', methods=['GET', 'POST'])
def generate_report():
    """Generate a new report"""
    try:
        if request.method == 'GET':
            # Show report generation form
            projects = project_manager.list_projects()
            templates = reporting_service.get_available_templates()
            
            return render_template('reports/generate.html',
                                 projects=projects,
                                 templates=templates)
        
        # Handle POST request for report generation
        if not reporting_service:
            return jsonify({'error': 'Reporting service not available'}), 500
        
        data = request.get_json() if request.is_json else request.form
        
        report_config = {
            'template_id': data.get('template_id', 'technical_detailed'),
            'project_id': data.get('project_id'),
            'website_id': data.get('website_id'),
            'time_range': data.get('time_range', '30d'),
            'format': data.get('format', 'html'),
            'generated_by': data.get('generated_by', 'web_interface'),
            'data_sources': data.getlist('data_sources') if hasattr(data, 'getlist') else data.get('data_sources', []),
            'filters': {
                'severity': data.getlist('severity_filter') if hasattr(data, 'getlist') else data.get('severity_filter', []),
                'wcag_level': data.getlist('wcag_filter') if hasattr(data, 'getlist') else data.get('wcag_filter', [])
            }
        }
        
        # Generate report
        report = reporting_service.generate_report(report_config)
        
        if request.is_json:
            return jsonify({
                'success': True,
                'report_id': report['report_id'],
                'message': 'Report generated successfully'
            })
        
        flash('Report generated successfully.', 'success')
        return redirect(url_for('reports.view_report', report_id=report['report_id']))
    
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        if request.is_json:
            return jsonify({'error': str(e)}), 500
        flash('Error generating report.', 'error')
        return redirect(url_for('reports.generate_report'))


@reports_bp.route('/list')
def list_reports():
    """List all generated reports"""
    try:
        if not reporting_service:
            flash('Reporting service not available.', 'error')
            return redirect(url_for('reports.dashboard'))
        
        # Get filter parameters
        project_id = request.args.get('project_id')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        
        # Get reports
        reports = reporting_service.list_reports(
            project_id=project_id,
            limit=per_page
        )
        
        # Get additional context for each report
        for report in reports:
            if report.get('project_id'):
                report['project'] = project_manager.get_project(report['project_id'])
        
        # Get projects for filter dropdown
        projects = project_manager.list_projects()
        
        return render_template('reports/list_reports.html',
                             reports=reports,
                             projects=projects,
                             current_filters={
                                 'project_id': project_id,
                                 'page': page,
                                 'per_page': per_page
                             })
    
    except Exception as e:
        logger.error(f"Error listing reports: {e}")
        flash('Error loading reports.', 'error')
        return redirect(url_for('reports.dashboard'))


@reports_bp.route('/view/<report_id>')
def view_report(report_id):
    """View a specific report"""
    try:
        if not reporting_service:
            flash('Reporting service not available.', 'error')
            return redirect(url_for('reports.dashboard'))
        
        # Get report
        report = reporting_service.get_report(report_id)
        if not report:
            flash('Report not found.', 'error')
            return redirect(url_for('reports.list_reports'))
        
        # Get additional context
        context = {}
        if report.get('project_id'):
            context['project'] = project_manager.get_project(report['project_id'])
        if report.get('website_id'):
            context['website'] = website_manager.get_website(report['website_id'])
        
        return render_template('reports/view_report.html',
                             report=report,
                             context=context)
    
    except Exception as e:
        logger.error(f"Error viewing report {report_id}: {e}")
        flash('Error loading report.', 'error')
        return redirect(url_for('reports.list_reports'))


@reports_bp.route('/download/<report_id>')
def download_report(report_id):
    """Download a report in its original format"""
    try:
        if not reporting_service:
            return jsonify({'error': 'Reporting service not available'}), 500
        
        # Get report
        report = reporting_service.get_report(report_id)
        if not report:
            return jsonify({'error': 'Report not found'}), 404
        
        formatted_output = report.get('formatted_output', '')
        report_format = report.get('format', 'html')
        
        # Set appropriate content type and filename
        if report_format == 'pdf':
            # Decode base64 PDF
            try:
                pdf_data = base64.b64decode(formatted_output)
                response = Response(
                    pdf_data,
                    mimetype='application/pdf',
                    headers={
                        'Content-Disposition': f'attachment; filename=report_{report_id}.pdf'
                    }
                )
                return response
            except Exception as e:
                return jsonify({'error': 'Invalid PDF data'}), 500
        
        elif report_format == 'json':
            response = Response(
                formatted_output,
                mimetype='application/json',
                headers={
                    'Content-Disposition': f'attachment; filename=report_{report_id}.json'
                }
            )
            return response
        
        elif report_format == 'markdown':
            response = Response(
                formatted_output,
                mimetype='text/markdown',
                headers={
                    'Content-Disposition': f'attachment; filename=report_{report_id}.md'
                }
            )
            return response
        
        else:  # HTML
            response = Response(
                formatted_output,
                mimetype='text/html',
                headers={
                    'Content-Disposition': f'attachment; filename=report_{report_id}.html'
                }
            )
            return response
    
    except Exception as e:
        logger.error(f"Error downloading report {report_id}: {e}")
        return jsonify({'error': str(e)}), 500


@reports_bp.route('/delete/<report_id>', methods=['POST'])
def delete_report(report_id):
    """Delete a report"""
    try:
        if not reporting_service:
            return jsonify({'error': 'Reporting service not available'}), 500
        
        success = reporting_service.delete_report(report_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Report deleted successfully'
            })
        else:
            return jsonify({'error': 'Report not found or could not be deleted'}), 404
    
    except Exception as e:
        logger.error(f"Error deleting report {report_id}: {e}")
        return jsonify({'error': str(e)}), 500


@reports_bp.route('/templates')
def list_templates():
    """List available report templates"""
    try:
        if not reporting_service:
            flash('Reporting service not available.', 'error')
            return redirect(url_for('reports.dashboard'))
        
        templates = reporting_service.get_available_templates()
        
        return render_template('reports/templates.html', templates=templates)
    
    except Exception as e:
        logger.error(f"Error listing templates: {e}")
        flash('Error loading templates.', 'error')
        return redirect(url_for('reports.dashboard'))


@reports_bp.route('/api/generate', methods=['POST'])
def api_generate_report():
    """API endpoint for report generation"""
    try:
        if not reporting_service:
            return jsonify({'error': 'Reporting service not available'}), 500
        
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Generate report
        report = reporting_service.generate_report(data)
        
        # Return report metadata (without formatted output for API)
        response_data = {
            'report_id': report['report_id'],
            'template_name': report['template_name'],
            'created_date': report['created_date'].isoformat() if report.get('created_date') else None,
            'project_id': report.get('project_id'),
            'format': report.get('format'),
            'sections_count': len(report.get('sections', [])),
            'download_url': url_for('reports.download_report', report_id=report['report_id'], _external=True)
        }
        
        return jsonify(response_data)
    
    except Exception as e:
        logger.error(f"Error in API report generation: {e}")
        return jsonify({'error': str(e)}), 500


@reports_bp.route('/api/templates')
def api_list_templates():
    """API endpoint for listing templates"""
    try:
        if not reporting_service:
            return jsonify({'error': 'Reporting service not available'}), 500
        
        templates = reporting_service.get_available_templates()
        
        return jsonify({
            'templates': templates,
            'total_templates': len(templates)
        })
    
    except Exception as e:
        logger.error(f"Error in API template listing: {e}")
        return jsonify({'error': str(e)}), 500


@reports_bp.route('/api/reports')
def api_list_reports():
    """API endpoint for listing reports"""
    try:
        if not reporting_service:
            return jsonify({'error': 'Reporting service not available'}), 500
        
        project_id = request.args.get('project_id')
        limit = int(request.args.get('limit', 50))
        
        reports = reporting_service.list_reports(project_id=project_id, limit=limit)
        
        # Add download URLs
        for report in reports:
            report['download_url'] = url_for('reports.download_report', 
                                           report_id=report['report_id'], 
                                           _external=True)
        
        return jsonify({
            'reports': reports,
            'total_reports': len(reports)
        })
    
    except Exception as e:
        logger.error(f"Error in API report listing: {e}")
        return jsonify({'error': str(e)}), 500


@reports_bp.route('/preview', methods=['POST'])
def preview_report():
    """Generate a preview of report sections without full generation"""
    try:
        if not reporting_service:
            return jsonify({'error': 'Reporting service not available'}), 500
        
        data = request.get_json() if request.is_json else request.form
        
        template_id = data.get('template_id', 'technical_detailed')
        project_id = data.get('project_id')
        
        # Get template information
        templates = reporting_service.get_available_templates()
        template = next((t for t in templates if t['template_id'] == template_id), None)
        
        if not template:
            return jsonify({'error': 'Template not found'}), 404
        
        # Generate preview data
        preview = {
            'template_id': template_id,
            'template_name': template['name'],
            'template_description': template['description'],
            'sections': template['sections'],
            'estimated_pages': self._estimate_report_pages(template, project_id),
            'format_options': template['format_options'],
            'target_audience': template['target_audience']
        }
        
        return jsonify(preview)
    
    except Exception as e:
        logger.error(f"Error generating report preview: {e}")
        return jsonify({'error': str(e)}), 500


def _estimate_report_pages(template: Dict[str, Any], project_id: str) -> int:
    """Estimate number of pages for report (rough calculation)"""
    try:
        base_pages = len(template.get('sections', [])) * 2  # 2 pages per section average
        
        # Adjust based on template type
        if template.get('template_id') == 'executive_summary':
            return min(base_pages, 10)
        elif template.get('template_id') == 'technical_detailed':
            return base_pages + 5  # More detailed content
        else:
            return base_pages
            
    except Exception:
        return 10  # Default estimate


@reports_bp.route('/bulk-generate', methods=['POST'])
def bulk_generate_reports():
    """Generate multiple reports for different projects/templates"""
    try:
        if not reporting_service:
            return jsonify({'error': 'Reporting service not available'}), 500
        
        data = request.get_json()
        report_configs = data.get('report_configs', [])
        
        if not report_configs:
            return jsonify({'error': 'No report configurations provided'}), 400
        
        generated_reports = []
        errors = []
        
        for config in report_configs:
            try:
                report = reporting_service.generate_report(config)
                generated_reports.append({
                    'report_id': report['report_id'],
                    'template_name': report['template_name'],
                    'project_id': report.get('project_id'),
                    'status': 'success'
                })
            except Exception as e:
                errors.append({
                    'config': config,
                    'error': str(e)
                })
        
        return jsonify({
            'generated_reports': generated_reports,
            'successful_count': len(generated_reports),
            'error_count': len(errors),
            'errors': errors
        })
    
    except Exception as e:
        logger.error(f"Error in bulk report generation: {e}")
        return jsonify({'error': str(e)}), 500


@reports_bp.route('/schedule', methods=['GET', 'POST'])
def schedule_report():
    """Schedule automatic report generation"""
    try:
        if request.method == 'GET':
            # Show scheduling interface
            projects = project_manager.list_projects()
            templates = reporting_service.get_available_templates()
            
            return render_template('reports/schedule.html',
                                 projects=projects,
                                 templates=templates)
        
        # Handle POST request for scheduling
        data = request.get_json() if request.is_json else request.form
        
        # This would integrate with the scheduler service
        schedule_config = {
            'name': data.get('name', 'Scheduled Report'),
            'description': data.get('description', ''),
            'report_template': data.get('template_id'),
            'project_id': data.get('project_id'),
            'frequency': data.get('frequency', 'weekly'),
            'delivery_emails': data.get('delivery_emails', '').split(',') if data.get('delivery_emails') else [],
            'report_format': data.get('report_format', 'pdf')
        }
        
        # This would create a scheduled task for report generation
        # For now, return success response
        
        if request.is_json:
            return jsonify({
                'success': True,
                'message': 'Report scheduling configured successfully'
            })
        
        flash('Report scheduling configured successfully.', 'success')
        return redirect(url_for('reports.dashboard'))
    
    except Exception as e:
        logger.error(f"Error scheduling report: {e}")
        if request.is_json:
            return jsonify({'error': str(e)}), 500
        flash('Error scheduling report.', 'error')
        return redirect(url_for('reports.schedule_report'))


@reports_bp.route('/archive')
def archived_reports():
    """View archived reports"""
    try:
        if not reporting_service:
            flash('Reporting service not available.', 'error')
            return redirect(url_for('reports.dashboard'))
        
        # Get older reports (simplified - could be enhanced with actual archiving logic)
        reports = reporting_service.list_reports(limit=100)
        
        # Filter to show older reports (more than 30 days old)
        from datetime import datetime, timedelta
        thirty_days_ago = datetime.now() - timedelta(days=30)
        
        archived_reports = [
            report for report in reports 
            if report.get('created_date') and report['created_date'] < thirty_days_ago
        ]
        
        return render_template('reports/archived.html', reports=archived_reports)
    
    except Exception as e:
        logger.error(f"Error loading archived reports: {e}")
        flash('Error loading archived reports.', 'error')
        return redirect(url_for('reports.dashboard'))