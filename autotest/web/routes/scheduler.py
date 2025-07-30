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
Scheduler routes for AutoTest web interface.
Handles scheduled testing management and configuration.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from autotest.services.scheduler_service import SchedulerService
from autotest.core.project_manager import ProjectManager
from autotest.core.website_manager import WebsiteManager
import logging

# Create blueprint
scheduler_bp = Blueprint('scheduler', __name__, url_prefix='/scheduler')

# Initialize services
scheduler_service = None  # Will be initialized by app factory
project_manager = None  # ProjectManager()
website_manager = None  # WebsiteManager()

logger = logging.getLogger(__name__)


def init_scheduler_service(config, db_connection, testing_service):
    """Initialize scheduler service (called by app factory)"""
    global scheduler_service, project_manager, website_manager
    scheduler_service = SchedulerService(config, db_connection, testing_service)
    project_manager = ProjectManager(db_connection)
    website_manager = WebsiteManager(db_connection)


@scheduler_bp.route('/dashboard')
def dashboard():
    """Scheduler dashboard with statistics and active schedules"""
    try:
        # Get scheduler statistics (mock data for now)
        stats = {
            'total_schedules': 0,
            'active_schedules': 0,
            'paused_schedules': 0,
            'recent_executions_24h': 0
        }
        
        # Get active schedules (mock data for now)
        active_schedules = []
        
        # Get recent executions (mock data for now)
        recent_executions = []
        
        return render_template('scheduler/dashboard.html',
                             stats=stats,
                             active_schedules=active_schedules,
                             recent_executions=recent_executions)
    
    except Exception as e:
        logger.error(f"Error loading scheduler dashboard: {e}")
        flash('Error loading scheduler dashboard.', 'error')
        return redirect(url_for('main.index'))


@scheduler_bp.route('/schedules')
def list_schedules():
    """List all scheduled tests with filtering options"""
    try:
        if not scheduler_service:
            flash('Scheduler service not available.', 'error')
            return redirect(url_for('scheduler.dashboard'))
        
        # Get filter parameters
        project_id = request.args.get('project_id')
        status = request.args.get('status')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        
        # Calculate offset
        offset = (page - 1) * per_page
        
        # Get schedules
        schedules = scheduler_service.list_schedules(
            project_id=project_id,
            status=status,
            limit=per_page,
            offset=offset
        )
        
        # Get additional context for each schedule
        for schedule in schedules:
            if schedule.get('project_id'):
                schedule['project'] = project_manager.get_project(schedule['project_id'])
            if schedule.get('website_id'):
                schedule['website'] = website_manager.get_website(schedule['website_id'])
        
        # Get all projects for filter dropdown
        projects_result = project_manager.list_projects()
        projects = projects_result.get('projects', []) if projects_result.get('success') else []
        
        return render_template('scheduler/list_schedules.html',
                             schedules=schedules,
                             projects=projects,
                             current_filters={
                                 'project_id': project_id,
                                 'status': status,
                                 'page': page,
                                 'per_page': per_page
                             })
    
    except Exception as e:
        logger.error(f"Error listing schedules: {e}")
        flash('Error loading schedules.', 'error')
        return redirect(url_for('scheduler.dashboard'))


@scheduler_bp.route('/schedules/create', methods=['GET', 'POST'])
def create_schedule():
    """Create a new scheduled test"""
    try:
        if request.method == 'GET':
            # Show create schedule form
            projects_result = project_manager.list_projects()
            projects = projects_result.get('projects', []) if projects_result.get('success') else []
            return render_template('scheduler/create_schedule.html', projects=projects)
        
        # Handle POST request
        if not scheduler_service:
            return jsonify({'error': 'Scheduler service not available'}), 500
        
        # Get form data
        data = request.get_json() if request.is_json else request.form
        
        schedule_data = {
            'name': data.get('name'),
            'description': data.get('description', ''),
            'project_id': data.get('project_id'),
            'website_id': data.get('website_id'),
            'page_ids': data.getlist('page_ids') if hasattr(data, 'getlist') else data.get('page_ids', []),
            'test_type': data.get('test_type', 'accessibility'),
            'frequency': data.get('frequency', 'weekly'),
            'custom_interval_hours': int(data.get('custom_interval_hours', 0)) if data.get('custom_interval_hours') else None,
            'start_date': data.get('start_date'),
            'end_date': data.get('end_date'),
            'notification_emails': data.get('notification_emails', '').split(',') if data.get('notification_emails') else [],
            'test_config': {
                'scenario_ids': data.getlist('scenario_ids') if hasattr(data, 'getlist') else data.get('scenario_ids', [])
            },
            'created_by': data.get('created_by', 'system')
        }
        
        # Validate required fields
        if not schedule_data['name']:
            if request.is_json:
                return jsonify({'error': 'Schedule name is required'}), 400
            flash('Schedule name is required.', 'error')
            return redirect(url_for('scheduler.create_schedule'))
        
        # Create schedule
        schedule_id = scheduler_service.create_schedule(schedule_data)
        
        if request.is_json:
            return jsonify({
                'success': True,
                'schedule_id': schedule_id,
                'message': 'Schedule created successfully'
            })
        
        flash(f'Schedule "{schedule_data["name"]}" created successfully.', 'success')
        return redirect(url_for('scheduler.view_schedule', schedule_id=schedule_id))
    
    except Exception as e:
        logger.error(f"Error creating schedule: {e}")
        if request.is_json:
            return jsonify({'error': str(e)}), 500
        flash('Error creating schedule.', 'error')
        return redirect(url_for('scheduler.create_schedule'))


