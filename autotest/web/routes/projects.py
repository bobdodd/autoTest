"""
Project management routes for AutoTest web application
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from typing import Dict, Any

from autotest.utils.logger import get_logger

projects_bp = Blueprint('projects', __name__)
logger = get_logger(__name__)


@projects_bp.route('/')
def list_projects():
    """
    Display list of all projects
    """
    try:
        project_manager = current_app.config['PROJECT_MANAGER']
        
        projects_result = project_manager.list_projects()
        
        if projects_result['success']:
            projects = projects_result['projects']
        else:
            projects = []
            flash(f"Error loading projects: {projects_result.get('error')}", 'error')
        
        return render_template('projects/list.html', projects=projects)
        
    except Exception as e:
        logger.error(f"Error listing projects: {e}")
        flash("An error occurred while loading projects", 'error')
        return render_template('projects/list.html', projects=[])


@projects_bp.route('/new', methods=['GET', 'POST'])
def create_project():
    """
    Create a new project
    """
    if request.method == 'GET':
        return render_template('projects/create.html')
    
    try:
        project_manager = current_app.config['PROJECT_MANAGER']
        
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        
        # Validation
        if not name:
            flash("Project name is required", 'error')
            return render_template('projects/create.html', 
                                 form_data={'name': name, 'description': description})
        
        if len(name) > 100:
            flash("Project name must be 100 characters or less", 'error')
            return render_template('projects/create.html',
                                 form_data={'name': name, 'description': description})
        
        # Create project
        result = project_manager.create_project(name, description)
        
        if result['success']:
            flash(f"Project '{name}' created successfully", 'success')
            return redirect(url_for('projects.view_project', project_id=result['project_id']))
        else:
            flash(f"Error creating project: {result.get('error')}", 'error')
            return render_template('projects/create.html',
                                 form_data={'name': name, 'description': description})
        
    except Exception as e:
        logger.error(f"Error creating project: {e}")
        flash("An error occurred while creating the project", 'error')
        return render_template('projects/create.html')


@projects_bp.route('/<project_id>')
def view_project(project_id: str):
    """
    View project details and websites
    """
    try:
        project_manager = current_app.config['PROJECT_MANAGER']
        
        # Get project details
        project_result = project_manager.get_project(project_id)
        
        if not project_result['success']:
            flash(f"Project not found: {project_result.get('error')}", 'error')
            return redirect(url_for('projects.list_projects'))
        
        project = project_result['project']
        
        # Get project statistics
        stats_result = project_manager.get_project_statistics(project_id)
        
        if stats_result['success']:
            statistics = stats_result['statistics']
        else:
            statistics = {
                'total_websites': 0,
                'total_pages': 0,
                'untested_pages': 0,
                'total_violations': 0,
                'total_tests': 0
            }
            logger.warning(f"Failed to load project statistics: {stats_result.get('error')}")
        
        return render_template('projects/detail.html', 
                             project=project, 
                             statistics=statistics)
        
    except Exception as e:
        logger.error(f"Error viewing project {project_id}: {e}")
        flash("An error occurred while loading the project", 'error')
        return redirect(url_for('projects.list_projects'))


@projects_bp.route('/<project_id>/edit', methods=['GET', 'POST'])
def edit_project(project_id: str):
    """
    Edit project details
    """
    try:
        project_manager = current_app.config['PROJECT_MANAGER']
        
        if request.method == 'GET':
            # Get current project data
            project_result = project_manager.get_project(project_id)
            
            if not project_result['success']:
                flash(f"Project not found: {project_result.get('error')}", 'error')
                return redirect(url_for('projects.list_projects'))
            
            project = project_result['project']
            return render_template('projects/edit.html', project=project)
        
        # POST request - update project
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        
        # Validation
        if not name:
            flash("Project name is required", 'error')
            return redirect(url_for('projects.edit_project', project_id=project_id))
        
        if len(name) > 100:
            flash("Project name must be 100 characters or less", 'error')
            return redirect(url_for('projects.edit_project', project_id=project_id))
        
        # Update project
        result = project_manager.update_project(project_id, name, description)
        
        if result['success']:
            flash("Project updated successfully", 'success')
            return redirect(url_for('projects.view_project', project_id=project_id))
        else:
            flash(f"Error updating project: {result.get('error')}", 'error')
            return redirect(url_for('projects.edit_project', project_id=project_id))
        
    except Exception as e:
        logger.error(f"Error editing project {project_id}: {e}")
        flash("An error occurred while updating the project", 'error')
        return redirect(url_for('projects.view_project', project_id=project_id))


@projects_bp.route('/<project_id>/delete', methods=['POST'])
def delete_project(project_id: str):
    """
    Delete a project
    """
    try:
        project_manager = current_app.config['PROJECT_MANAGER']
        
        # Confirm deletion
        confirm = request.form.get('confirm', '').lower()
        if confirm != 'delete':
            flash("Please type 'delete' to confirm project deletion", 'error')
            return redirect(url_for('projects.view_project', project_id=project_id))
        
        # Delete project
        result = project_manager.delete_project(project_id)
        
        if result['success']:
            flash(f"Project deleted successfully. {result.get('deleted_pages', 0)} pages and {result.get('deleted_results', 0)} test results were also removed.", 'success')
            return redirect(url_for('projects.list_projects'))
        else:
            flash(f"Error deleting project: {result.get('error')}", 'error')
            return redirect(url_for('projects.view_project', project_id=project_id))
        
    except Exception as e:
        logger.error(f"Error deleting project {project_id}: {e}")
        flash("An error occurred while deleting the project", 'error')
        return redirect(url_for('projects.view_project', project_id=project_id))


@projects_bp.route('/<project_id>/add-website', methods=['GET', 'POST'])
def add_website(project_id: str):
    """
    Add a website to a project
    """
    try:
        project_manager = current_app.config['PROJECT_MANAGER']
        
        if request.method == 'GET':
            # Get project info for breadcrumb
            project_result = project_manager.get_project(project_id)
            
            if not project_result['success']:
                flash(f"Project not found: {project_result.get('error')}", 'error')
                return redirect(url_for('projects.list_projects'))
            
            project = project_result['project']
            return render_template('projects/add_website.html', project=project)
        
        # POST request - add website
        name = request.form.get('name', '').strip()
        url = request.form.get('url', '').strip()
        
        # Validation
        if not url:
            flash("Website URL is required", 'error')
            return redirect(url_for('projects.add_website', project_id=project_id))
        
        if not name:
            # Use domain as default name
            from urllib.parse import urlparse
            parsed_url = urlparse(url)
            name = parsed_url.netloc or url
        
        # Add website
        result = project_manager.add_website_to_project(project_id, name, url)
        
        if result['success']:
            flash(f"Website '{name}' added successfully", 'success')
            return redirect(url_for('projects.view_project', project_id=project_id))
        else:
            flash(f"Error adding website: {result.get('error')}", 'error')
            return redirect(url_for('projects.add_website', project_id=project_id))
        
    except Exception as e:
        logger.error(f"Error adding website to project {project_id}: {e}")
        flash("An error occurred while adding the website", 'error')
        return redirect(url_for('projects.view_project', project_id=project_id))


@projects_bp.route('/<project_id>/remove-website/<website_id>', methods=['POST'])
def remove_website(project_id: str, website_id: str):
    """
    Remove a website from a project
    """
    try:
        project_manager = current_app.config['PROJECT_MANAGER']
        
        # Remove website
        result = project_manager.remove_website_from_project(project_id, website_id)
        
        if result['success']:
            flash(f"Website removed successfully. {result.get('deleted_pages', 0)} pages and {result.get('deleted_results', 0)} test results were also removed.", 'success')
        else:
            flash(f"Error removing website: {result.get('error')}", 'error')
        
        return redirect(url_for('projects.view_project', project_id=project_id))
        
    except Exception as e:
        logger.error(f"Error removing website {website_id} from project {project_id}: {e}")
        flash("An error occurred while removing the website", 'error')
        return redirect(url_for('projects.view_project', project_id=project_id))