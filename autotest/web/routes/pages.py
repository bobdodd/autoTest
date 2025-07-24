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
project_manager = ProjectManager()
website_manager = WebsiteManager()
scraper = WebScraper()
accessibility_tester = AccessibilityTester()

logger = logging.getLogger(__name__)

# Store active scan/test processes (in production, use Redis or database)
active_processes = {}


@pages_bp.route('/')
def list_pages(project_id, website_id):
    """Display list of pages for a website."""
    try:
        project = project_manager.get_project(project_id)
        website = website_manager.get_website(website_id)
        
        if not project or not website:
            flash('Website not found.', 'error')
            return redirect(url_for('projects.view_project', project_id=project_id))
        
        # Get pages with filtering and sorting
        filter_status = request.args.get('status', '')
        sort_by = request.args.get('sort', 'url')
        search_query = request.args.get('q', '')
        
        pages = website.get('pages', [])
        
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
        
        # Calculate statistics
        stats = {
            'total_pages': len(website.get('pages', [])),
            'tested_pages': len([p for p in website.get('pages', []) if p.get('last_test_date')]),
            'scanned_pages': len([p for p in website.get('pages', []) if p.get('last_scan_date')]),
            'pages_with_issues': len([p for p in website.get('pages', []) if p.get('issues', [])]),
            'total_issues': sum(len(p.get('issues', [])) for p in website.get('pages', []))
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
        project = project_manager.get_project(project_id)
        website = website_manager.get_website(website_id)
        
        if not project or not website:
            flash('Website not found.', 'error')
            return redirect(url_for('projects.view_project', project_id=project_id))
        
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
            
            # Add page
            page_data = {
                'url': url,
                'title': title or None,
                'description': description or None,
                'discovery_method': 'manual',
                'added_date': None  # Will be set by website_manager
            }
            
            page_id = website_manager.add_page_to_website(website_id, page_data)
            if page_id:
                flash(f'Page added successfully.', 'success')
                return redirect(url_for('pages.list_pages',
                                      project_id=project_id,
                                      website_id=website_id))
            else:
                flash('Error adding page.', 'error')
        
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


@pages_bp.route('/<page_id>/delete', methods=['POST'])
def delete_page(project_id, website_id, page_id):
    """Delete a page from the website."""
    try:
        website = website_manager.get_website(website_id)
        if not website:
            flash('Website not found.', 'error')
            return redirect(url_for('projects.view_project', project_id=project_id))
        
        # Find and remove the page
        success = website_manager.remove_page_from_website(website_id, page_id)
        if success:
            flash('Page deleted successfully.', 'success')
        else:
            flash('Error deleting page.', 'error')
        
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
                base_url = website.get('base_url')
                max_pages = config.get('max_pages', 100)
                
                # Simulate discovery process
                for i in range(min(10, max_pages)):  # Mock discovery of up to 10 pages
                    if website_id not in active_processes:  # Check if cancelled
                        break
                    
                    time.sleep(0.5)  # Simulate discovery time
                    
                    # Mock discovered page
                    page_data = {
                        'url': f"{base_url}/page-{i+1}",
                        'title': f"Page {i+1}",
                        'discovery_method': 'automated',
                        'depth': 1
                    }
                    
                    # Add page to website
                    website_manager.add_page_to_website(website_id, page_data)
                    
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