@scheduler_bp.route('/schedules/<schedule_id>')
def view_schedule(schedule_id):
    """View detailed schedule information"""
    try:
        if not scheduler_service:
            flash('Scheduler service not available.', 'error')
            return redirect(url_for('scheduler.dashboard'))
        
        # Get schedule details
        schedule = scheduler_service.get_schedule(schedule_id)
        if not schedule:
            flash('Schedule not found.', 'error')
            return redirect(url_for('scheduler.list_schedules'))
        
        # Get execution history
        execution_history = scheduler_service.get_schedule_execution_history(schedule_id)
        
        # Get additional context
        context = {}
        if schedule.get('project_id'):
            context['project'] = project_manager.get_project(schedule['project_id'])
        if schedule.get('website_id'):
            context['website'] = website_manager.get_website(schedule['website_id'])
        
        return render_template('scheduler/view_schedule.html',
                             schedule=schedule,
                             execution_history=execution_history,
                             context=context)
    
    except Exception as e:
        logger.error(f"Error viewing schedule {schedule_id}: {e}")
        flash('Error loading schedule details.', 'error')
        return redirect(url_for('scheduler.list_schedules'))


@scheduler_bp.route('/schedules/<schedule_id>/edit', methods=['GET', 'POST'])
def edit_schedule(schedule_id):
    """Edit an existing schedule"""
    try:
        if not scheduler_service:
            flash('Scheduler service not available.', 'error')
            return redirect(url_for('scheduler.dashboard'))
        
        schedule = scheduler_service.get_schedule(schedule_id)
        if not schedule:
            flash('Schedule not found.', 'error')
            return redirect(url_for('scheduler.list_schedules'))
        
        if request.method == 'GET':
            # Show edit form
            projects_result = project_manager.list_projects()
            projects = projects_result.get('projects', []) if projects_result.get('success') else []
            return render_template('scheduler/edit_schedule.html',
                                 schedule=schedule,
                                 projects=projects)
        
        # Handle POST request
        data = request.get_json() if request.is_json else request.form
        
        update_data = {}
        
        # Update fields that are provided
        for field in ['name', 'description', 'frequency', 'custom_interval_hours',
                     'start_date', 'end_date', 'status']:
            if field in data and data[field] is not None:
                if field == 'custom_interval_hours' and data[field]:
                    update_data[field] = int(data[field])
                else:
                    update_data[field] = data[field]
        
        if 'notification_emails' in data:
            update_data['notification_emails'] = data.get('notification_emails', '').split(',') if data.get('notification_emails') else []
        
        # Update schedule
        success = scheduler_service.update_schedule(schedule_id, update_data)
        
        if success:
            if request.is_json:
                return jsonify({
                    'success': True,
                    'message': 'Schedule updated successfully'
                })
            flash('Schedule updated successfully.', 'success')
            return redirect(url_for('scheduler.view_schedule', schedule_id=schedule_id))
        else:
            if request.is_json:
                return jsonify({'error': 'Failed to update schedule'}), 500
            flash('Failed to update schedule.', 'error')
            return redirect(url_for('scheduler.edit_schedule', schedule_id=schedule_id))
    
    except Exception as e:
        logger.error(f"Error editing schedule {schedule_id}: {e}")
        if request.is_json:
            return jsonify({'error': str(e)}), 500
        flash('Error updating schedule.', 'error')
        return redirect(url_for('scheduler.edit_schedule', schedule_id=schedule_id))


