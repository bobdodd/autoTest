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
                           title: str = "", discovered_method: str = "manual") -> Dict[str, Any]:
        """
        Add a page to a website
        
        Args:
            project_id: Project ID
            website_id: Website ID
            url: Page URL
            title: Page title
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
            page_id = self.page_repo.create_page(
                project_id, website_id, url, title, discovered_method
            )
            
            self.logger.info(f"Added page {url} to website {website_id}")
            
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
            # Verify the page belongs to the correct project and website
            page = self.page_repo.get_page(page_id)
            if not page:
                return {
                    'success': False,
                    'error': 'Page not found'
                }
            
            if page.project_id != project_id or page.website_id != website_id:
                return {
                    'success': False,
                    'error': 'Page does not belong to the specified project and website'
                }
            
            # Delete associated test results first
            from autotest.models.test_result import TestResultRepository
            test_result_repo = TestResultRepository(self.db_connection)
            results_deleted = test_result_repo.delete_results_by_page(page_id)
            
            # Delete the page
            success = self.page_repo.delete(page_id)
            
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
                   title: Optional[str] = None) -> Dict[str, Any]:
        """
        Update page information
        
        Args:
            page_id: Page ID
            url: New page URL (optional)
            title: New page title (optional)
        
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
            
            success = self.page_repo.update_page(page_id, title, url)
            
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
                        project_id, website_id, url, "", discovered_method
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