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
Website management routes for AutoTest web interface.
Handles website creation, editing, viewing, and deletion within projects.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from autotest.core.project_manager import ProjectManager
from autotest.core.website_manager import WebsiteManager
from autotest.core.scraper import WebScraper
import logging
import time
import threading

# Create blueprint
websites_bp = Blueprint('websites', __name__, url_prefix='/projects/<project_id>/websites')

# Initialize managers (will be set by app context)
project_manager = None
website_manager = None
scraper = None

logger = logging.getLogger(__name__)

# Store active test processes (in production, use Redis or database)
active_test_processes = {}


def init_website_managers(config, db_connection):
    """Initialize website managers (called by app factory)"""
    global project_manager, website_manager, scraper
    try:
        project_manager = ProjectManager(db_connection)
        website_manager = WebsiteManager(db_connection)
        scraper = WebScraper(config, db_connection)
        logger.info("Website managers initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize website managers: {e}")
        raise


@websites_bp.route('/')
def list_websites(project_id):
    """Display list of websites for a project."""
    try:
        project_result = project_manager.get_project(project_id)
        if not project_result.get('success'):
            flash('Project not found.', 'error')
            return redirect(url_for('projects.list_projects'))
        
        project = project_result['project']
        
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
        # Check if managers are initialized
        if project_manager is None:
            logger.error("Project manager not initialized")
            flash('System error: Project manager not available.', 'error')
            return redirect(url_for('main.index'))
        
        project_result = project_manager.get_project(project_id)
        if not project_result.get('success'):
            flash('Project not found.', 'error')
            return redirect(url_for('projects.list_projects'))
        
        project = project_result['project']
        
        if request.method == 'POST':
            # Get form data
            name = request.form.get('name', '').strip()
            base_url = request.form.get('base_url', '').strip()
            description = request.form.get('description', '').strip()
            
            # Scraping configuration
            max_depth_raw = request.form.get('max_depth', 'unlimited')
            if max_depth_raw == 'unlimited':
                max_depth = 'unlimited'
            else:
                max_depth = int(max_depth_raw)
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
            
            if max_depth != 'unlimited' and (max_depth < 1 or max_depth > 10):
                errors.append('Max depth must be between 1 and 10, or unlimited.')
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
            
            logger.info(f"Adding website '{name}' with URL '{base_url}' to project {project_id}")
            
            result = project_manager.add_website_to_project(
                project_id=project_id,
                name=name,
                url=base_url,
                description=description,
                scraping_config=website_data['scraping_config']
            )
            
            logger.info(f"Website addition result: {result}")
            
            if result['success']:
                flash(f'Website "{name}" added successfully.', 'success')
                return redirect(url_for('websites.view_website', 
                                      project_id=project_id, 
                                      website_id=result['website_id']))
            else:
                error_msg = result.get('error', 'Error creating website.')
                logger.error(f"Failed to add website: {error_msg}")
                flash(error_msg, 'error')
        
        return render_template('websites/add.html', project=project)
    
    except Exception as e:
        logger.error(f"Error adding website to project {project_id}: {e}")
        flash('Error adding website.', 'error')
        return redirect(url_for('projects.view_project', project_id=project_id))


