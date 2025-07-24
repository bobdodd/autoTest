"""
Website management routes for AutoTest web interface.
Handles website creation, editing, viewing, and deletion within projects.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from autotest.core.project_manager import ProjectManager
from autotest.core.website_manager import WebsiteManager
from autotest.core.scraper import WebScraper
import logging

# Create blueprint
websites_bp = Blueprint('websites', __name__, url_prefix='/projects/<project_id>/websites')

# Initialize managers
project_manager = ProjectManager()
website_manager = WebsiteManager()
scraper = WebScraper()

logger = logging.getLogger(__name__)


@websites_bp.route('/')
def list_websites(project_id):
    """Display list of websites for a project."""
    try:
        project = project_manager.get_project(project_id)
        if not project:
            flash('Project not found.', 'error')
            return redirect(url_for('projects.list_projects'))
        
        # Get websites with additional metadata
        websites = []
        for website_data in project.get('websites', []):
            website = website_manager.get_website(website_data['website_id'])
            if website:
                # Add page count and last scan info
                website['page_count'] = len(website.get('pages', []))
                websites.append(website)
        
        return render_template('websites/list.html', 
                             project=project, 
                             websites=websites)
    
    except Exception as e:
        logger.error(f"Error listing websites for project {project_id}: {e}")
        flash('Error loading websites.', 'error')
        return redirect(url_for('projects.view_project', project_id=project_id))


@websites_bp.route('/add', methods=['GET', 'POST'])
def add_website(project_id):
    """Add a new website to the project."""
    try:
        project = project_manager.get_project(project_id)
        if not project:
            flash('Project not found.', 'error')
            return redirect(url_for('projects.list_projects'))
        
        if request.method == 'POST':
            # Get form data
            name = request.form.get('name', '').strip()
            base_url = request.form.get('base_url', '').strip()
            description = request.form.get('description', '').strip()
            
            # Scraping configuration
            max_depth = int(request.form.get('max_depth', 3))
            max_pages = int(request.form.get('max_pages', 100))
            respect_robots = request.form.get('respect_robots') == 'on'
            follow_external = request.form.get('follow_external') == 'on'
            
            # Validation
            errors = []
            if not name:
                errors.append('Website name is required.')
            if not base_url:
                errors.append('Base URL is required.')
            elif not base_url.startswith(('http://', 'https://')):
                errors.append('Base URL must start with http:// or https://')
            
            if max_depth < 1 or max_depth > 10:
                errors.append('Max depth must be between 1 and 10.')
            if max_pages < 1 or max_pages > 10000:
                errors.append('Max pages must be between 1 and 10,000.')
            
            if errors:
                for error in errors:
                    flash(error, 'error')
                return render_template('websites/add.html', 
                                     project=project,
                                     form_data=request.form)
            
            # Create website
            website_data = {
                'name': name,
                'base_url': base_url,
                'description': description,
                'scraping_config': {
                    'max_depth': max_depth,
                    'max_pages': max_pages,
                    'respect_robots_txt': respect_robots,
                    'follow_external_links': follow_external,
                }
            }
            
            website_id = website_manager.create_website(project_id, website_data)
            if website_id:
                flash(f'Website "{name}" added successfully.', 'success')
                return redirect(url_for('websites.view_website', 
                                      project_id=project_id, 
                                      website_id=website_id))
            else:
                flash('Error creating website.', 'error')
        
        return render_template('websites/add.html', project=project)
    
    except Exception as e:
        logger.error(f"Error adding website to project {project_id}: {e}")
        flash('Error adding website.', 'error')
        return redirect(url_for('projects.view_project', project_id=project_id))


@websites_bp.route('/<website_id>')
def view_website(project_id, website_id):
    """View website details and pages."""
    try:
        project = project_manager.get_project(project_id)
        website = website_manager.get_website(website_id)
        
        if not project or not website:
            flash('Website not found.', 'error')
            return redirect(url_for('projects.view_project', project_id=project_id))
        
        # Get pages for this website
        pages = website.get('pages', [])
        
        # Get recent test results
        recent_tests = []  # TODO: Implement test results retrieval
        
        # Calculate statistics
        stats = {
            'total_pages': len(pages),
            'scanned_pages': len([p for p in pages if p.get('last_scan_date')]),
            'tested_pages': len([p for p in pages if p.get('last_test_date')]),
            'total_issues': sum(len(p.get('issues', [])) for p in pages)
        }
        
        return render_template('websites/detail.html',
                             project=project,
                             website=website,
                             pages=pages,
                             stats=stats,
                             recent_tests=recent_tests)
    
    except Exception as e:
        logger.error(f"Error viewing website {website_id}: {e}")
        flash('Error loading website.', 'error')
        return redirect(url_for('projects.view_project', project_id=project_id))


@websites_bp.route('/<website_id>/edit', methods=['GET', 'POST'])
def edit_website(project_id, website_id):
    """Edit website details and configuration."""
    try:
        project = project_manager.get_project(project_id)
        website = website_manager.get_website(website_id)
        
        if not project or not website:
            flash('Website not found.', 'error')
            return redirect(url_for('projects.view_project', project_id=project_id))
        
        if request.method == 'POST':
            # Get form data
            name = request.form.get('name', '').strip()
            base_url = request.form.get('base_url', '').strip()
            description = request.form.get('description', '').strip()
            
            # Scraping configuration
            max_depth = int(request.form.get('max_depth', 3))
            max_pages = int(request.form.get('max_pages', 100))
            respect_robots = request.form.get('respect_robots') == 'on'
            follow_external = request.form.get('follow_external') == 'on'
            
            # Validation
            errors = []
            if not name:
                errors.append('Website name is required.')
            if not base_url:
                errors.append('Base URL is required.')
            elif not base_url.startswith(('http://', 'https://')):
                errors.append('Base URL must start with http:// or https://')
            
            if max_depth < 1 or max_depth > 10:
                errors.append('Max depth must be between 1 and 10.')
            if max_pages < 1 or max_pages > 10000:
                errors.append('Max pages must be between 1 and 10,000.')
            
            if errors:
                for error in errors:
                    flash(error, 'error')
                return render_template('websites/edit.html',
                                     project=project,
                                     website=website,
                                     form_data=request.form)
            
            # Update website
            update_data = {
                'name': name,
                'base_url': base_url,
                'description': description,
                'scraping_config': {
                    'max_depth': max_depth,
                    'max_pages': max_pages,
                    'respect_robots_txt': respect_robots,
                    'follow_external_links': follow_external,
                }
            }
            
            success = website_manager.update_website(website_id, update_data)
            if success:
                flash(f'Website "{name}" updated successfully.', 'success')
                return redirect(url_for('websites.view_website',
                                      project_id=project_id,
                                      website_id=website_id))
            else:
                flash('Error updating website.', 'error')
        
        return render_template('websites/edit.html',
                             project=project,
                             website=website)
    
    except Exception as e:
        logger.error(f"Error editing website {website_id}: {e}")
        flash('Error editing website.', 'error')
        return redirect(url_for('websites.view_website',
                              project_id=project_id,
                              website_id=website_id))


@websites_bp.route('/<website_id>/delete', methods=['POST'])
def delete_website(project_id, website_id):
    """Delete a website and all its data."""
    try:
        project = project_manager.get_project(project_id)
        website = website_manager.get_website(website_id)
        
        if not project or not website:
            flash('Website not found.', 'error')
            return redirect(url_for('projects.view_project', project_id=project_id))
        
        # Verify confirmation
        confirm = request.form.get('confirm', '').strip().lower()
        if confirm != 'delete':
            flash('Confirmation text does not match. Website was not deleted.', 'error')
            return redirect(url_for('websites.edit_website',
                                  project_id=project_id,
                                  website_id=website_id))
        
        # Delete website
        success = website_manager.delete_website(website_id)
        if success:
            flash(f'Website "{website["name"]}" deleted successfully.', 'success')
            return redirect(url_for('projects.view_project', project_id=project_id))
        else:
            flash('Error deleting website.', 'error')
            return redirect(url_for('websites.view_website',
                                  project_id=project_id,
                                  website_id=website_id))
    
    except Exception as e:
        logger.error(f"Error deleting website {website_id}: {e}")
        flash('Error deleting website.', 'error')
        return redirect(url_for('websites.view_website',
                              project_id=project_id,
                              website_id=website_id))


@websites_bp.route('/<website_id>/scan', methods=['POST'])
def scan_website(project_id, website_id):
    """Start scanning/crawling a website for pages."""
    try:
        website = website_manager.get_website(website_id)
        if not website:
            return jsonify({'error': 'Website not found'}), 404
        
        # Start scanning process (this would typically be done asynchronously)
        scraper.configure(website.get('scraping_config', {}))
        
        # TODO: Implement async scanning with progress tracking
        # For now, return success response
        return jsonify({
            'success': True,
            'message': 'Website scan started',
            'scan_id': website_id  # In real implementation, this would be a unique scan ID
        })
    
    except Exception as e:
        logger.error(f"Error starting scan for website {website_id}: {e}")
        return jsonify({'error': 'Error starting scan'}), 500


@websites_bp.route('/<website_id>/test', methods=['POST'])
def test_website(project_id, website_id):
    """Start accessibility testing for all pages in a website."""
    try:
        website = website_manager.get_website(website_id)
        if not website:
            return jsonify({'error': 'Website not found'}), 404
        
        # TODO: Implement accessibility testing
        # This would start the testing process for all pages
        
        return jsonify({
            'success': True,
            'message': 'Accessibility testing started',
            'test_id': website_id  # In real implementation, this would be a unique test ID
        })
    
    except Exception as e:
        logger.error(f"Error starting test for website {website_id}: {e}")
        return jsonify({'error': 'Error starting test'}), 500