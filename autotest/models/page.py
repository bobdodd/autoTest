"""
Page model for AutoTest application
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import datetime

from autotest.core.database import BaseRepository, DatabaseConnection


@dataclass
class Page:
    """Page data model"""
    page_id: Optional[str]
    project_id: str
    website_id: str
    url: str
    title: str = ""
    discovered_method: str = "manual"  # "manual" or "scraping"
    created_date: Optional[datetime.datetime] = None
    last_tested: Optional[datetime.datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage"""
        return {
            'project_id': self.project_id,
            'website_id': self.website_id,
            'url': self.url,
            'title': self.title,
            'discovered_method': self.discovered_method,
            'created_date': self.created_date,
            'last_tested': self.last_tested
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Page':
        """Create Page instance from dictionary"""
        return cls(
            page_id=data.get('_id'),
            project_id=data['project_id'],
            website_id=data['website_id'],
            url=data['url'],
            title=data.get('title', ''),
            discovered_method=data.get('discovered_method', 'manual'),
            created_date=data.get('created_date'),
            last_tested=data.get('last_tested')
        )


class PageRepository(BaseRepository):
    """Repository for Page model operations"""
    
    def __init__(self, db_connection: DatabaseConnection):
        super().__init__(db_connection, 'pages')
    
    def create_page(self, project_id: str, website_id: str, url: str, 
                   title: str = "", discovered_method: str = "manual") -> str:
        """
        Create a new page
        
        Args:
            project_id: Project ID
            website_id: Website ID
            url: Page URL
            title: Page title
            discovered_method: How the page was discovered
        
        Returns:
            Created page ID
        """
        page = Page(
            page_id=None,
            project_id=project_id,
            website_id=website_id,
            url=url,
            title=title,
            discovered_method=discovered_method
        )
        
        return self.create(page.to_dict())
    
    def get_page(self, page_id: str) -> Optional[Page]:
        """
        Get page by ID
        
        Args:
            page_id: Page ID
        
        Returns:
            Page instance or None if not found
        """
        data = self.get_by_id(page_id)
        if data:
            return Page.from_dict(data)
        return None
    
    def update_page(self, page_id: str, title: Optional[str] = None, 
                   url: Optional[str] = None) -> bool:
        """
        Update page information
        
        Args:
            page_id: Page ID
            title: New page title (optional)
            url: New page URL (optional)
        
        Returns:
            True if update successful, False otherwise
        """
        update_data = {}
        
        if title is not None:
            update_data['title'] = title
        
        if url is not None:
            update_data['url'] = url
        
        if update_data:
            return self.update(page_id, update_data)
        
        return True
    
    def update_last_tested(self, page_id: str) -> bool:
        """
        Update the last tested timestamp for a page
        
        Args:
            page_id: Page ID
        
        Returns:
            True if update successful, False otherwise
        """
        return self.update(page_id, {'last_tested': datetime.datetime.utcnow()})
    
    def get_pages_by_project(self, project_id: str) -> List[Page]:
        """
        Get all pages for a project
        
        Args:
            project_id: Project ID
        
        Returns:
            List of Page instances
        """
        pages_data = self.find_all(
            filter_dict={'project_id': project_id},
            sort=[('created_date', -1)]
        )
        return [Page.from_dict(data) for data in pages_data]
    
    def get_pages_by_website(self, project_id: str, website_id: str) -> List[Page]:
        """
        Get all pages for a specific website
        
        Args:
            project_id: Project ID
            website_id: Website ID
        
        Returns:
            List of Page instances
        """
        pages_data = self.find_all(
            filter_dict={
                'project_id': project_id,
                'website_id': website_id
            },
            sort=[('created_date', -1)]
        )
        return [Page.from_dict(data) for data in pages_data]
    
    def get_untested_pages(self, project_id: str, website_id: Optional[str] = None) -> List[Page]:
        """
        Get pages that haven't been tested yet
        
        Args:
            project_id: Project ID
            website_id: Website ID (optional, for specific website)
        
        Returns:
            List of untested Page instances
        """
        filter_dict = {
            'project_id': project_id,
            'last_tested': None
        }
        
        if website_id:
            filter_dict['website_id'] = website_id
        
        pages_data = self.find_all(
            filter_dict=filter_dict,
            sort=[('created_date', -1)]
        )
        return [Page.from_dict(data) for data in pages_data]
    
    def get_pages_needing_retest(self, project_id: str, days_old: int = 7) -> List[Page]:
        """
        Get pages that need retesting (older than specified days)
        
        Args:
            project_id: Project ID
            days_old: Number of days after which a page needs retesting
        
        Returns:
            List of Page instances needing retest
        """
        cutoff_date = datetime.datetime.utcnow() - datetime.timedelta(days=days_old)
        
        filter_dict = {
            'project_id': project_id,
            '$or': [
                {'last_tested': None},
                {'last_tested': {'$lt': cutoff_date}}
            ]
        }
        
        pages_data = self.find_all(
            filter_dict=filter_dict,
            sort=[('last_tested', 1)]
        )
        return [Page.from_dict(data) for data in pages_data]
    
    def delete_pages_by_website(self, project_id: str, website_id: str) -> int:
        """
        Delete all pages for a specific website
        
        Args:
            project_id: Project ID
            website_id: Website ID
        
        Returns:
            Number of pages deleted
        """
        try:
            result = self.collection.delete_many({
                'project_id': project_id,
                'website_id': website_id
            })
            
            self.logger.info(f"Deleted {result.deleted_count} pages for website {website_id}")
            return result.deleted_count
            
        except Exception as e:
            self.logger.error(f"Error deleting pages for website {website_id}: {e}")
            return 0
    
    def delete_pages_by_project(self, project_id: str) -> int:
        """
        Delete all pages for a project
        
        Args:
            project_id: Project ID
        
        Returns:
            Number of pages deleted
        """
        try:
            result = self.collection.delete_many({'project_id': project_id})
            
            self.logger.info(f"Deleted {result.deleted_count} pages for project {project_id}")
            return result.deleted_count
            
        except Exception as e:
            self.logger.error(f"Error deleting pages for project {project_id}: {e}")
            return 0
    
    def page_exists(self, project_id: str, website_id: str, url: str) -> bool:
        """
        Check if a page already exists
        
        Args:
            project_id: Project ID
            website_id: Website ID
            url: Page URL
        
        Returns:
            True if page exists, False otherwise
        """
        return self.count({
            'project_id': project_id,
            'website_id': website_id,
            'url': url
        }) > 0
    
    def get_page_count_by_website(self, project_id: str, website_id: str) -> int:
        """
        Get the number of pages for a specific website
        
        Args:
            project_id: Project ID
            website_id: Website ID
        
        Returns:
            Number of pages
        """
        return self.count({
            'project_id': project_id,
            'website_id': website_id
        })