@websites_bp.route('/<website_id>')
def view_website(project_id, website_id):
    """View website details and pages."""
    try:
        project_result = project_manager.get_project(project_id)
        if not project_result.get('success'):
            flash('Project not found.', 'error')
            return redirect(url_for('projects.list_projects'))
        
        project = project_result['project']
        
        # Find website in project
        logger.info(f"Looking for website_id: {website_id}")
        logger.info(f"Available websites in project: {[w.get('website_id') for w in project.get('websites', [])]}")
        
        website = None
        for w in project.get('websites', []):
            if w.get('website_id') == website_id:
                website = w
                break
        
        if not website:
            logger.error(f"Website {website_id} not found in project {project_id}")
            flash('Website not found.', 'error')
            return redirect(url_for('projects.view_project', project_id=project_id))
        
        # Get pages for this website
        pages_result = website_manager.get_website_pages(project_id, website_id)
        pages = pages_result.get('pages', []) if pages_result.get('success') else []
        
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
        project_result = project_manager.get_project(project_id)
        website = website_manager.get_website(website_id)
        
        logger.info(f"Edit website - project_result: {project_result.get('success') if project_result else 'None'}")
        logger.info(f"Edit website - website found: {website is not None}")
        
        if not project_result.get('success') or not website:
            logger.error(f"Website edit failed - project success: {project_result.get('success') if project_result else 'None'}, website: {website is not None}")
            flash('Website not found.', 'error')
            return redirect(url_for('projects.view_project', project_id=project_id))
        
        if request.method == 'POST':
            # Get form data
            name = request.form.get('name', '').strip()
            base_url = request.form.get('base_url', '').strip()
            description = request.form.get('description', '').strip()
            
            # Scraping configuration
            max_depth_raw = request.form.get('max_depth', 'unlimited')
            if max_depth_raw == 'unlimited':
                max_depth = 'unlimited'
            else:
                max_depth = int(max_depth_raw)
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
            
            if max_depth != 'unlimited' and (max_depth < 1 or max_depth > 10):
                errors.append('Max depth must be between 1 and 10, or unlimited.')
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
        
        project = project_result['project']
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
        project_result = project_manager.get_project(project_id)
        website = website_manager.get_website(website_id)
        
        logger.info(f"Delete website - project_result: {project_result.get('success') if project_result else 'None'}")
        logger.info(f"Delete website - website found: {website is not None}")
        
        if not project_result.get('success'):
            logger.error(f"Project {project_id} not found")
            flash('Project not found.', 'error')
            return redirect(url_for('projects.list_projects'))
            
        if not website:
            logger.error(f"Website {website_id} not found")
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
        # Check if managers are initialized
        if website_manager is None or scraper is None:
            logger.error("Website managers not initialized")
            return jsonify({'error': 'System error: Website managers not available'}), 500
        
        website = website_manager.get_website(website_id)
        if not website:
            return jsonify({'error': 'Website not found'}), 404
        
        logger.info(f"Starting scan for website {website_id} with URL: {website.get('url')}")
        
        # Configure scraper
        scraping_config = website.get('scraping_config', {})
        logger.info(f"Scraping config: {scraping_config}")
        
        # Get base URL and discover pages (simplified version)
        base_url = website.get('url')
        if not base_url:
            return jsonify({'error': 'Website has no base URL configured'}), 400
        
        logger.info(f"Starting page discovery for base URL: {base_url}")
        
        # For now, do a simple discovery by adding the base URL as a page
        # and a common about page (this simulates basic page discovery)
        discovered_pages = []
        
        # Add the home page
        home_result = website_manager.add_page_to_website(
            project_id, website_id, base_url, "Home Page", "", "automated"
        )
        if home_result.get('success'):
            discovered_pages.append(base_url)
            logger.info(f"Added home page: {base_url}")
        
        # Try to add common pages
        common_paths = ['/about', '/about.html', '/contact', '/services', '/products']
        for path in common_paths:
            try:
                page_url = base_url.rstrip('/') + path
                result = website_manager.add_page_to_website(
                    project_id, website_id, page_url, f"Page: {path}", "", "automated"
                )
                if result.get('success'):
                    discovered_pages.append(page_url)
                    logger.info(f"Added discovered page: {page_url}")
            except Exception as e:
                logger.warning(f"Failed to add page {page_url}: {e}")
        
        return jsonify({
            'success': True,
            'message': f'Page discovery completed. Found {len(discovered_pages)} pages.',
            'pages_discovered': len(discovered_pages),
            'pages': discovered_pages
        })
    
    except Exception as e:
        logger.error(f"Error starting scan for website {website_id}: {e}")
        return jsonify({'error': f'Error starting scan: {str(e)}'}), 500


@websites_bp.route('/<website_id>/test/debug', methods=['GET'])
def test_debug(project_id, website_id):
    """Debug route to check if routes are working."""
    return jsonify({
        'success': True,
        'message': f'Debug route working for project {project_id}, website {website_id}',
        'managers_initialized': {
            'website_manager': website_manager is not None,
            'project_manager': project_manager is not None
        }
    })

