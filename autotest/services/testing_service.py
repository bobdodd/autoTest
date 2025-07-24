"""
Testing Service for AutoTest application.
Handles single page testing, batch testing, and test result management.
"""

import threading
import time
import json
import csv
import io
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import uuid

from autotest.core.accessibility_tester import AccessibilityTester
from autotest.core.project_manager import ProjectManager
from autotest.core.website_manager import WebsiteManager
from autotest.core.scraper import WebScraper
from autotest.utils.logger import LoggerMixin


@dataclass
class TestJob:
    """Represents a testing job"""
    job_id: str
    job_type: str  # 'single_page', 'batch_pages', 'website', 'project'
    status: str    # 'pending', 'running', 'completed', 'failed', 'cancelled'
    progress: int  # 0-100
    total_items: int
    completed_items: int
    failed_items: int
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error_message: Optional[str]
    results: Dict[str, Any]
    
    # Target information
    project_id: Optional[str] = None
    website_id: Optional[str] = None
    page_ids: Optional[List[str]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert job to dictionary for JSON serialization"""
        data = asdict(self)
        # Convert datetime objects to ISO strings
        if self.started_at:
            data['started_at'] = self.started_at.isoformat()
        if self.completed_at:
            data['completed_at'] = self.completed_at.isoformat()
        return data


class TestingService(LoggerMixin):
    """Service for managing accessibility testing operations"""
    
    def __init__(self, config, db_connection):
        """
        Initialize testing service
        
        Args:
            config: Application configuration
            db_connection: Database connection instance
        """
        self.config = config
        self.db_connection = db_connection
        
        # Initialize managers
        self.accessibility_tester = AccessibilityTester(config, db_connection)
        self.project_manager = ProjectManager()
        self.website_manager = WebsiteManager()
        self.scraper = WebScraper(config, db_connection)
        
        # Job management
        self.active_jobs: Dict[str, TestJob] = {}
        self.job_history: List[TestJob] = []
        self.max_concurrent_jobs = config.get('testing.max_concurrent_jobs', 3)
        self.job_timeout = config.get('testing.job_timeout_minutes', 30)
        
        # Background cleanup thread
        self._start_cleanup_thread()
    
    def _start_cleanup_thread(self):
        """Start background thread for job cleanup"""
        def cleanup_worker():
            while True:
                try:
                    self._cleanup_old_jobs()
                    time.sleep(300)  # Check every 5 minutes
                except Exception as e:
                    self.logger.error(f"Error in cleanup thread: {e}")
                    time.sleep(60)  # Wait a minute before retrying
        
        cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        cleanup_thread.start()
    
    def _cleanup_old_jobs(self):
        """Clean up old completed jobs"""
        cutoff_time = datetime.now() - timedelta(hours=24)
        
        # Move old active jobs to history
        jobs_to_remove = []
        for job_id, job in self.active_jobs.items():
            if (job.status in ['completed', 'failed', 'cancelled'] and 
                job.completed_at and job.completed_at < cutoff_time):
                self.job_history.append(job)
                jobs_to_remove.append(job_id)
        
        for job_id in jobs_to_remove:
            del self.active_jobs[job_id]
        
        # Limit history size
        if len(self.job_history) > 100:
            self.job_history = self.job_history[-100:]
    
    def test_single_page(self, page_id: str, callback: Optional[Callable] = None) -> str:
        """
        Test a single page for accessibility issues
        
        Args:
            page_id: ID of the page to test
            callback: Optional callback function for progress updates
        
        Returns:
            Job ID for tracking the test
        """
        job_id = str(uuid.uuid4())
        
        job = TestJob(
            job_id=job_id,
            job_type='single_page',
            status='pending',
            progress=0,
            total_items=1,
            completed_items=0,
            failed_items=0,
            started_at=None,
            completed_at=None,
            error_message=None,
            results={},
            page_ids=[page_id]
        )
        
        self.active_jobs[job_id] = job
        
        # Start testing in background thread
        def test_worker():
            try:
                job.status = 'running'
                job.started_at = datetime.now()
                job.progress = 10
                
                if callback:
                    callback(job)
                
                self.logger.info(f"Starting single page test: {page_id}")
                
                # Run the accessibility test
                result = self.accessibility_tester.test_page(page_id)
                
                job.progress = 90
                if callback:
                    callback(job)
                
                if result['success']:
                    job.status = 'completed'
                    job.completed_items = 1
                    job.results = {
                        'page_results': {page_id: result},
                        'summary': result.get('summary', {})
                    }
                    self.logger.info(f"Single page test completed: {page_id}")
                else:
                    job.status = 'failed'
                    job.failed_items = 1
                    job.error_message = result.get('error', 'Unknown error')
                    self.logger.error(f"Single page test failed: {page_id} - {job.error_message}")
                
                job.progress = 100
                job.completed_at = datetime.now()
                
                if callback:
                    callback(job)
                    
            except Exception as e:
                self.logger.error(f"Error in single page test worker: {e}")
                job.status = 'failed'
                job.failed_items = 1
                job.error_message = str(e)
                job.progress = 100
                job.completed_at = datetime.now()
                
                if callback:
                    callback(job)
        
        thread = threading.Thread(target=test_worker, daemon=True)
        thread.start()
        
        return job_id
    
    def test_multiple_pages(self, page_ids: List[str], callback: Optional[Callable] = None) -> str:
        """
        Test multiple pages for accessibility issues
        
        Args:
            page_ids: List of page IDs to test
            callback: Optional callback function for progress updates
        
        Returns:
            Job ID for tracking the test
        """
        job_id = str(uuid.uuid4())
        
        job = TestJob(
            job_id=job_id,
            job_type='batch_pages',
            status='pending',
            progress=0,
            total_items=len(page_ids),
            completed_items=0,
            failed_items=0,
            started_at=None,
            completed_at=None,
            error_message=None,
            results={'page_results': {}, 'summary': {}},
            page_ids=page_ids
        )
        
        self.active_jobs[job_id] = job
        
        # Start testing in background thread
        def batch_test_worker():
            try:
                job.status = 'running'
                job.started_at = datetime.now()
                
                self.logger.info(f"Starting batch page test: {len(page_ids)} pages")
                
                # Initialize WebDriver once for all tests
                if not self.scraper._setup_driver():
                    raise Exception("Failed to setup web browser")
                
                try:
                    total_violations = 0
                    total_passes = 0
                    
                    for i, page_id in enumerate(page_ids):
                        if job.status == 'cancelled':
                            break
                        
                        try:
                            self.logger.info(f"Testing page {i+1}/{len(page_ids)}: {page_id}")
                            
                            # Test the page using existing driver
                            result = self.accessibility_tester.test_page(page_id, self.scraper.driver)
                            
                            if result['success']:
                                job.results['page_results'][page_id] = result
                                job.completed_items += 1
                                
                                # Update summary
                                summary = result.get('summary', {})
                                total_violations += summary.get('violations', 0)
                                total_passes += summary.get('passes', 0)
                                
                            else:
                                job.failed_items += 1
                                job.results['page_results'][page_id] = {
                                    'success': False,
                                    'error': result.get('error', 'Unknown error')
                                }
                                self.logger.warning(f"Failed to test page {page_id}: {result.get('error')}")
                            
                            # Update progress
                            job.progress = int((i + 1) / len(page_ids) * 100)
                            
                            if callback:
                                callback(job)
                            
                            # Small delay between tests to avoid overwhelming the browser
                            time.sleep(1)
                            
                        except Exception as e:
                            self.logger.error(f"Error testing page {page_id}: {e}")
                            job.failed_items += 1
                            job.results['page_results'][page_id] = {
                                'success': False,
                                'error': str(e)
                            }
                    
                    # Update final summary
                    job.results['summary'] = {
                        'total_pages': len(page_ids),
                        'completed_pages': job.completed_items,
                        'failed_pages': job.failed_items,
                        'total_violations': total_violations,
                        'total_passes': total_passes
                    }
                    
                    if job.status != 'cancelled':
                        job.status = 'completed'
                        self.logger.info(f"Batch page test completed: {job.completed_items}/{len(page_ids)} pages")
                    
                finally:
                    # Clean up WebDriver
                    try:
                        self.scraper.driver.quit()
                    except Exception:
                        pass
                    finally:
                        self.scraper.driver = None
                
                job.progress = 100
                job.completed_at = datetime.now()
                
                if callback:
                    callback(job)
                    
            except Exception as e:
                self.logger.error(f"Error in batch test worker: {e}")
                job.status = 'failed'
                job.error_message = str(e)
                job.progress = 100
                job.completed_at = datetime.now()
                
                if callback:
                    callback(job)
        
        thread = threading.Thread(target=batch_test_worker, daemon=True)
        thread.start()
        
        return job_id
    
    def test_website(self, website_id: str, callback: Optional[Callable] = None) -> str:
        """
        Test all pages in a website
        
        Args:
            website_id: ID of the website to test
            callback: Optional callback function for progress updates
        
        Returns:
            Job ID for tracking the test
        """
        try:
            website = self.website_manager.get_website(website_id)
            if not website:
                raise ValueError(f"Website not found: {website_id}")
            
            page_ids = [page.get('page_id') for page in website.get('pages', []) if page.get('page_id')]
            
            if not page_ids:
                raise ValueError("No pages found in website")
            
            job_id = self.test_multiple_pages(page_ids, callback)
            
            # Update job with website information
            if job_id in self.active_jobs:
                self.active_jobs[job_id].job_type = 'website'
                self.active_jobs[job_id].website_id = website_id
            
            return job_id
            
        except Exception as e:
            self.logger.error(f"Error starting website test: {e}")
            raise
    
    def test_project(self, project_id: str, callback: Optional[Callable] = None) -> str:
        """
        Test all pages in all websites of a project
        
        Args:
            project_id: ID of the project to test
            callback: Optional callback function for progress updates
        
        Returns:
            Job ID for tracking the test
        """
        try:
            project = self.project_manager.get_project(project_id)
            if not project:
                raise ValueError(f"Project not found: {project_id}")
            
            # Collect all page IDs from all websites
            all_page_ids = []
            for website_data in project.get('websites', []):
                website = self.website_manager.get_website(website_data.get('website_id'))
                if website:
                    page_ids = [page.get('page_id') for page in website.get('pages', []) if page.get('page_id')]
                    all_page_ids.extend(page_ids)
            
            if not all_page_ids:
                raise ValueError("No pages found in project")
            
            job_id = self.test_multiple_pages(all_page_ids, callback)
            
            # Update job with project information
            if job_id in self.active_jobs:
                self.active_jobs[job_id].job_type = 'project'
                self.active_jobs[job_id].project_id = project_id
            
            return job_id
            
        except Exception as e:
            self.logger.error(f"Error starting project test: {e}")
            raise
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get status of a testing job
        
        Args:
            job_id: ID of the job
        
        Returns:
            Job status dictionary or None if not found
        """
        job = self.active_jobs.get(job_id)
        if job:
            return job.to_dict()
        
        # Check job history
        for historical_job in self.job_history:
            if historical_job.job_id == job_id:
                return historical_job.to_dict()
        
        return None
    
    def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a running job
        
        Args:
            job_id: ID of the job to cancel
        
        Returns:
            True if job was cancelled, False if not found or already completed
        """
        job = self.active_jobs.get(job_id)
        if job and job.status in ['pending', 'running']:
            job.status = 'cancelled'
            job.completed_at = datetime.now()
            job.progress = 100
            self.logger.info(f"Job cancelled: {job_id}")
            return True
        
        return False
    
    def get_active_jobs(self) -> List[Dict[str, Any]]:
        """
        Get list of all active jobs
        
        Returns:
            List of active job dictionaries
        """
        return [job.to_dict() for job in self.active_jobs.values()]
    
    def get_job_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get job history
        
        Args:
            limit: Maximum number of jobs to return
        
        Returns:
            List of historical job dictionaries
        """
        return [job.to_dict() for job in self.job_history[-limit:]]
    
    def get_testing_statistics(self) -> Dict[str, Any]:
        """
        Get overall testing statistics
        
        Returns:
            Dictionary with testing statistics
        """
        active_count = len(self.active_jobs)
        running_count = len([j for j in self.active_jobs.values() if j.status == 'running'])
        
        # Calculate statistics from recent jobs
        recent_jobs = list(self.active_jobs.values()) + self.job_history[-50:]
        completed_jobs = [j for j in recent_jobs if j.status == 'completed']
        
        total_pages_tested = sum(j.completed_items for j in completed_jobs)
        total_violations_found = 0
        
        for job in completed_jobs:
            if 'summary' in job.results:
                total_violations_found += job.results['summary'].get('total_violations', 0)
        
        return {
            'active_jobs': active_count,
            'running_jobs': running_count,
            'completed_jobs_24h': len([j for j in recent_jobs if j.status == 'completed' and 
                                     j.completed_at and j.completed_at > datetime.now() - timedelta(hours=24)]),
            'total_pages_tested_24h': sum(j.completed_items for j in recent_jobs if j.status == 'completed' and 
                                        j.completed_at and j.completed_at > datetime.now() - timedelta(hours=24)),
            'total_violations_found': total_violations_found,
            'average_violations_per_page': round(total_violations_found / max(total_pages_tested, 1), 2)
        }
    
    def get_violation_details(self, violation_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific violation
        
        Args:
            violation_id: ID of the violation
        
        Returns:
            Detailed violation information or None if not found
        """
        try:
            # This would typically query the database for violation details
            # For now, we'll return mock data with comprehensive violation information
            
            # In a real implementation, this would fetch from the database
            # where violations are stored with their detailed analysis
            
            violation_data = {
                'violation_id': violation_id,
                'rule_id': 'color-contrast',
                'description': 'Elements must have sufficient color contrast',
                'severity': 'serious',
                'wcag_level': '2.1 AA',
                'impact_level': 'high',
                'impact_description': 'Users with visual impairments, including color blindness and low vision, may have difficulty reading text with insufficient contrast.',
                'affected_users': ['Users with low vision', 'Users with color blindness', 'Users in bright environments'],
                'assistive_tech': ['Screen readers', 'High contrast mode', 'Magnification software'],
                'element_count': 3,
                'elements': [
                    {
                        'tag': 'button',
                        'line': 42,
                        'xpath': '/html/body/main/div[2]/form/button',
                        'html': '<button class="btn-primary" type="submit">Submit Form</button>',
                        'context': {
                            'foreground_color': '#888888',
                            'background_color': '#cccccc',
                            'contrast_ratio': '1.9:1',
                            'required_ratio': '4.5:1',
                            'font_size': '14px',
                            'font_weight': 'normal'
                        }
                    },
                    {
                        'tag': 'a',
                        'line': 67,
                        'xpath': '/html/body/nav/ul/li[3]/a',
                        'html': '<a href="/contact" class="nav-link">Contact Us</a>',
                        'context': {
                            'foreground_color': '#999999',
                            'background_color': '#eeeeee',
                            'contrast_ratio': '2.1:1',
                            'required_ratio': '4.5:1',
                            'font_size': '16px',
                            'font_weight': 'normal'
                        }
                    },
                    {
                        'tag': 'span',
                        'line': 89,
                        'xpath': '/html/body/footer/div/span',
                        'html': '<span class="copyright">© 2024 Company Name</span>',
                        'context': {
                            'foreground_color': '#aaaaaa',
                            'background_color': '#f5f5f5',
                            'contrast_ratio': '2.3:1',
                            'required_ratio': '4.5:1',
                            'font_size': '12px',
                            'font_weight': 'normal'
                        }
                    }
                ],
                'fix_steps': [
                    {
                        'description': 'Increase the contrast ratio between text and background colors to meet WCAG AA standards (4.5:1 for normal text, 3:1 for large text).',
                        'code_example': '/* Example: Fix button contrast */\n.btn-primary {\n  color: #ffffff; /* White text */\n  background-color: #0066cc; /* Darker blue background */\n  /* This achieves a 7.2:1 contrast ratio */\n}'
                    },
                    {
                        'description': 'Use online contrast checking tools to verify your color combinations meet accessibility standards.',
                        'code_example': '/* Example: Fix navigation link contrast */\n.nav-link {\n  color: #333333; /* Dark gray text */\n  background-color: #ffffff; /* White background */\n  /* This achieves a 12.6:1 contrast ratio */\n}'
                    },
                    {
                        'description': 'Consider using CSS custom properties to maintain consistent, accessible color schemes across your site.',
                        'code_example': ':root {\n  --text-primary: #212529; /* High contrast text */\n  --text-secondary: #6c757d; /* Medium contrast text */\n  --bg-primary: #ffffff; /* White background */\n  --bg-secondary: #f8f9fa; /* Light gray background */\n}\n\n.copyright {\n  color: var(--text-secondary);\n  background-color: var(--bg-primary);\n}'
                    }
                ],
                'alternative_solutions': [
                    {
                        'title': 'Use semantic color combinations',
                        'description': 'Choose colors that naturally provide good contrast, such as dark text on light backgrounds.',
                        'pros': ['Simple to implement', 'Universally accessible', 'Works well in all contexts'],
                        'cons': ['May limit design creativity', 'Could appear plain or boring']
                    },
                    {
                        'title': 'Implement automatic contrast adjustment',
                        'description': 'Use JavaScript to automatically adjust colors based on contrast ratios.',
                        'pros': ['Dynamic adaptation', 'Maintains design intent', 'Can handle edge cases'],
                        'cons': ['More complex to implement', 'Requires JavaScript', 'May cause visual jumps']
                    }
                ],
                'testing_methods': {
                    'manual': [
                        'Use browser developer tools to inspect color values',
                        'Test the page with different display settings',
                        'View the page in bright sunlight or low-light conditions',
                        'Ask users with visual impairments to test the interface'
                    ],
                    'screen_reader': [
                        'Use NVDA or JAWS to navigate through the problematic elements',
                        'Check if high contrast mode affects the elements properly',
                        'Verify that text remains readable when using screen reader highlighting'
                    ],
                    'keyboard': [
                        'Tab through the interface to check focus indicators',
                        'Ensure focused elements have sufficient contrast',
                        'Test with Windows High Contrast Mode enabled'
                    ]
                },
                'wcag_reference': 'https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum.html',
                'mdn_reference': 'https://developer.mozilla.org/en-US/docs/Web/Accessibility/Understanding_WCAG/Perceivable/Color_contrast',
                'page_id': 'example-page-123',
                'project_id': 'proj-456',
                'website_id': 'site-789'
            }
            
            return violation_data
            
        except Exception as e:
            self.logger.error(f"Error getting violation details: {e}")
            return None
    
    def get_filtered_violations(self, project_id=None, website_id=None, 
                              severity_filter=None, rule_filter=None, wcag_filter=None, 
                              sort_by='severity-desc') -> Dict[str, Any]:
        """
        Get filtered and sorted violations
        
        Args:
            project_id: Filter by project ID
            website_id: Filter by website ID
            severity_filter: List of severity levels to include
            rule_filter: List of rule types to include
            wcag_filter: List of WCAG levels to include
            sort_by: Sorting criteria (field-direction)
        
        Returns:
            Dictionary with filtered violations and statistics
        """
        try:
            # Mock data for comprehensive filtering demonstration
            # In a real implementation, this would query the database
            
            mock_violations = [
                {
                    'violation_id': 'v1',
                    'rule_id': 'color-contrast',
                    'description': 'Elements must have sufficient color contrast',
                    'severity': 'serious',
                    'wcag_level': '2.1 AA',
                    'element_count': 3,
                    'page_id': 'page1',
                    'page_title': 'Home Page',
                    'page_url': 'https://example.com/',
                    'project_id': 'proj-456',
                    'website_id': 'site-789',
                    'impact_description': 'Users with visual impairments may have difficulty reading text with insufficient contrast.',
                    'fix_preview': 'Increase contrast ratio to meet WCAG standards (4.5:1 minimum)'
                },
                {
                    'violation_id': 'v2',
                    'rule_id': 'image-alt',
                    'description': 'Images must have alternative text',
                    'severity': 'critical',
                    'wcag_level': '2.1 A',
                    'element_count': 2,
                    'page_id': 'page2',
                    'page_title': 'About Us',
                    'page_url': 'https://example.com/about',
                    'project_id': 'proj-456',
                    'website_id': 'site-789',
                    'impact_description': 'Screen reader users cannot understand the content or purpose of images without alt text.',
                    'fix_preview': 'Add descriptive alt attributes to all informational images'
                },
                {
                    'violation_id': 'v3',
                    'rule_id': 'heading-order',
                    'description': 'Heading levels should only increase by one',
                    'severity': 'moderate',
                    'wcag_level': '2.1 AA',
                    'element_count': 1,
                    'page_id': 'page3',
                    'page_title': 'Services',
                    'page_url': 'https://example.com/services',
                    'project_id': 'proj-456',
                    'website_id': 'site-789',
                    'impact_description': 'Screen reader users rely on proper heading structure for navigation.',
                    'fix_preview': 'Restructure headings to follow logical order (h1 → h2 → h3)'
                },
                {
                    'violation_id': 'v4',
                    'rule_id': 'form-label',
                    'description': 'Form elements must have labels',
                    'severity': 'serious',
                    'wcag_level': '2.1 A',
                    'element_count': 4,
                    'page_id': 'page4',
                    'page_title': 'Contact Form',
                    'page_url': 'https://example.com/contact',
                    'project_id': 'proj-456',
                    'website_id': 'site-789',
                    'impact_description': 'Users cannot understand what information to enter in form fields.',
                    'fix_preview': 'Associate labels with form controls using for/id attributes'
                },
                {
                    'violation_id': 'v5',
                    'rule_id': 'keyboard-navigation',
                    'description': 'Interactive elements must be keyboard accessible',
                    'severity': 'critical',
                    'wcag_level': '2.1 A',
                    'element_count': 2,
                    'page_id': 'page5',
                    'page_title': 'Product Catalog',
                    'page_url': 'https://example.com/products',
                    'project_id': 'proj-456',
                    'website_id': 'site-789',
                    'impact_description': 'Keyboard users cannot interact with custom controls.',
                    'fix_preview': 'Add tabindex and keyboard event handlers to custom elements'
                },
                {
                    'violation_id': 'v6',
                    'rule_id': 'link-purpose',
                    'description': 'Links must have discernible text',
                    'severity': 'moderate',
                    'wcag_level': '2.1 AA',
                    'element_count': 3,
                    'page_id': 'page1',
                    'page_title': 'Home Page',
                    'page_url': 'https://example.com/',
                    'project_id': 'proj-456',
                    'website_id': 'site-789',
                    'impact_description': 'Screen reader users cannot understand where links will take them.',
                    'fix_preview': 'Replace "click here" with descriptive link text'
                },
                {
                    'violation_id': 'v7',
                    'rule_id': 'aria-labels',
                    'description': 'ARIA labels must be accessible',
                    'severity': 'minor',
                    'wcag_level': '2.1 AAA',
                    'element_count': 1,
                    'page_id': 'page6',
                    'page_title': 'Dashboard',
                    'page_url': 'https://example.com/dashboard',
                    'project_id': 'proj-456',
                    'website_id': 'site-789',
                    'impact_description': 'Assistive technology users may receive incorrect or confusing information.',
                    'fix_preview': 'Ensure ARIA labels are descriptive and accurate'
                },
                {
                    'violation_id': 'v8',
                    'rule_id': 'color-contrast',
                    'description': 'Elements must have sufficient color contrast',
                    'severity': 'serious',
                    'wcag_level': '2.1 AA',
                    'element_count': 2,
                    'page_id': 'page7',
                    'page_title': 'Footer',
                    'page_url': 'https://example.com/footer',
                    'project_id': 'proj-456',
                    'website_id': 'site-789',
                    'impact_description': 'Footer links are difficult to read against the background.',
                    'fix_preview': 'Use darker text colors for better contrast'
                }
            ]
            
            # Apply filters
            filtered_violations = mock_violations.copy()
            
            # Filter by project
            if project_id:
                filtered_violations = [v for v in filtered_violations if v.get('project_id') == project_id]
            
            # Filter by website
            if website_id:
                filtered_violations = [v for v in filtered_violations if v.get('website_id') == website_id]
            
            # Filter by severity
            if severity_filter:
                filtered_violations = [v for v in filtered_violations if v['severity'] in severity_filter]
            
            # Filter by rule type
            if rule_filter:
                filtered_violations = [v for v in filtered_violations if v['rule_id'] in rule_filter]
            
            # Filter by WCAG level
            if wcag_filter:
                filtered_violations = [v for v in filtered_violations if v['wcag_level'] in wcag_filter]
            
            # Apply sorting
            if sort_by:
                field, direction = sort_by.split('-') if '-' in sort_by else (sort_by, 'desc')
                reverse = direction == 'desc'
                
                if field == 'severity':
                    severity_order = {'critical': 4, 'serious': 3, 'moderate': 2, 'minor': 1}
                    filtered_violations.sort(
                        key=lambda x: severity_order.get(x['severity'], 0), 
                        reverse=reverse
                    )
                elif field == 'rule':
                    filtered_violations.sort(key=lambda x: x['rule_id'], reverse=reverse)
                elif field == 'page':
                    filtered_violations.sort(key=lambda x: x['page_title'] or x['page_url'], reverse=reverse)
                elif field == 'elements':
                    filtered_violations.sort(key=lambda x: x['element_count'], reverse=reverse)
            
            # Calculate statistics
            severity_counts = {}
            rule_counts = {}
            wcag_counts = {}
            page_ids = set()
            
            for violation in mock_violations:  # Use unfiltered data for counts
                # Count severities
                severity = violation['severity']
                severity_counts[severity] = severity_counts.get(severity, 0) + 1
                
                # Count rule types
                rule = violation['rule_id']
                rule_counts[rule] = rule_counts.get(rule, 0) + 1
                
                # Count WCAG levels
                wcag = violation['wcag_level']
                wcag_counts[wcag] = wcag_counts.get(wcag, 0) + 1
                
                # Collect unique pages
                if violation.get('page_id'):
                    page_ids.add(violation['page_id'])
            
            return {
                'violations': filtered_violations,
                'total_violations': len(filtered_violations),
                'total_pages': len(page_ids),
                'severity_counts': severity_counts,
                'rule_counts': rule_counts,
                'wcag_counts': wcag_counts
            }
            
        except Exception as e:
            self.logger.error(f"Error getting filtered violations: {e}")
            return {
                'violations': [],
                'total_violations': 0,
                'total_pages': 0,
                'severity_counts': {},
                'rule_counts': {},
                'wcag_counts': {}
            }
    
    def get_progress_data(self, project_id=None, website_id=None, time_range='30d') -> Dict[str, Any]:
        """
        Get progress data for historical comparison
        
        Args:
            project_id: Filter by project ID
            website_id: Filter by website ID
            time_range: Time range for analysis
        
        Returns:
            Dictionary with progress metrics
        """
        try:
            # Mock progress data - in real implementation, this would calculate from historical records
            progress_data = {
                'violations_fixed': 23,
                'new_violations': 7,
                'current_score': 8.4,
                'improvement_rate': '+18%',
                'new_issues_rate': '+7',
                'score_change': '+1.2',
                'critical_issues': 3,
                'testing_frequency': {
                    'current_week': 15,
                    'average_per_week': 12,
                    'trend': 'increasing'
                },
                'top_issues_fixed': [
                    'Color contrast violations reduced by 80%',
                    'Missing alt text issues completely resolved',
                    'Form labeling improved significantly'
                ],
                'areas_for_improvement': [
                    'Focus management on custom components',
                    'ARIA label accuracy and consistency',
                    'Keyboard navigation in complex widgets'
                ]
            }
            
            return progress_data
            
        except Exception as e:
            self.logger.error(f"Error getting progress data: {e}")
            return {}
    
    def get_historical_snapshots(self, project_id=None, website_id=None, time_range='30d') -> List[Dict[str, Any]]:
        """
        Get historical test snapshots for comparison
        
        Args:
            project_id: Filter by project ID
            website_id: Filter by website ID
            time_range: Time range for snapshots
        
        Returns:
            List of historical snapshot data
        """
        try:
            from datetime import datetime, timedelta
            
            # Mock historical snapshots - in real implementation, this would query the database
            snapshots = [
                {
                    'id': 'snap-001',
                    'date': '2024-01-15',
                    'title': 'Major accessibility improvements deployed',
                    'total_violations': 45,
                    'critical': 0,
                    'serious': 5,
                    'moderate': 18,
                    'minor': 22,
                    'change': -12,
                    'project_id': project_id,
                    'website_id': website_id,
                    'highlights': [
                        {
                            'type': 'improvement',
                            'text': 'All critical color contrast issues resolved'
                        },
                        {
                            'type': 'improvement',
                            'text': 'Form accessibility significantly improved'
                        },
                        {
                            'type': 'neutral',
                            'text': 'Minor issues increased due to new content'
                        }
                    ]
                },
                {
                    'id': 'snap-002',
                    'date': '2024-01-08',
                    'title': 'Weekly accessibility audit',
                    'total_violations': 57,
                    'critical': 2,
                    'serious': 8,
                    'moderate': 21,
                    'minor': 26,
                    'change': +5,
                    'project_id': project_id,
                    'website_id': website_id,
                    'highlights': [
                        {
                            'type': 'regression',
                            'text': 'New critical issues found in checkout flow'
                        },
                        {
                            'type': 'improvement',
                            'text': 'Image alt text coverage improved to 95%'
                        }
                    ]
                },
                {
                    'id': 'snap-003',
                    'date': '2024-01-01',
                    'title': 'New Year baseline assessment',
                    'total_violations': 52,
                    'critical': 3,
                    'serious': 12,
                    'moderate': 19,
                    'minor': 18,
                    'change': 0,
                    'project_id': project_id,
                    'website_id': website_id,
                    'highlights': [
                        {
                            'type': 'neutral',
                            'text': 'Baseline established for 2024 improvements'
                        },
                        {
                            'type': 'improvement',
                            'text': 'Testing coverage expanded to mobile views'
                        }
                    ]
                },
                {
                    'id': 'snap-004',
                    'date': '2023-12-25',
                    'title': 'Pre-holiday accessibility check',
                    'total_violations': 68,
                    'critical': 5,
                    'serious': 15,
                    'moderate': 23,
                    'minor': 25,
                    'change': +8,
                    'project_id': project_id,
                    'website_id': website_id,
                    'highlights': [
                        {
                            'type': 'regression',
                            'text': 'Holiday promotions introduced accessibility issues'
                        },
                        {
                            'type': 'neutral',
                            'text': 'Scheduled fixes postponed due to holiday freeze'
                        }
                    ]
                },
                {
                    'id': 'snap-005',
                    'date': '2023-12-18',
                    'title': 'Weekly assessment',
                    'total_violations': 60,
                    'critical': 4,
                    'serious': 13,
                    'moderate': 20,
                    'minor': 23,
                    'change': -3,
                    'project_id': project_id,
                    'website_id': website_id,
                    'highlights': [
                        {
                            'type': 'improvement',
                            'text': 'Gradual progress on keyboard navigation'
                        },
                        {
                            'type': 'neutral',
                            'text': 'Steady state maintained this week'
                        }
                    ]
                },
                {
                    'id': 'snap-006',
                    'date': '2023-12-11',
                    'title': 'Post-deployment assessment',
                    'total_violations': 63,
                    'critical': 6,
                    'serious': 14,
                    'moderate': 22,
                    'minor': 21,
                    'change': +7,
                    'project_id': project_id,
                    'website_id': website_id,
                    'highlights': [
                        {
                            'type': 'regression',
                            'text': 'New features introduced accessibility gaps'
                        },
                        {
                            'type': 'improvement',
                            'text': 'Team training on accessibility best practices completed'
                        }
                    ]
                }
            ]
            
            # Filter by time range if needed
            if time_range != 'all':
                cutoff_date = datetime.now()
                if time_range == '7d':
                    cutoff_date -= timedelta(days=7)
                elif time_range == '30d':
                    cutoff_date -= timedelta(days=30)
                elif time_range == '90d':
                    cutoff_date -= timedelta(days=90)
                elif time_range == '1y':
                    cutoff_date -= timedelta(days=365)
                
                snapshots = [
                    s for s in snapshots 
                    if datetime.strptime(s['date'], '%Y-%m-%d') >= cutoff_date
                ]
            
            return snapshots
            
        except Exception as e:
            self.logger.error(f"Error getting historical snapshots: {e}")
            return []
    
    def get_snapshot_details(self, snapshot_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific snapshot
        
        Args:
            snapshot_id: ID of the snapshot
        
        Returns:
            Detailed snapshot information or None if not found
        """
        try:
            # Get all snapshots and find the requested one
            all_snapshots = self.get_historical_snapshots(time_range='all')
            
            for snapshot in all_snapshots:
                if snapshot['id'] == snapshot_id:
                    # Add additional details for the snapshot
                    snapshot.update({
                        'detailed_breakdown': {
                            'pages_tested': 25,
                            'pages_with_issues': 18,
                            'compliance_score': 7.2,
                            'wcag_aa_compliance': '78%',
                            'wcag_aaa_compliance': '45%'
                        },
                        'top_violations': [
                            {
                                'rule': 'color-contrast',
                                'count': 12,
                                'severity': 'serious',
                                'description': 'Insufficient color contrast'
                            },
                            {
                                'rule': 'image-alt',
                                'count': 8,
                                'severity': 'critical',
                                'description': 'Missing alternative text'
                            },
                            {
                                'rule': 'form-label',
                                'count': 6,
                                'severity': 'serious',
                                'description': 'Form controls missing labels'
                            }
                        ],
                        'affected_pages': [
                            {'url': 'https://example.com/', 'violations': 8},
                            {'url': 'https://example.com/products', 'violations': 12},
                            {'url': 'https://example.com/contact', 'violations': 6}
                        ]
                    })
                    return snapshot
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting snapshot details: {e}")
            return None
    
    def generate_export_data(self, project_id: str, format: str, include_historical: bool = False, 
                           severity_filter: Optional[List[str]] = None, time_range: str = '30d') -> Dict[str, Any]:
        """
        Generate comprehensive export data for a project
        
        Args:
            project_id: ID of the project to export
            format: Export format (json, csv, pdf)
            include_historical: Whether to include historical data
            severity_filter: List of severity levels to include
            time_range: Time range for historical data
        
        Returns:
            Dictionary containing all export data
        """
        try:
            # Get project information
            project = self.project_manager.get_project(project_id)
            if not project:
                raise ValueError(f"Project not found: {project_id}")
            
            # Get current violations data
            violations_data = self.get_filtered_violations(
                project_id=project_id,
                severity_filter=severity_filter
            )
            
            # Get project websites
            websites = []
            for website_data in project.get('websites', []):
                website = self.website_manager.get_website(website_data.get('website_id'))
                if website:
                    websites.append(website)
            
            # Prepare export data structure
            export_data = {
                'metadata': {
                    'project_id': project_id,
                    'project_name': project['name'],
                    'project_description': project.get('description', ''),
                    'export_date': datetime.now().isoformat(),
                    'export_format': format,
                    'time_range': time_range,
                    'include_historical': include_historical,
                    'severity_filter': severity_filter or ['critical', 'serious', 'moderate', 'minor'],
                    'total_websites': len(websites),
                    'total_pages': sum(len(w.get('pages', [])) for w in websites)
                },
                'summary': {
                    'total_violations': violations_data['total_violations'],
                    'severity_breakdown': violations_data['severity_counts'],
                    'rule_breakdown': violations_data['rule_counts'],
                    'wcag_breakdown': violations_data['wcag_counts'],
                    'affected_pages': violations_data['total_pages']
                },
                'websites': [],
                'violations': violations_data['violations'],
                'historical_data': []
            }
            
            # Add website details
            for website in websites:
                website_summary = {
                    'website_id': website['website_id'],
                    'name': website['name'],
                    'base_url': website['base_url'],
                    'total_pages': len(website.get('pages', [])),
                    'pages': website.get('pages', [])
                }
                export_data['websites'].append(website_summary)
            
            # Add historical data if requested
            if include_historical:
                historical_snapshots = self.get_historical_snapshots(
                    project_id=project_id,
                    time_range=time_range
                )
                export_data['historical_data'] = historical_snapshots
                
                # Add progress data
                progress_data = self.get_progress_data(
                    project_id=project_id,
                    time_range=time_range
                )
                export_data['progress_metrics'] = progress_data
            
            return export_data
            
        except Exception as e:
            self.logger.error(f"Error generating export data: {e}")
            raise
    
    def export_json(self, export_data: Dict[str, Any], project_name: str):
        """
        Export data as JSON format
        
        Args:
            export_data: Data to export
            project_name: Name of the project for filename
        
        Returns:
            Flask response with JSON data
        """
        try:
            from flask import make_response, jsonify
            # Clean filename
            safe_name = "".join(c for c in project_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            filename = f"{safe_name}_accessibility_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            # Create response
            response_data = json.dumps(export_data, indent=2, default=str)
            response = make_response(response_data)
            response.headers['Content-Type'] = 'application/json'
            response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error exporting JSON: {e}")
            from flask import jsonify
            return jsonify({'error': f'JSON export failed: {str(e)}'}), 500
    
    def export_csv(self, export_data: Dict[str, Any], project_name: str):
        """
        Export data as CSV format
        
        Args:
            export_data: Data to export
            project_name: Name of the project for filename
        
        Returns:
            Flask response with CSV data
        """
        try:
            from flask import make_response, jsonify
            # Clean filename
            safe_name = "".join(c for c in project_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            filename = f"{safe_name}_accessibility_violations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            
            # Create CSV data
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            headers = [
                'Violation ID', 'Rule ID', 'Description', 'Severity', 'WCAG Level',
                'Page Title', 'Page URL', 'Element Count', 'Impact Description', 'Fix Preview'
            ]
            writer.writerow(headers)
            
            # Write violation data
            for violation in export_data.get('violations', []):
                row = [
                    violation.get('violation_id', ''),
                    violation.get('rule_id', ''),
                    violation.get('description', ''),
                    violation.get('severity', ''),
                    violation.get('wcag_level', ''),
                    violation.get('page_title', ''),
                    violation.get('page_url', ''),
                    violation.get('element_count', 0),
                    violation.get('impact_description', ''),
                    violation.get('fix_preview', '')
                ]
                writer.writerow(row)
            
            # Create response
            csv_data = output.getvalue()
            output.close()
            
            response = make_response(csv_data)
            response.headers['Content-Type'] = 'text/csv'
            response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error exporting CSV: {e}")
            from flask import jsonify
            return jsonify({'error': f'CSV export failed: {str(e)}'}), 500
    
    def export_pdf(self, export_data: Dict[str, Any], project_name: str):
        """
        Export data as PDF format
        
        Args:
            export_data: Data to export
            project_name: Name of the project for filename
        
        Returns:
            Flask response with PDF data
        """
        try:
            from flask import make_response, jsonify
            from reportlab.lib.pagesizes import letter, A4
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.lib import colors
            from reportlab.lib.enums import TA_CENTER, TA_LEFT
            
            # Clean filename
            safe_name = "".join(c for c in project_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            filename = f"{safe_name}_accessibility_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            
            # Create PDF buffer
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1*inch)
            
            # Get styles
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                alignment=TA_CENTER,
                spaceAfter=30
            )
            
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=16,
                spaceAfter=12
            )
            
            # Build PDF content
            story = []
            
            # Title page
            story.append(Paragraph(f"Accessibility Report", title_style))
            story.append(Paragraph(f"Project: {project_name}", styles['Heading2']))
            story.append(Spacer(1, 20))
            
            # Metadata
            metadata = export_data.get('metadata', {})
            metadata_data = [
                ['Export Date:', metadata.get('export_date', 'N/A')],
                ['Total Websites:', str(metadata.get('total_websites', 0))],
                ['Total Pages:', str(metadata.get('total_pages', 0))],
                ['Time Range:', metadata.get('time_range', 'N/A')]
            ]
            
            metadata_table = Table(metadata_data, colWidths=[2*inch, 3*inch])
            metadata_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(metadata_table)
            story.append(Spacer(1, 30))
            
            # Summary
            story.append(Paragraph("Summary", heading_style))
            summary = export_data.get('summary', {})
            
            summary_data = [
                ['Total Violations:', str(summary.get('total_violations', 0))],
                ['Affected Pages:', str(summary.get('affected_pages', 0))]
            ]
            
            # Add severity breakdown
            severity_counts = summary.get('severity_breakdown', {})
            for severity, count in severity_counts.items():
                summary_data.append([f'{severity.title()} Issues:', str(count)])
            
            summary_table = Table(summary_data, colWidths=[2*inch, 1*inch])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightblue),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(summary_table)
            story.append(PageBreak())
            
            # Violations details
            story.append(Paragraph("Detailed Violations", heading_style))
            
            violations = export_data.get('violations', [])
            if violations:
                # Group violations by severity
                severity_order = ['critical', 'serious', 'moderate', 'minor']
                for severity in severity_order:
                    severity_violations = [v for v in violations if v.get('severity') == severity]
                    if severity_violations:
                        story.append(Paragraph(f"{severity.title()} Issues ({len(severity_violations)})", styles['Heading3']))
                        
                        violation_data = [['Rule', 'Description', 'Page', 'Elements']]
                        for violation in severity_violations[:10]:  # Limit to first 10 per severity
                            violation_data.append([
                                violation.get('rule_id', ''),
                                violation.get('description', '')[:50] + ('...' if len(violation.get('description', '')) > 50 else ''),
                                violation.get('page_title', '')[:30] + ('...' if len(violation.get('page_title', '')) > 30 else ''),
                                str(violation.get('element_count', 0))
                            ])
                        
                        violation_table = Table(violation_data, colWidths=[1.2*inch, 2.5*inch, 1.8*inch, 0.8*inch])
                        violation_table.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                            ('FONTSIZE', (0, 0), (-1, 0), 10),
                            ('FONTSIZE', (0, 1), (-1, -1), 8),
                            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                            ('GRID', (0, 0), (-1, -1), 1, colors.black)
                        ]))
                        story.append(violation_table)
                        story.append(Spacer(1, 20))
            
            # Historical data if included
            if export_data.get('include_historical') and export_data.get('historical_data'):
                story.append(PageBreak())
                story.append(Paragraph("Historical Progress", heading_style))
                
                historical_data = export_data.get('historical_data', [])
                if historical_data:
                    hist_data = [['Date', 'Total Issues', 'Critical', 'Serious', 'Moderate', 'Minor']]
                    for snapshot in historical_data[:10]:  # Limit to recent 10
                        hist_data.append([
                            snapshot.get('date', ''),
                            str(snapshot.get('total_violations', 0)),
                            str(snapshot.get('critical', 0)),
                            str(snapshot.get('serious', 0)),
                            str(snapshot.get('moderate', 0)),
                            str(snapshot.get('minor', 0))
                        ])
                    
                    hist_table = Table(hist_data, colWidths=[1*inch, 1*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.8*inch])
                    hist_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 10),
                        ('FONTSIZE', (0, 1), (-1, -1), 8),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black)
                    ]))
                    story.append(hist_table)
            
            # Build PDF
            doc.build(story)
            buffer.seek(0)
            
            # Create response
            response = make_response(buffer.getvalue())
            response.headers['Content-Type'] = 'application/pdf'
            response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            buffer.close()
            return response
            
        except ImportError as e:
            self.logger.error(f"ReportLab not installed: {e}")
            from flask import jsonify
            return jsonify({'error': 'PDF export requires reportlab package. Please install it.'}), 500
        except Exception as e:
            self.logger.error(f"Error exporting PDF: {e}")
            from flask import jsonify
            return jsonify({'error': f'PDF export failed: {str(e)}'}), 500