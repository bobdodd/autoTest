"""
Website management module for AutoTest application
"""

from typing import Dict, List, Optional, Any
import datetime
from urllib.parse import urlparse, urljoin

from autotest.core.database import DatabaseConnection
from autotest.models.project import ProjectRepository
from autotest.models.page import Page, PageRepository
from autotest.utils.logger import LoggerMixin


class WebsiteManager(LoggerMixin):
    """Website management class with business logic"""
    
    def __init__(self, db_connection: DatabaseConnection):
        """
        Initialize website manager
        
        Args:
            db_connection: Database connection instance
        """
        self.db_connection = db_connection
        self.project_repo = ProjectRepository(db_connection)
        self.page_repo = PageRepository(db_connection)
    
    def add_page_to_website(self, project_id: str, website_id: str, url: str, 
                           title: str = "", description: str = "", discovered_method: str = "manual") -> Dict[str, Any]:
        """
        Add a page to a website
        
        Args:
            project_id: Project ID
            website_id: Website ID
            url: Page URL
            title: Page title
            description: Page description
            discovered_method: How the page was discovered ("manual" or "scraping")
        
        Returns:
            Dictionary with success status and page details
        """
        try:
            # Validate project and website exist
            project = self.project_repo.get_project(project_id)
            if not project:
                return {
                    'success': False,
                    'error': 'Project not found'
                }
            
            website = project.get_website(website_id)
            if not website:
                return {
                    'success': False,
                    'error': 'Website not found in project'
                }
            
            # Validate URL format
            if not self._is_valid_url(url):
                return {
                    'success': False,
                    'error': 'Invalid URL format'
                }
            
            # Check if page already exists
            if self.page_repo.page_exists(project_id, website_id, url):
                return {
                    'success': False,
                    'error': 'Page already exists in this website'
                }
            
            # Create the page
            self.logger.info(f"Creating page with project_id={project_id}, website_id={website_id}, url={url}")
            page_id = self.page_repo.create_page(
                project_id, website_id, url, title, description, discovered_method
            )
            
            self.logger.info(f"Added page {url} to website {website_id} with page_id {page_id}")
            
            # Verify the page was created by trying to retrieve it
            created_pages = self.page_repo.get_pages_by_website(project_id, website_id)
            self.logger.info(f"After creation, found {len(created_pages)} pages for website {website_id}")
            
            return {
                'success': True,
                'page_id': page_id,
                'message': f'Page "{url}" added successfully'
            }
            
        except Exception as e:
            self.logger.error(f"Error adding page to website: {e}")
            return {
                'success': False,
                'error': f'Failed to add page: {str(e)}'
            }
    
    def remove_page_from_website(self, project_id: str, website_id: str, page_id: str) -> Dict[str, Any]:
        """
        Remove a page from a website
        
        Args:
            project_id: Project ID
            website_id: Website ID
            page_id: Page ID
        
        Returns:
            Dictionary with success status and message
        """
        try:
            self.logger.info(f"Starting deletion of page {page_id} from website {website_id} in project {project_id}")
            
            # Verify the page belongs to the correct project and website
            page = self.page_repo.get_page(page_id)
            if not page:
                self.logger.error(f"Page {page_id} not found in database")
                return {
                    'success': False,
                    'error': 'Page not found'
                }
            
            self.logger.info(f"Page found: project_id={page.project_id}, website_id={page.website_id}")
            
            if page.project_id != project_id or page.website_id != website_id:
                self.logger.error(f"Page belongs to project {page.project_id}/website {page.website_id}, not {project_id}/{website_id}")
                return {
                    'success': False,
                    'error': 'Page does not belong to the specified project and website'
                }
            
            # Delete associated test results first
            self.logger.info(f"Deleting test results for page {page_id}")
            from autotest.models.test_result import TestResultRepository
            test_result_repo = TestResultRepository(self.db_connection)
            results_deleted = test_result_repo.delete_results_by_page(page_id)
            self.logger.info(f"Deleted {results_deleted} test results")
            
            # Delete the page
            self.logger.info(f"Deleting page {page_id} from database")
            success = self.page_repo.delete(page_id)
            self.logger.info(f"Page deletion success: {success}")
            
            if success:
                self.logger.info(f"Removed page {page_id} from website {website_id}")
                return {
                    'success': True,
                    'message': 'Page removed successfully',
                    'deleted_results': results_deleted
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to remove page'
                }
                
        except Exception as e:
            self.logger.error(f"Error removing page {page_id}: {e}")
            return {
                'success': False,
                'error': f'Failed to remove page: {str(e)}'
            }
    
    def update_page(self, page_id: str, url: Optional[str] = None, 
                   title: Optional[str] = None, description: Optional[str] = None) -> Dict[str, Any]:
        """
        Update page information
        
        Args:
            page_id: Page ID
            url: New page URL (optional)
            title: New page title (optional)
            description: New page description (optional)
        
        Returns:
            Dictionary with success status and message
        """
        try:
            # Check if page exists
            page = self.page_repo.get_page(page_id)
            if not page:
                return {
                    'success': False,
                    'error': 'Page not found'
                }
            
            # Validate new URL if provided
            if url and not self._is_valid_url(url):
                return {
                    'success': False,
                    'error': 'Invalid URL format'
                }
            
            # Check for URL conflicts if URL is being changed
            if url and url != page.url:
                if self.page_repo.page_exists(page.project_id, page.website_id, url):
                    return {
                        'success': False,
                        'error': 'A page with this URL already exists in the website'
                    }
            
            success = self.page_repo.update_page(page_id, title, url, description)
            
            if success:
                self.logger.info(f"Updated page {page_id}")
                return {
                    'success': True,
                    'message': 'Page updated successfully'
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to update page'
                }
                
        except Exception as e:
            self.logger.error(f"Error updating page {page_id}: {e}")
            return {
                'success': False,
                'error': f'Failed to update page: {str(e)}'
            }
    
    def get_website(self, website_id: str) -> Optional[Dict[str, Any]]:
        """
        Get website details by website ID
        
        Args:
            website_id: Website ID to search for
            
        Returns:
            Website dictionary if found, None otherwise
        """
        try:
            self.logger.info(f"Searching for website_id: {website_id}")
            
            # Search through all projects to find the website
            projects = self.project_repo.get_all_projects()
            self.logger.info(f"Found {len(projects)} projects to search")
            
            for project in projects:
                self.logger.info(f"Searching project {project.project_id} with {len(project.websites)} websites")
                for website in project.websites:
                    self.logger.info(f"  - Website ID: {website.website_id}")
                
                website = project.get_website(website_id)
                if website:
                    self.logger.info(f"Found website {website_id} in project {project.project_id}")
                    return website.to_dict()
            
            self.logger.warning(f"Website {website_id} not found in any project")
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting website {website_id}: {e}")
            return None

    def update_website(self, website_id: str, update_data: Dict[str, Any]) -> bool:
        """
        Update website details
        
        Args:
            website_id: Website ID to update
            update_data: Dictionary containing fields to update
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Find the project containing this website
            projects = self.project_repo.get_all_projects()
            
            for project in projects:
                website = project.get_website(website_id)
                if website:
                    # Update website fields
                    if 'name' in update_data:
                        website.name = update_data['name']
                    if 'base_url' in update_data:
                        website.url = update_data['base_url']
                    if 'description' in update_data:
                        website.description = update_data['description']
                    if 'scraping_config' in update_data:
                        website.scraping_config = update_data['scraping_config']
                    
                    # Update the project in database
                    success = self.project_repo.update(
                        project.project_id, 
                        {'websites': [w.to_dict() for w in project.websites]}
                    )
                    
                    if success:
                        self.logger.info(f"Updated website {website_id}")
                    return success
            
            self.logger.error(f"Website {website_id} not found for update")
            return False
            
        except Exception as e:
            self.logger.error(f"Error updating website {website_id}: {e}")
            return False

    def delete_website(self, website_id: str) -> bool:
        """
        Delete a website and all its data
        
        Args:
            website_id: Website ID to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info(f"Starting deletion of website {website_id}")
            
            # Find the project containing this website
            projects = self.project_repo.get_all_projects()
            self.logger.info(f"Found {len(projects)} projects to search for website deletion")
            
            for project in projects:
                self.logger.info(f"Checking project {project.project_id} for website {website_id}")
                if project.get_website(website_id):
                    self.logger.info(f"Found website {website_id} in project {project.project_id}")
                    
                    # Remove website from project
                    success = project.remove_website(website_id)
                    self.logger.info(f"Website removal from project: {success}")
                    
                    if success:
                        # Update the project in database
                        self.logger.info(f"Updating project {project.project_id} in database")
                        success = self.project_repo.update(
                            project.project_id, 
                            {'websites': [w.to_dict() for w in project.websites]}
                        )
                        self.logger.info(f"Database update result: {success}")
                        
                        if success:
                            self.logger.info(f"Successfully deleted website {website_id}")
                            
                            # Also delete all pages for this website
                            # We need the project_id, so we'll get it from the project
                            page_delete_result = self.page_repo.delete_pages_by_website(
                                project.project_id, website_id
                            )
                            self.logger.info(f"Deleted {page_delete_result} pages for website {website_id}")
                        
                        return success
                    else:
                        self.logger.error(f"Failed to remove website {website_id} from project")
                        return False
            
            self.logger.error(f"Website {website_id} not found in any project for deletion")
            return False
            
        except Exception as e:
            self.logger.error(f"Error deleting website {website_id}: {e}")
            return False

    def get_website_pages(self, project_id: str, website_id: str) -> Dict[str, Any]:
        """
        Get all pages for a website
        
        Args:
            project_id: Project ID
            website_id: Website ID
        
        Returns:
            Dictionary with pages list or error
        """
        try:
            # Validate project and website exist
            project = self.project_repo.get_project(project_id)
            if not project:
                return {
                    'success': False,
                    'error': 'Project not found'
                }
            
            website = project.get_website(website_id)
            if not website:
                return {
                    'success': False,
                    'error': 'Website not found in project'
                }
            
            pages = self.page_repo.get_pages_by_website(project_id, website_id)
            
            # Convert pages to dictionaries and add additional info
            pages_data = []
            for page in pages:
                page_data = page.to_dict()
                page_data['page_id'] = page.page_id
                
                # Debug logging
                self.logger.info(f"DEBUG: Page URL: {page.url}, page_id: '{page.page_id}', type: {type(page.page_id)}")
                
                # Add test status
                if page.last_tested:
                    page_data['test_status'] = 'tested'
                    # Check if needs retesting (older than 7 days)
                    days_old = (datetime.datetime.utcnow() - page.last_tested).days
                    page_data['needs_retest'] = days_old > 7
                else:
                    page_data['test_status'] = 'untested'
                    page_data['needs_retest'] = True
                
                pages_data.append(page_data)
            
            return {
                'success': True,
                'website_name': website.name,
                'website_url': website.url,
                'pages': pages_data,
                'total_pages': len(pages_data)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting website pages: {e}")
            return {
                'success': False,
                'error': f'Failed to retrieve pages: {str(e)}'
            }
    
    def get_page_details(self, page_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a page
        
        Args:
            page_id: Page ID
        
        Returns:
            Dictionary with page details or error
        """
        try:
            page = self.page_repo.get_page(page_id)
            if not page:
                return {
                    'success': False,
                    'error': 'Page not found'
                }
            
            # Get project and website info
            project = self.project_repo.get_project(page.project_id)
            website = project.get_website(page.website_id) if project else None
            
            page_data = page.to_dict()
            page_data['page_id'] = page.page_id
            
            # Add project and website context
            if project:
                page_data['project_name'] = project.name
            if website:
                page_data['website_name'] = website.name
                page_data['website_url'] = website.url
            
            # Add test result summary
            from autotest.models.test_result import TestResultRepository
            test_result_repo = TestResultRepository(self.db_connection)
            latest_result = test_result_repo.get_latest_result_for_page(page_id)
            
            if latest_result:
                page_data['latest_test'] = {
                    'test_date': latest_result.test_date,
                    'violations': latest_result.summary.violations if latest_result.summary else 0,
                    'passes': latest_result.summary.passes if latest_result.summary else 0,
                    'incomplete': latest_result.summary.incomplete if latest_result.summary else 0
                }
            else:
                page_data['latest_test'] = None
            
            return {
                'success': True,
                'page': page_data
            }
            
        except Exception as e:
            self.logger.error(f"Error getting page details {page_id}: {e}")
            return {
                'success': False,
                'error': f'Failed to retrieve page details: {str(e)}'
            }
    
    def bulk_add_pages(self, project_id: str, website_id: str, 
                      urls: List[str], discovered_method: str = "manual") -> Dict[str, Any]:
        """
        Add multiple pages to a website at once
        
        Args:
            project_id: Project ID
            website_id: Website ID
            urls: List of URLs to add
            discovered_method: How the pages were discovered
        
        Returns:
            Dictionary with results summary
        """
        try:
            # Validate project and website exist
            project = self.project_repo.get_project(project_id)
            if not project:
                return {
                    'success': False,
                    'error': 'Project not found'
                }
            
            website = project.get_website(website_id)
            if not website:
                return {
                    'success': False,
                    'error': 'Website not found in project'
                }
            
            results = {
                'added': [],
                'skipped': [],
                'errors': []
            }
            
            for url in urls:
                try:
                    # Validate URL
                    if not self._is_valid_url(url):
                        results['errors'].append({
                            'url': url,
                            'error': 'Invalid URL format'
                        })
                        continue
                    
                    # Check if page already exists
                    if self.page_repo.page_exists(project_id, website_id, url):
                        results['skipped'].append({
                            'url': url,
                            'reason': 'Page already exists'
                        })
                        continue
                    
                    # Add the page
                    page_id = self.page_repo.create_page(
                        project_id, website_id, url, "", "", discovered_method
                    )
                    
                    results['added'].append({
                        'url': url,
                        'page_id': page_id
                    })
                    
                except Exception as e:
                    results['errors'].append({
                        'url': url,
                        'error': str(e)
                    })
            
            self.logger.info(f"Bulk added {len(results['added'])} pages to website {website_id}")
            
            return {
                'success': True,
                'results': results,
                'summary': {
                    'total_requested': len(urls),
                    'added': len(results['added']),
                    'skipped': len(results['skipped']),
                    'errors': len(results['errors'])
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error bulk adding pages: {e}")
            return {
                'success': False,
                'error': f'Failed to bulk add pages: {str(e)}'
            }
    
    def get_website_statistics(self, project_id: str, website_id: str) -> Dict[str, Any]:
        """
        Get statistics for a website
        
        Args:
            project_id: Project ID
            website_id: Website ID
        
        Returns:
            Dictionary with website statistics
        """
        try:
            # Validate project and website exist
            project = self.project_repo.get_project(project_id)
            if not project:
                return {
                    'success': False,
                    'error': 'Project not found'
                }
            
            website = project.get_website(website_id)
            if not website:
                return {
                    'success': False,
                    'error': 'Website not found in project'
                }
            
            # Get basic counts
            total_pages = self.page_repo.get_page_count_by_website(project_id, website_id)
            untested_pages = len(self.page_repo.get_untested_pages(project_id, website_id))
            
            # Get pages needing retest
            pages_needing_retest = len(self.page_repo.get_pages_needing_retest(project_id, 7))
            
            # Get all pages for violation summary
            pages = self.page_repo.get_pages_by_website(project_id, website_id)
            
            # Calculate test results summary
            from autotest.models.test_result import TestResultRepository
            test_result_repo = TestResultRepository(self.db_connection)
            
            total_violations = 0
            total_passes = 0
            total_tests = 0
            
            for page in pages:
                if page.page_id:
                    latest_result = test_result_repo.get_latest_result_for_page(page.page_id)
                    if latest_result and latest_result.summary:
                        total_violations += latest_result.summary.violations
                        total_passes += latest_result.summary.passes
                        total_tests += 1
            
            statistics = {
                'website_name': website.name,
                'website_url': website.url,
                'total_pages': total_pages,
                'untested_pages': untested_pages,
                'tested_pages': total_pages - untested_pages,
                'pages_needing_retest': pages_needing_retest,
                'total_violations': total_violations,
                'total_passes': total_passes,
                'total_tests': total_tests,
                'scraping_config': website.scraping_config
            }
            
            return {
                'success': True,
                'statistics': statistics
            }
            
        except Exception as e:
            self.logger.error(f"Error getting website statistics: {e}")
            return {
                'success': False,
                'error': f'Failed to retrieve statistics: {str(e)}'
            }
    
    def _is_valid_url(self, url: str) -> bool:
        """
        Validate URL format
        
        Args:
            url: URL to validate
        
        Returns:
            True if URL is valid, False otherwise
        """
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc]) and result.scheme in ['http', 'https']
        except Exception:
            return False
    
    def update_page_test_results(self, project_id: str, website_id: str, page_id: str, 
                                test_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update a page with accessibility test results
        
        Args:
            project_id: Project ID
            website_id: Website ID
            page_id: Page ID
            test_results: Dictionary containing test results (issues, test_date, etc.)
        
        Returns:
            Dictionary with success status
        """
        try:
            # Verify page exists and belongs to project/website
            page = self.page_repo.get_page(page_id)
            if not page:
                return {
                    'success': False,
                    'error': 'Page not found'
                }
            
            if page.project_id != project_id or page.website_id != website_id:
                return {
                    'success': False,
                    'error': 'Page does not belong to this project/website'
                }
            
            # Prepare update data
            update_data = {}
            
            if 'issues' in test_results:
                update_data['issues'] = test_results['issues']
            
            if 'test_date' in test_results:
                if test_results['test_date'] is None:
                    # Set current timestamp
                    update_data['last_tested'] = datetime.datetime.utcnow()
                else:
                    update_data['last_tested'] = test_results['test_date']
            
            # Update the page
            success = self.page_repo.update(page_id, update_data)
            
            if success:
                self.logger.info(f"Updated test results for page {page_id}")
                return {
                    'success': True,
                    'page_id': page_id
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to update page test results'
                }
        
        except Exception as e:
            self.logger.error(f"Error updating page test results for {page_id}: {e}")
            return {
                'success': False,
                'error': str(e)
            }