@websites_bp.route('/<website_id>/test', methods=['POST'])
def test_website(project_id, website_id):
    """Start accessibility testing for all pages in a website."""
    logger.info(f"Test website route called - project_id: {project_id}, website_id: {website_id}")
    
    try:
        # Check if managers are initialized
        if website_manager is None:
            logger.error("Website manager not initialized")
            return jsonify({'error': 'System error: Website manager not available'}), 500
        
        website = website_manager.get_website(website_id)
        if not website:
            logger.error(f"Website not found: {website_id}")
            return jsonify({'error': 'Website not found'}), 404
        
        logger.info(f"Found website: {website.get('name', 'Unnamed')}")
        
        # Get pages to test
        logger.info(f"Getting pages for website {website_id}")
        pages_result = website_manager.get_website_pages(project_id, website_id)
        logger.info(f"Pages result: {pages_result}")
        
        if not pages_result.get('success'):
            error_msg = pages_result.get('error', 'Could not get pages to test')
            logger.error(f"Failed to get pages: {error_msg}")
            return jsonify({'error': error_msg}), 400
        
        pages = pages_result.get('pages', [])
        logger.info(f"Found {len(pages)} total pages")
        
        # Filter out ignored pages
        pages_to_test = [p for p in pages if not p.get('ignored', False)]
        logger.info(f"Found {len(pages_to_test)} pages to test (after filtering ignored)")
        
        if not pages_to_test:
            logger.warning("No pages available to test")
            return jsonify({'error': 'No pages available to test. Add pages to this website first.'}), 400
        
        # Check if testing is already running
        if website_id in active_test_processes:
            return jsonify({'error': 'Testing already in progress'}), 400
        
        # Start testing process in background
        def run_testing():
            try:
                active_test_processes[website_id] = {
                    'type': 'testing',
                    'status': 'running',
                    'progress': 0,
                    'pages_tested': 0,
                    'issues_found': 0,
                    'total_pages': len(pages_to_test),
                    'current_page': '',
                    'start_time': time.time()
                }
                
                logger.info(f"Starting accessibility testing for {len(pages_to_test)} pages")
                
                total_issues = 0
                
                for i, page in enumerate(pages_to_test):
                    if website_id not in active_test_processes:  # Check if cancelled
                        break
                    
                    current_url = page.get('url', '')
                    active_test_processes[website_id]['current_page'] = current_url
                    
                    # TODO: Implement actual accessibility testing here
                    # For now, simulate testing with mock results
                    time.sleep(2)  # Simulate testing time
                    
                    # Mock test results - in real implementation, this would be actual accessibility testing
                    mock_issues = [
                        {
                            'rule': 'alt_text_missing',
                            'severity': 'serious',
                            'message': 'Image missing alternative text',
                            'element': '<img src="example.jpg">',
                            'line': 42
                        },
                        {
                            'rule': 'heading_order',
                            'severity': 'moderate', 
                            'message': 'Heading levels should increase by one',
                            'element': '<h3>Section Title</h3>',
                            'line': 15
                        }
                    ] if i % 3 == 0 else []  # Add issues to some pages
                    
                    total_issues += len(mock_issues)
                    
                    # Update page with test results (this would be done by the actual tester)
                    try:
                        website_manager.update_page_test_results(
                            project_id, website_id, page.get('page_id'),
                            {'issues': mock_issues, 'test_date': None}  # None will set current timestamp
                        )
                    except Exception as e:
                        logger.warning(f"Failed to update test results for page {page.get('page_id')}: {e}")
                    
                    # Update progress
                    pages_tested = i + 1
                    progress = int((pages_tested / len(pages_to_test)) * 100)
                    
                    active_test_processes[website_id].update({
                        'progress': progress,
                        'pages_tested': pages_tested,
                        'issues_found': total_issues
                    })
                    
                    logger.info(f"Tested page {pages_tested}/{len(pages_to_test)}: {current_url}")
                
                # Mark as completed
                if website_id in active_test_processes:
                    active_test_processes[website_id]['status'] = 'completed'
                    active_test_processes[website_id]['current_page'] = ''
                    logger.info(f"Testing completed. {total_issues} issues found across {len(pages_to_test)} pages")
                    
                    # Clean up after delay
                    time.sleep(5)
                    if website_id in active_test_processes:
                        del active_test_processes[website_id]
                
            except Exception as e:
                logger.error(f"Error during accessibility testing for website {website_id}: {e}")
                if website_id in active_test_processes:
                    active_test_processes[website_id]['status'] = 'error'
        
        # Start background thread
        thread = threading.Thread(target=run_testing)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'message': 'Accessibility testing started',
            'test_id': website_id,
            'total_pages': len(pages_to_test)
        })
    
    except Exception as e:
        logger.error(f"Error starting test for website {website_id}: {e}")
        return jsonify({'error': 'Error starting test'}), 500


@websites_bp.route('/<website_id>/test/status')
def test_status(project_id, website_id):
    """Get status of accessibility testing process."""
    try:
        if website_id not in active_test_processes:
            return jsonify({'status': 'not_running'})
        
        process = active_test_processes[website_id]
        return jsonify({
            'status': process['status'],
            'progress': process['progress'],
            'pages_tested': process['pages_tested'],
            'issues_found': process['issues_found'],
            'total_pages': process['total_pages'],
            'current_page': process['current_page'],
            'elapsed_time': int(time.time() - process['start_time'])
        })
    
    except Exception as e:
        logger.error(f"Error getting test status for website {website_id}: {e}")
        return jsonify({'error': 'Error getting status'}), 500


@websites_bp.route('/<website_id>/test/cancel', methods=['POST'])
def cancel_test(project_id, website_id):
    """Cancel ongoing accessibility testing."""
    try:
        if website_id in active_test_processes:
            del active_test_processes[website_id]
            return jsonify({'success': True, 'message': 'Testing cancelled'})
        else:
            return jsonify({'error': 'No testing process running'}), 400
    
    except Exception as e:
        logger.error(f"Error cancelling test for website {website_id}: {e}")
        return jsonify({'error': 'Error cancelling test'}), 500