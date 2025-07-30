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
Page management routes for AutoTest web interface.
Handles page discovery, manual addition, testing, and management within websites.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from autotest.core.project_manager import ProjectManager
from autotest.core.website_manager import WebsiteManager
from autotest.core.scraper import WebScraper
from autotest.core.accessibility_tester import AccessibilityTester
import logging
import threading
import time

# Create blueprint
pages_bp = Blueprint('pages', __name__, url_prefix='/projects/<project_id>/websites/<website_id>/pages')

# Initialize managers
project_manager = None  # ProjectManager()
website_manager = None  # WebsiteManager()
scraper = None  # WebScraper()
accessibility_tester = None  # AccessibilityTester()

logger = logging.getLogger(__name__)

# Store active scan/test processes (in production, use Redis or database)
active_processes = {}


def init_page_managers(config, db_connection):
    """Initialize page managers (called by app factory)"""
    global project_manager, website_manager, scraper, accessibility_tester
    try:
        project_manager = ProjectManager(db_connection)
        website_manager = WebsiteManager(db_connection)
        scraper = WebScraper(config, db_connection)
        accessibility_tester = AccessibilityTester(config, db_connection)
        logger.info("Page managers initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize page managers: {e}")
        raise


@pages_bp.route('/')
def list_pages(project_id, website_id):
    """Display list of pages for a website."""
    try:
        project_result = project_manager.get_project(project_id)
        website = website_manager.get_website(website_id)
        
        if not project_result.get('success') or not website:
            flash('Website not found.', 'error')
            return redirect(url_for('projects.view_project', project_id=project_id))
        
        project = project_result['project']
        
        # Get pages from database 
        filter_status = request.args.get('status', '')
        sort_by = request.args.get('sort', 'url')
        search_query = request.args.get('q', '')
        
        # Get pages from database using website_manager
        logger.info(f"Getting pages for website {website_id} in project {project_id}")
        pages_result = website_manager.get_website_pages(project_id, website_id)
        logger.info(f"Pages result: {pages_result}")
        
        if pages_result.get('success'):
            pages = pages_result.get('pages', [])
            logger.info(f"Found {len(pages)} pages")
        else:
            pages = []
            logger.warning(f"Failed to get pages for website {website_id}: {pages_result.get('error', 'Unknown error')}")
        
        # Apply filters
        if filter_status:
            if filter_status == 'tested':
                pages = [p for p in pages if p.get('last_test_date')]
            elif filter_status == 'scanned':
                pages = [p for p in pages if p.get('last_scan_date') and not p.get('last_test_date')]
            elif filter_status == 'discovered':
                pages = [p for p in pages if not p.get('last_scan_date')]
        
        # Apply search
        if search_query:
            pages = [p for p in pages if search_query.lower() in p.get('url', '').lower() or 
                    search_query.lower() in p.get('title', '').lower()]
        
        # Apply sorting
        if sort_by == 'title':
            pages.sort(key=lambda p: p.get('title', p.get('url', '')).lower())
        elif sort_by == 'status':
            def status_sort_key(p):
                if p.get('last_test_date'): return 3
                elif p.get('last_scan_date'): return 2
                else: return 1
            pages.sort(key=status_sort_key, reverse=True)
        elif sort_by == 'issues':
            pages.sort(key=lambda p: len(p.get('issues', [])), reverse=True)
        else:  # default: url
            pages.sort(key=lambda p: p.get('url', '').lower())
        
        # Calculate statistics using actual pages from database
        all_pages = pages_result.get('pages', []) if pages_result.get('success') else []
        stats = {
            'total_pages': len(all_pages),
            'tested_pages': len([p for p in all_pages if p.get('last_test_date')]),
            'scanned_pages': len([p for p in all_pages if p.get('last_scan_date')]),
            'pages_with_issues': len([p for p in all_pages if p.get('issues', [])]),
            'total_issues': sum(len(p.get('issues', [])) for p in all_pages)
        }
        
        return render_template('pages/list.html',
                             project=project,
                             website=website,
                             pages=pages,
                             stats=stats,
                             current_filter=filter_status,
                             current_sort=sort_by,
                             search_query=search_query)
    
    except Exception as e:
        logger.error(f"Error listing pages for website {website_id}: {e}")
        flash('Error loading pages.', 'error')
        return redirect(url_for('websites.view_website',
                              project_id=project_id,
                              website_id=website_id))