@scheduler_bp.route('/schedules/<schedule_id>/delete', methods=['POST'])
def delete_schedule(schedule_id):
    """Delete a schedule"""
    try:
        if not scheduler_service:
            return jsonify({'error': 'Scheduler service not available'}), 500
        
        success = scheduler_service.delete_schedule(schedule_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Schedule deleted successfully'
            })
        else:
            return jsonify({'error': 'Failed to delete schedule'}), 500
    
    except Exception as e:
        logger.error(f"Error deleting schedule {schedule_id}: {e}")
        return jsonify({'error': str(e)}), 500


@scheduler_bp.route('/schedules/<schedule_id>/pause', methods=['POST'])
def pause_schedule(schedule_id):
    """Pause a schedule"""
    try:
        if not scheduler_service:
            return jsonify({'error': 'Scheduler service not available'}), 500
        
        success = scheduler_service.pause_schedule(schedule_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Schedule paused successfully'
            })
        else:
            return jsonify({'error': 'Failed to pause schedule'}), 500
    
    except Exception as e:
        logger.error(f"Error pausing schedule {schedule_id}: {e}")
        return jsonify({'error': str(e)}), 500


@scheduler_bp.route('/schedules/<schedule_id>/resume', methods=['POST'])
def resume_schedule(schedule_id):
    """Resume a paused schedule"""
    try:
        if not scheduler_service:
            return jsonify({'error': 'Scheduler service not available'}), 500
        
        success = scheduler_service.resume_schedule(schedule_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Schedule resumed successfully'
            })
        else:
            return jsonify({'error': 'Failed to resume schedule'}), 500
    
    except Exception as e:
        logger.error(f"Error resuming schedule {schedule_id}: {e}")
        return jsonify({'error': str(e)}), 500


@scheduler_bp.route('/schedules/<schedule_id>/execute', methods=['POST'])
def execute_schedule_now(schedule_id):
    """Execute a schedule immediately (manual trigger)"""
    try:
        if not scheduler_service:
            return jsonify({'error': 'Scheduler service not available'}), 500
        
        # Get schedule
        schedule = scheduler_service.get_schedule(schedule_id)
        if not schedule:
            return jsonify({'error': 'Schedule not found'}), 404
        
        # Execute the schedule manually
        # This would trigger the execution logic
        execution_result = scheduler_service._execute_scheduled_test(schedule)
        
        # Store the result
        scheduler_service._store_execution_result(schedule_id, execution_result)
        
        return jsonify({
            'success': True,
            'execution_result': execution_result,
            'message': 'Schedule executed successfully'
        })
    
    except Exception as e:
        logger.error(f"Error executing schedule {schedule_id}: {e}")
        return jsonify({'error': str(e)}), 500


@scheduler_bp.route('/api/stats')
def api_scheduler_stats():
    """API endpoint for scheduler statistics"""
    try:
        if not scheduler_service:
            return jsonify({'error': 'Scheduler service not available'}), 500
        
        stats = scheduler_service.get_scheduler_statistics()
        
        return jsonify(stats)
    
    except Exception as e:
        logger.error(f"Error getting scheduler stats: {e}")
        return jsonify({'error': str(e)}), 500


@scheduler_bp.route('/api/schedules/<schedule_id>/history')
def api_schedule_history(schedule_id):
    """API endpoint for schedule execution history"""
    try:
        if not scheduler_service:
            return jsonify({'error': 'Scheduler service not available'}), 500
        
        limit = int(request.args.get('limit', 20))
        
        history = scheduler_service.get_schedule_execution_history(schedule_id, limit)
        
        return jsonify({
            'schedule_id': schedule_id,
            'execution_history': history,
            'total_executions': len(history)
        })
    
    except Exception as e:
        logger.error(f"Error getting schedule history {schedule_id}: {e}")
        return jsonify({'error': str(e)}), 500


@scheduler_bp.route('/control/start', methods=['POST'])
def start_scheduler():
    """Start the scheduler service"""
    try:
        if not scheduler_service:
            return jsonify({'error': 'Scheduler service not available'}), 500
        
        scheduler_service.start_scheduler()
        
        return jsonify({
            'success': True,
            'message': 'Scheduler started successfully'
        })
    
    except Exception as e:
        logger.error(f"Error starting scheduler: {e}")
        return jsonify({'error': str(e)}), 500


