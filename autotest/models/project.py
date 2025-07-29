"""
Project model for AutoTest application
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import datetime

from autotest.core.database import BaseRepository, DatabaseConnection


@dataclass
class Website:
    """Website data model"""
    website_id: str
    name: str
    url: str
    created_date: datetime.datetime
    description: str = ""
    scraping_config: Dict[str, Any] = field(default_factory=lambda: {
        'max_pages': 100,
        'depth_limit': 3,
        'include_external': False
    })
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage"""
        return {
            'website_id': self.website_id,
            'name': self.name,
            'url': self.url,
            'created_date': self.created_date,
            'description': self.description,
            'scraping_config': self.scraping_config
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Website':
        """Create Website instance from dictionary"""
        return cls(
            website_id=data['website_id'],
            name=data['name'],
            url=data['url'],
            created_date=data['created_date'],
            description=data.get('description', ''),
            scraping_config=data.get('scraping_config', {
                'max_pages': 100,
                'depth_limit': 3,
                'include_external': False
            })
        )


@dataclass
class Project:
    """Project data model"""
    project_id: Optional[str]
    name: str
    description: str = ""
    created_date: Optional[datetime.datetime] = None
    last_modified: Optional[datetime.datetime] = None
    websites: List[Website] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage"""
        return {
            'name': self.name,
            'description': self.description,
            'created_date': self.created_date,
            'last_modified': self.last_modified,
            'websites': [website.to_dict() for website in self.websites]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Project':
        """Create Project instance from dictionary"""
        websites = [
            Website.from_dict(website_data) 
            for website_data in data.get('websites', [])
        ]
        
        return cls(
            project_id=data.get('_id'),
            name=data['name'],
            description=data.get('description', ''),
            created_date=data.get('created_date'),
            last_modified=data.get('last_modified'),
            websites=websites
        )
    
    def add_website(self, name: str, url: str, description: str = "", scraping_config: Optional[Dict[str, Any]] = None) -> Website:
        """Add a website to the project"""
        from bson import ObjectId
        
        website_id = str(ObjectId())
        website = Website(
            website_id=website_id,
            name=name,
            url=url,
            created_date=datetime.datetime.utcnow(),
            description=description,
            scraping_config=scraping_config or {
                'max_pages': 100,
                'depth_limit': 3,
                'include_external': False
            }
        )
        
        self.websites.append(website)
        return website
    
    def remove_website(self, website_id: str) -> bool:
        """Remove a website from the project"""
        for i, website in enumerate(self.websites):
            if website.website_id == website_id:
                del self.websites[i]
                return True
        return False
    
    def get_website(self, website_id: str) -> Optional[Website]:
        """Get a website by ID"""
        for website in self.websites:
            if website.website_id == website_id:
                return website
        return None


class ProjectRepository(BaseRepository):
    """Repository for Project model operations"""
    
    def __init__(self, db_connection: DatabaseConnection):
        super().__init__(db_connection, 'projects')
    
    def create_project(self, name: str, description: str = "") -> str:
        """
        Create a new project
        
        Args:
            name: Project name
            description: Project description
        
        Returns:
            Created project ID
        """
        project = Project(
            project_id=None,
            name=name,
            description=description
        )
        
        return self.create(project.to_dict())
    
    def get_project(self, project_id: str) -> Optional[Project]:
        """
        Get project by ID
        
        Args:
            project_id: Project ID
        
        Returns:
            Project instance or None if not found
        """
        data = self.get_by_id(project_id)
        if data:
            return Project.from_dict(data)
        return None
    
    def update_project(self, project_id: str, name: Optional[str] = None, 
                      description: Optional[str] = None) -> bool:
        """
        Update project basic information
        
        Args:
            project_id: Project ID
            name: New project name (optional)
            description: New project description (optional)
        
        Returns:
            True if update successful, False otherwise
        """
        update_data = {}
        
        if name is not None:
            update_data['name'] = name
        
        if description is not None:
            update_data['description'] = description
        
        if update_data:
            return self.update(project_id, update_data)
        
        return True
    
    def add_website_to_project(self, project_id: str, name: str, url: str, 
                             description: str = "", scraping_config: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        Add a website to a project
        
        Args:
            project_id: Project ID
            name: Website name
            url: Website URL
            description: Website description
            scraping_config: Scraping configuration
        
        Returns:
            Website ID if successful, None otherwise
        """
        project = self.get_project(project_id)
        if not project:
            return None
        
        website = project.add_website(name, url, description, scraping_config)
        
        if self.update(project_id, {'websites': [w.to_dict() for w in project.websites]}):
            return website.website_id
        
        return None
    
    def remove_website_from_project(self, project_id: str, website_id: str) -> bool:
        """
        Remove a website from a project
        
        Args:
            project_id: Project ID
            website_id: Website ID
        
        Returns:
            True if removal successful, False otherwise
        """
        project = self.get_project(project_id)
        if not project:
            return False
        
        if project.remove_website(website_id):
            return self.update(project_id, {'websites': [w.to_dict() for w in project.websites]})
        
        return False
    
    def get_all_projects(self) -> List[Project]:
        """
        Get all projects
        
        Returns:
            List of Project instances
        """
        projects_data = self.find_all(sort=[('created_date', -1)])
        return [Project.from_dict(data) for data in projects_data]
    
    def get_projects_summary(self) -> List[Dict[str, Any]]:
        """
        Get projects summary (without full website data)
        
        Returns:
            List of project summary dictionaries
        """
        projects = self.get_all_projects()
        summaries = []
        
        for project in projects:
            summaries.append({
                'project_id': project.project_id,
                'name': project.name,
                'description': project.description,
                'created_date': project.created_date,
                'last_modified': project.last_modified,
                'website_count': len(project.websites)
            })
        
        return summaries