@pages_bp.route('/add', methods=['GET', 'POST'])
def add_page(project_id, website_id):
    """Manually add a page to the website."""
    try:
        # Check if managers are initialized
        if project_manager is None or website_manager is None:
            logger.error("Page managers not initialized")
            flash('System error: Page managers not available.', 'error')
            return redirect(url_for('main.index'))
        
        project_result = project_manager.get_project(project_id)
        website = website_manager.get_website(website_id)
        
        if not project_result.get('success') or not website:
            flash('Website not found.', 'error')
            return redirect(url_for('projects.view_project', project_id=project_id))
        
        project = project_result['project']
        
        if request.method == 'POST':
            # Get form data
            url = request.form.get('url', '').strip()
            title = request.form.get('title', '').strip()
            description = request.form.get('description', '').strip()
            
            # Validation
            errors = []
            if not url:
                errors.append('Page URL is required.')
            elif not url.startswith(('http://', 'https://')):
                errors.append('Page URL must start with http:// or https://')
            
            # Check if page already exists
            existing_pages = website.get('pages', [])
            if any(p.get('url') == url for p in existing_pages):
                errors.append('A page with this URL already exists.')
            
            if errors:
                for error in errors:
                    flash(error, 'error')
                return render_template('pages/add.html',
                                     project=project,
                                     website=website,
                                     form_data=request.form)
            
            # Add page using correct method signature
            logger.info(f"Adding page '{url}' to website {website_id} in project {project_id}")
            
            result = website_manager.add_page_to_website(
                project_id=project_id,
                website_id=website_id, 
                url=url,
                title=title or "",
                description=description or "",
                discovered_method='manual'
            )
            
            logger.info(f"Page addition result: {result}")
            
            if result.get('success'):
                flash(f'Page added successfully.', 'success')
                return redirect(url_for('pages.list_pages',
                                      project_id=project_id,
                                      website_id=website_id))
            else:
                error_msg = result.get('error', 'Error adding page.')
                flash(error_msg, 'error')
        
        return render_template('pages/add.html',
                             project=project,
                             website=website)
    
    except Exception as e:
        logger.error(f"Error adding page to website {website_id}: {e}")
        flash('Error adding page.', 'error')
        return redirect(url_for('websites.view_website',
                              project_id=project_id,
                              website_id=website_id))


@pages_bp.route('/<page_id>')
def view_page(project_id, website_id, page_id):
    """View page details and test results."""
    try:
        project = project_manager.get_project(project_id)
        website = website_manager.get_website(website_id)
        
        if not project or not website:
            flash('Website not found.', 'error')
            return redirect(url_for('projects.view_project', project_id=project_id))
        
        # Find the specific page
        page = None
        for p in website.get('pages', []):
            if p.get('page_id') == page_id:
                page = p
                break
        
        if not page:
            flash('Page not found.', 'error')
            return redirect(url_for('pages.list_pages',
                                  project_id=project_id,
                                  website_id=website_id))
        
        # Get test results grouped by severity
        issues = page.get('issues', [])
        issues_by_severity = {
            'critical': [i for i in issues if i.get('severity') == 'critical'],
            'serious': [i for i in issues if i.get('severity') == 'serious'],
            'moderate': [i for i in issues if i.get('severity') == 'moderate'],
            'minor': [i for i in issues if i.get('severity') == 'minor']
        }
        
        return render_template('pages/detail.html',
                             project=project,
                             website=website,
                             page=page,
                             issues_by_severity=issues_by_severity)
    
    except Exception as e:
        logger.error(f"Error viewing page {page_id}: {e}")
        flash('Error loading page.', 'error')
        return redirect(url_for('pages.list_pages',
                              project_id=project_id,
                              website_id=website_id))