@scheduler_bp.route('/control/stop', methods=['POST'])
def stop_scheduler():
    """Stop the scheduler service"""
    try:
        if not scheduler_service:
            return jsonify({'error': 'Scheduler service not available'}), 500
        
        scheduler_service.stop_scheduler()
        
        return jsonify({
            'success': True,
            'message': 'Scheduler stopped successfully'
        })
    
    except Exception as e:
        logger.error(f"Error stopping scheduler: {e}")
        return jsonify({'error': str(e)}), 500


@scheduler_bp.route('/templates')
def schedule_templates():
    """Show predefined schedule templates"""
    try:
        # Predefined schedule templates for common use cases
        templates = [
            {
                'id': 'daily_accessibility',
                'name': 'Daily Accessibility Check',
                'description': 'Run accessibility tests daily for critical pages',
                'frequency': 'daily',
                'test_type': 'accessibility',
                'recommended_for': 'Production websites with frequent updates'
            },
            {
                'id': 'weekly_full_site',
                'name': 'Weekly Full Site Audit',
                'description': 'Comprehensive accessibility audit of entire website',
                'frequency': 'weekly',
                'test_type': 'accessibility',
                'recommended_for': 'Regular maintenance and compliance monitoring'
            },
            {
                'id': 'monthly_css_review',
                'name': 'Monthly CSS Accessibility Review',
                'description': 'Review CSS modifications and accessibility improvements',
                'frequency': 'monthly',
                'test_type': 'css',
                'recommended_for': 'Design system maintenance'
            },
            {
                'id': 'weekly_scenarios',
                'name': 'Weekly Scenario Testing',
                'description': 'Run predefined accessibility scenarios weekly',
                'frequency': 'weekly',
                'test_type': 'scenarios',
                'recommended_for': 'Comprehensive accessibility validation'
            }
        ]
        
        return render_template('scheduler/templates.html', templates=templates)
    
    except Exception as e:
        logger.error(f"Error loading schedule templates: {e}")
        flash('Error loading schedule templates.', 'error')
        return redirect(url_for('scheduler.dashboard'))


@scheduler_bp.route('/templates/<template_id>/create', methods=['POST'])
def create_from_template(template_id):
    """Create a schedule from a predefined template"""
    try:
        if not scheduler_service:
            return jsonify({'error': 'Scheduler service not available'}), 500
        
        data = request.get_json() if request.is_json else request.form
        
        # Template configurations
        template_configs = {
            'daily_accessibility': {
                'name': f"Daily Accessibility Check - {data.get('name', 'Untitled')}",
                'description': 'Automated daily accessibility testing for critical pages',
                'frequency': 'daily',
                'test_type': 'accessibility'
            },
            'weekly_full_site': {
                'name': f"Weekly Full Site Audit - {data.get('name', 'Untitled')}",
                'description': 'Comprehensive weekly accessibility audit',
                'frequency': 'weekly',
                'test_type': 'accessibility'
            },
            'monthly_css_review': {
                'name': f"Monthly CSS Review - {data.get('name', 'Untitled')}",
                'description': 'Monthly CSS accessibility review and optimization',
                'frequency': 'monthly',
                'test_type': 'css'
            },
            'weekly_scenarios': {
                'name': f"Weekly Scenarios - {data.get('name', 'Untitled')}",
                'description': 'Weekly accessibility scenario testing',
                'frequency': 'weekly',
                'test_type': 'scenarios',
                'test_config': {
                    'scenario_ids': ['basic_compliance', 'enhanced_ux']
                }
            }
        }
        
        template_config = template_configs.get(template_id)
        if not template_config:
            return jsonify({'error': 'Template not found'}), 404
        
        # Merge template config with user data
        schedule_data = {
            **template_config,
            'project_id': data.get('project_id'),
            'website_id': data.get('website_id'),
            'page_ids': data.get('page_ids', []),
            'start_date': data.get('start_date'),
            'end_date': data.get('end_date'),
            'notification_emails': data.get('notification_emails', '').split(',') if data.get('notification_emails') else [],
            'created_by': data.get('created_by', 'system')
        }
        
        # Create schedule
        schedule_id = scheduler_service.create_schedule(schedule_data)
        
        return jsonify({
            'success': True,
            'schedule_id': schedule_id,
            'message': f'Schedule created from template: {template_id}'
        })
    
    except Exception as e:
        logger.error(f"Error creating schedule from template {template_id}: {e}")
        return jsonify({'error': str(e)}), 500