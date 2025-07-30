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
Project management module for AutoTest application
"""

from typing import Dict, List, Optional, Any
import datetime

from autotest.core.database import DatabaseConnection
from autotest.models.project import Project, ProjectRepository, Website
from autotest.models.page import PageRepository
from autotest.models.test_result import TestResultRepository
from autotest.utils.logger import LoggerMixin


class ProjectManager(LoggerMixin):
    """Main project management class with business logic"""
    
    def __init__(self, db_connection: DatabaseConnection):
        """
        Initialize project manager
        
        Args:
            db_connection: Database connection instance
        """
        self.db_connection = db_connection
        self.project_repo = ProjectRepository(db_connection)
        self.page_repo = PageRepository(db_connection)
        self.test_result_repo = TestResultRepository(db_connection)
    
    def create_project(self, name: str, description: str = "") -> Dict[str, Any]:
        """
        Create a new project
        
        Args:
            name: Project name
            description: Project description
        
        Returns:
            Dictionary with success status and project details
        """
        try:
            # Check if project name already exists
            existing_projects = self.project_repo.find_all({'name': name})
            if existing_projects:
                return {
                    'success': False,
                    'error': f'Project with name "{name}" already exists'
                }
            
            project_id = self.project_repo.create_project(name, description)
            
            self.logger.info(f"Created new project: {name} (ID: {project_id})")
            
            return {
                'success': True,
                'project_id': project_id,
                'message': f'Project "{name}" created successfully'
            }
            
        except Exception as e:
            self.logger.error(f"Error creating project: {e}")
            return {
                'success': False,
                'error': f'Failed to create project: {str(e)}'
            }
    
    def get_project(self, project_id: str) -> Dict[str, Any]:
        """
        Get project by ID
        
        Args:
            project_id: Project ID
        
        Returns:
            Dictionary with project data or error
        """
        try:
            project = self.project_repo.get_project(project_id)
            
            if not project:
                return {
                    'success': False,
                    'error': 'Project not found'
                }
            
            # Get additional statistics
            total_pages = self.page_repo.count({'project_id': project_id})
            
            project_data = project.to_dict()
            project_data['project_id'] = project.project_id
            project_data['total_pages'] = total_pages
            
            return {
                'success': True,
                'project': project_data
            }
            
        except Exception as e:
            self.logger.error(f"Error getting project {project_id}: {e}")
            return {
                'success': False,
                'error': f'Failed to retrieve project: {str(e)}'
            }
    
    def update_project(self, project_id: str, name: Optional[str] = None, 
                      description: Optional[str] = None) -> Dict[str, Any]:
        """
        Update project information
        
        Args:
            project_id: Project ID
            name: New project name (optional)
            description: New project description (optional)
        
        Returns:
            Dictionary with success status and message
        """
        try:
            # Check if project exists
            existing_project = self.project_repo.get_project(project_id)
            if not existing_project:
                return {
                    'success': False,
                    'error': 'Project not found'
                }
            
            # Check if new name conflicts with existing projects
            if name and name != existing_project.name:
                existing_projects = self.project_repo.find_all({'name': name})
                if existing_projects:
                    return {
                        'success': False,
                        'error': f'Project with name "{name}" already exists'
                    }
            
            success = self.project_repo.update_project(project_id, name, description)
            
            if success:
                self.logger.info(f"Updated project {project_id}")
                return {
                    'success': True,
                    'message': 'Project updated successfully'
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to update project'
                }
                
        except Exception as e:
            self.logger.error(f"Error updating project {project_id}: {e}")
            return {
                'success': False,
                'error': f'Failed to update project: {str(e)}'
            }
    
    def delete_project(self, project_id: str) -> Dict[str, Any]:
        """
        Delete project and all associated data
        
        Args:
            project_id: Project ID
        
        Returns:
            Dictionary with success status and message
        """
        try:
            # Check if project exists
            project = self.project_repo.get_project(project_id)
            if not project:
                return {
                    'success': False,
                    'error': 'Project not found'
                }
            
            # Get all pages for the project to delete test results
            pages = self.page_repo.get_pages_by_project(project_id)
            
            # Delete all test results for pages in this project
            total_results_deleted = 0
            for page in pages:
                if page.page_id:
                    results_deleted = self.test_result_repo.delete_results_by_page(page.page_id)
                    total_results_deleted += results_deleted
            
            # Delete all pages for this project
            pages_deleted = self.page_repo.delete_pages_by_project(project_id)
            
            # Delete the project itself
            project_deleted = self.project_repo.delete(project_id)
            
            if project_deleted:
                self.logger.info(f"Deleted project {project_id} with {pages_deleted} pages and {total_results_deleted} test results")
                return {
                    'success': True,
                    'message': f'Project "{project.name}" deleted successfully',
                    'deleted_pages': pages_deleted,
                    'deleted_results': total_results_deleted
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to delete project'
                }
                
        except Exception as e:
            self.logger.error(f"Error deleting project {project_id}: {e}")
            return {
                'success': False,
                'error': f'Failed to delete project: {str(e)}'
            }
    
    def list_projects(self) -> Dict[str, Any]:
        """
        Get list of all projects with summary information
        
        Returns:
            Dictionary with project list or error
        """
        try:
            projects_summary = self.project_repo.get_projects_summary()
            
            # Add additional statistics for each project
            for project_summary in projects_summary:
                project_id = project_summary['project_id']
                
                # Get page count
                page_count = self.page_repo.count({'project_id': project_id})
                project_summary['page_count'] = page_count
                
                # Get latest test results summary
                if page_count > 0:
                    violation_summary = self.test_result_repo.get_violation_summary_by_project(project_id)
                    project_summary['total_violations'] = violation_summary['total_violations']
                    project_summary['total_tests'] = violation_summary['total_tests']
                else:
                    project_summary['total_violations'] = 0
                    project_summary['total_tests'] = 0
            
            return {
                'success': True,
                'projects': projects_summary
            }
            
        except Exception as e:
            self.logger.error(f"Error listing projects: {e}")
            return {
                'success': False,
                'error': f'Failed to retrieve projects: {str(e)}'
            }
    
    def add_website_to_project(self, project_id: str, name: str, url: str, 
                             description: str = "", scraping_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Add a website to a project
        
        Args:
            project_id: Project ID
            name: Website name
            url: Website URL
            scraping_config: Scraping configuration
        
        Returns:
            Dictionary with success status and website details
        """
        try:
            # Validate URL format
            if not url.startswith(('http://', 'https://')):
                return {
                    'success': False,
                    'error': 'URL must start with http:// or https://'
                }
            
            website_id = self.project_repo.add_website_to_project(
                project_id, name, url, description, scraping_config
            )
            
            if website_id:
                self.logger.info(f"Added website {name} to project {project_id}")
                return {
                    'success': True,
                    'website_id': website_id,
                    'message': f'Website "{name}" added successfully'
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to add website to project'
                }
                
        except Exception as e:
            self.logger.error(f"Error adding website to project {project_id}: {e}")
            return {
                'success': False,
                'error': f'Failed to add website: {str(e)}'
            }
    
    def remove_website_from_project(self, project_id: str, website_id: str) -> Dict[str, Any]:
        """
        Remove a website from a project
        
        Args:
            project_id: Project ID
            website_id: Website ID
        
        Returns:
            Dictionary with success status and message
        """
        try:
            # Delete all pages for this website
            pages_deleted = self.page_repo.delete_pages_by_website(project_id, website_id)
            
            # Delete all test results for pages in this website
            pages = self.page_repo.get_pages_by_website(project_id, website_id)
            total_results_deleted = 0
            for page in pages:
                if page.page_id:
                    results_deleted = self.test_result_repo.delete_results_by_page(page.page_id)
                    total_results_deleted += results_deleted
            
            # Remove website from project
            success = self.project_repo.remove_website_from_project(project_id, website_id)
            
            if success:
                self.logger.info(f"Removed website {website_id} from project {project_id}")
                return {
                    'success': True,
                    'message': 'Website removed successfully',
                    'deleted_pages': pages_deleted,
                    'deleted_results': total_results_deleted
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to remove website from project'
                }
                
        except Exception as e:
            self.logger.error(f"Error removing website {website_id} from project {project_id}: {e}")
            return {
                'success': False,
                'error': f'Failed to remove website: {str(e)}'
            }
    
    def get_project_statistics(self, project_id: str) -> Dict[str, Any]:
        """
        Get detailed statistics for a project
        
        Args:
            project_id: Project ID
        
        Returns:
            Dictionary with project statistics
        """
        try:
            project = self.project_repo.get_project(project_id)
            if not project:
                return {
                    'success': False,
                    'error': 'Project not found'
                }
            
            # Basic counts
            total_websites = len(project.websites)
            total_pages = self.page_repo.count({'project_id': project_id})
            
            # Test results summary
            violation_summary = self.test_result_repo.get_violation_summary_by_project(project_id)
            
            # Pages by website
            pages_by_website = {}
            for website in project.websites:
                page_count = self.page_repo.get_page_count_by_website(project_id, website.website_id)
                pages_by_website[website.name] = page_count
            
            # Untested pages
            untested_pages = len(self.page_repo.get_untested_pages(project_id))
            
            return {
                'success': True,
                'statistics': {
                    'project_name': project.name,
                    'total_websites': total_websites,
                    'total_pages': total_pages,
                    'untested_pages': untested_pages,
                    'pages_by_website': pages_by_website,
                    'total_violations': violation_summary['total_violations'],
                    'total_passes': violation_summary['total_passes'],
                    'total_tests': violation_summary['total_tests'],
                    'violations_by_impact': violation_summary['violations_by_impact']
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error getting project statistics {project_id}: {e}")
            return {
                'success': False,
                'error': f'Failed to retrieve statistics: {str(e)}'
            }