@pages_bp.route('/<page_id>/test', methods=['POST'])
def test_page(project_id, website_id, page_id):
    """Run accessibility test on a specific page."""
    try:
        website = website_manager.get_website(website_id)
        if not website:
            return jsonify({'error': 'Website not found'}), 404
        
        # Find the specific page
        page = None
        for p in website.get('pages', []):
            if p.get('page_id') == page_id:
                page = p
                break
        
        if not page:
            return jsonify({'error': 'Page not found'}), 404
        
        # Start testing process in background
        def run_test():
            try:
                # TODO: Implement actual accessibility testing
                # This would run the accessibility tester on the page
                time.sleep(2)  # Simulate testing time
                
                # Mock test results
                test_results = {
                    'page_id': page_id,
                    'issues': [
                        {
                            'rule': 'alt_text_missing',
                            'severity': 'serious',
                            'message': 'Image missing alternative text',
                            'element': '<img src="example.jpg">',
                            'line': 42
                        }
                    ],
                    'test_date': None  # Will be set by website_manager
                }
                
                # Update page with test results
                website_manager.update_page_test_results(website_id, page_id, test_results)
                
            except Exception as e:
                logger.error(f"Error testing page {page_id}: {e}")
        
        # Start background thread
        thread = threading.Thread(target=run_test)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'message': 'Page testing started',
            'test_id': page_id
        })
    
    except Exception as e:
        logger.error(f"Error starting test for page {page_id}: {e}")
        return jsonify({'error': 'Error starting test'}), 500


@pages_bp.route('/<page_id>/edit', methods=['GET', 'POST'])
def edit_page(project_id, website_id, page_id):
    """Edit a page's details."""
    try:
        # Check if managers are initialized
        if project_manager is None or website_manager is None:
            logger.error("Page managers not initialized")
            flash('System error: Page managers not available.', 'error')
            return redirect(url_for('main.index'))
        
        project_result = project_manager.get_project(project_id)
        website = website_manager.get_website(website_id)
        
        if not project_result.get('success') or not website:
            flash('Website not found.', 'error')
            return redirect(url_for('projects.view_project', project_id=project_id))
        
        project = project_result['project']
        
        # Get the page from database
        page = website_manager.page_repo.get_page(page_id)
        if not page:
            flash('Page not found.', 'error')
            return redirect(url_for('pages.list_pages',
                                  project_id=project_id,
                                  website_id=website_id))
        
        # Verify page belongs to this project/website
        if page.project_id != project_id or page.website_id != website_id:
            flash('Page not found.', 'error')
            return redirect(url_for('pages.list_pages',
                                  project_id=project_id,
                                  website_id=website_id))
        
        if request.method == 'POST':
            # Get form data
            url = request.form.get('url', '').strip()
            title = request.form.get('title', '').strip()
            description = request.form.get('description', '').strip()
            
            # Validation
            errors = []
            if not url:
                errors.append('Page URL is required.')
            elif not url.startswith(('http://', 'https://')):
                errors.append('Page URL must start with http:// or https://')
            
            # Check if URL changed and conflicts with existing page
            if url != page.url:
                if website_manager.page_repo.page_exists(project_id, website_id, url):
                    errors.append('A page with this URL already exists.')
            
            if errors:
                for error in errors:
                    flash(error, 'error')
                return render_template('pages/edit.html',
                                     project=project,
                                     website=website,
                                     page=page,
                                     form_data=request.form)
            
            # Update page
            logger.info(f"Updating page {page_id} with URL '{url}', title '{title}', and description '{description}'")
            
            result = website_manager.update_page(
                page_id=page_id,
                url=url if url != page.url else None,
                title=title if title != page.title else None,
                description=description if description != page.description else None
            )
            
            if result.get('success'):
                flash('Page updated successfully.', 'success')
                return redirect(url_for('pages.view_page',
                                      project_id=project_id,
                                      website_id=website_id,
                                      page_id=page_id))
            else:
                error_msg = result.get('error', 'Error updating page.')
                flash(error_msg, 'error')
        
        return render_template('pages/edit.html',
                             project=project,
                             website=website,
                             page=page)
    
    except Exception as e:
        logger.error(f"Error editing page {page_id}: {e}")
        flash('Error editing page.', 'error')
        return redirect(url_for('pages.list_pages',
                              project_id=project_id,
                              website_id=website_id))


@pages_bp.route('/<page_id>/toggle-ignore', methods=['POST'])
def toggle_page_ignore(project_id, website_id, page_id):
    """Toggle ignore status of a page."""
    try:
        # Check if managers are initialized
        if website_manager is None:
            logger.error("Website manager not initialized")
            return jsonify({'error': 'System error: Website manager not available'}), 500
        
        # Verify page exists and belongs to this project/website
        page = website_manager.page_repo.get_page(page_id)
        if not page:
            return jsonify({'error': 'Page not found'}), 404
            
        if page.project_id != project_id or page.website_id != website_id:
            return jsonify({'error': 'Page not found'}), 404
        
        # Toggle ignore status
        logger.info(f"Toggling ignore status for page {page_id}")
        success = website_manager.page_repo.toggle_ignored(page_id)
        
        if success:
            # Get updated page to return new status
            updated_page = website_manager.page_repo.get_page(page_id)
            return jsonify({
                'success': True,
                'ignored': updated_page.ignored,
                'message': f'Page {"ignored" if updated_page.ignored else "unignored"} successfully'
            })
        else:
            return jsonify({'error': 'Failed to toggle ignore status'}), 500
    
    except Exception as e:
        logger.error(f"Error toggling ignore status for page {page_id}: {e}")
        return jsonify({'error': 'Error updating page'}), 500


@pages_bp.route('/<page_id>/delete', methods=['POST'])
def delete_page(project_id, website_id, page_id):
    """Delete a page from the website."""
    try:
        # Check if managers are initialized
        if website_manager is None:
            logger.error("Website manager not initialized")
            flash('System error: Website manager not available.', 'error')
            return redirect(url_for('main.index'))
        
        website = website_manager.get_website(website_id)
        if not website:
            flash('Website not found.', 'error')
            return redirect(url_for('projects.view_project', project_id=project_id))
        
        # Remove the page using correct method signature
        logger.info(f"Deleting page {page_id} from website {website_id} in project {project_id}")
        
        result = website_manager.remove_page_from_website(project_id, website_id, page_id)
        logger.info(f"Page deletion result: {result}")
        
        if result.get('success'):
            flash('Page deleted successfully.', 'success')
        else:
            error_msg = result.get('error', 'Error deleting page.')
            logger.error(f"Failed to delete page: {error_msg}")
            flash(error_msg, 'error')
        
        return redirect(url_for('pages.list_pages',
                              project_id=project_id,
                              website_id=website_id))
    
    except Exception as e:
        logger.error(f"Error deleting page {page_id}: {e}")
        flash('Error deleting page.', 'error')
        return redirect(url_for('pages.list_pages',
                              project_id=project_id,
                              website_id=website_id))


@pages_bp.route('/discover', methods=['POST'])
def discover_pages(project_id, website_id):
    """Start automated page discovery for the website."""
    try:
        website = website_manager.get_website(website_id)
        if not website:
            return jsonify({'error': 'Website not found'}), 404
        
        # Check if discovery is already running
        if website_id in active_processes:
            return jsonify({'error': 'Discovery already in progress'}), 400
        
        # Start discovery process in background
        def run_discovery():
            try:
                active_processes[website_id] = {
                    'type': 'discovery',
                    'status': 'running',
                    'progress': 0,
                    'pages_found': 0,
                    'start_time': time.time()
                }
                
                # Configure scraper
                config = website.get('scraping_config', {})
                scraper.configure(config)
                
                # TODO: Implement actual page discovery
                # This would use the scraper to crawl the website
                base_url = website.get('url')
                max_pages = config.get('max_pages', 100)
                
                # Simulate discovery process
                for i in range(min(10, max_pages)):  # Mock discovery of up to 10 pages
                    if website_id not in active_processes:  # Check if cancelled
                        break
                    
                    time.sleep(0.5)  # Simulate discovery time
                    
                    # Mock discovered page URL and title
                    page_url = f"{base_url}/page-{i+1}"
                    page_title = f"Page {i+1}"
                    
                    # Add page to website
                    result = website_manager.add_page_to_website(
                        project_id, website_id, page_url, page_title, "", "automated"
                    )
                    
                    if not result.get('success'):
                        logger.warning(f"Failed to add discovered page: {result.get('error')}")
                    
                    # Update progress
                    active_processes[website_id]['progress'] = int((i + 1) / 10 * 100)
                    active_processes[website_id]['pages_found'] = i + 1
                
                # Mark as completed
                if website_id in active_processes:
                    active_processes[website_id]['status'] = 'completed'
                    # Clean up after delay
                    time.sleep(5)
                    if website_id in active_processes:
                        del active_processes[website_id]
                
            except Exception as e:
                logger.error(f"Error during page discovery for website {website_id}: {e}")
                if website_id in active_processes:
                    active_processes[website_id]['status'] = 'error'
        
        # Start background thread
        thread = threading.Thread(target=run_discovery)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'message': 'Page discovery started',
            'discovery_id': website_id
        })
    
    except Exception as e:
        logger.error(f"Error starting discovery for website {website_id}: {e}")
        return jsonify({'error': 'Error starting discovery'}), 500


@pages_bp.route('/discover/status')
def discovery_status(project_id, website_id):
    """Get status of page discovery process."""
    try:
        if website_id not in active_processes:
            return jsonify({'status': 'not_running'})
        
        process = active_processes[website_id]
        return jsonify({
            'status': process['status'],
            'progress': process['progress'],
            'pages_found': process['pages_found'],
            'elapsed_time': int(time.time() - process['start_time'])
        })
    
    except Exception as e:
        logger.error(f"Error getting discovery status for website {website_id}: {e}")
        return jsonify({'error': 'Error getting status'}), 500


@pages_bp.route('/discover/cancel', methods=['POST'])
def cancel_discovery(project_id, website_id):
    """Cancel ongoing page discovery."""
    try:
        if website_id in active_processes:
            del active_processes[website_id]
            return jsonify({'success': True, 'message': 'Discovery cancelled'})
        else:
            return jsonify({'error': 'No discovery process running'}), 400
    
    except Exception as e:
        logger.error(f"Error cancelling discovery for website {website_id}: {e}")
        return jsonify({'error': 'Error cancelling discovery'}), 500


@pages_bp.route('/bulk-action', methods=['POST'])
def bulk_action(project_id, website_id):
    """Perform bulk actions on selected pages."""
    try:
        action = request.form.get('action')
        page_ids = request.form.getlist('page_ids')
        
        if not action or not page_ids:
            flash('No action or pages selected.', 'error')
            return redirect(url_for('pages.list_pages',
                                  project_id=project_id,
                                  website_id=website_id))
        
        website = website_manager.get_website(website_id)
        if not website:
            flash('Website not found.', 'error')
            return redirect(url_for('projects.view_project', project_id=project_id))
        
        success_count = 0
        
        if action == 'delete':
            for page_id in page_ids:
                if website_manager.remove_page_from_website(website_id, page_id):
                    success_count += 1
            
            flash(f'Deleted {success_count} of {len(page_ids)} pages.', 'success')
        
        elif action == 'test':
            # Start bulk testing
            def run_bulk_test():
                for page_id in page_ids:
                    try:
                        # TODO: Implement actual testing
                        time.sleep(1)  # Simulate testing
                        # Mock test results would be added here
                    except Exception as e:
                        logger.error(f"Error testing page {page_id}: {e}")
            
            thread = threading.Thread(target=run_bulk_test)
            thread.daemon = True
            thread.start()
            
            flash(f'Started testing {len(page_ids)} pages.', 'success')
        
        else:
            flash('Unknown action.', 'error')
        
        return redirect(url_for('pages.list_pages',
                              project_id=project_id,
                              website_id=website_id))
    
    except Exception as e:
        logger.error(f"Error performing bulk action: {e}")
        flash('Error performing bulk action.', 'error')
        return redirect(url_for('pages.list_pages',
                              project_id=project_id,
                              website_id=website_id))