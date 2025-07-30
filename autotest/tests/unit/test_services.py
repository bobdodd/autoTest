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
Proper unit tests for AutoTest service modules based on actual implementations
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone
import threading
import time

# Import actual service modules
from autotest.services.testing_service import TestingService, TestJob
from autotest.services.scheduler_service import SchedulerService
from autotest.services.history_service import HistoryService
from autotest.services.reporting_service import ReportingService


class TestTestJob:
    """Test cases for TestJob dataclass"""
    
    def test_test_job_creation(self):
        """Test TestJob creation with required fields"""
        job = TestJob(
            job_id="test_job_123",
            job_type="single_page",
            status="pending",
            progress=0,
            total_items=1,
            completed_items=0,
            failed_items=0,
            started_at=None,
            completed_at=None,
            error_message=None,
            results={}
        )
        
        assert job.job_id == "test_job_123"
        assert job.job_type == "single_page"
        assert job.status == "pending"
        assert job.progress == 0
        assert job.total_items == 1
        assert job.completed_items == 0
        assert job.failed_items == 0
        assert job.results == {}
    
    def test_test_job_to_dict(self):
        """Test TestJob serialization to dictionary"""
        start_time = datetime.now()
        job = TestJob(
            job_id="test_job_123",
            job_type="single_page",
            status="running",
            progress=50,
            total_items=2,
            completed_items=1,
            failed_items=0,
            started_at=start_time,
            completed_at=None,
            error_message=None,
            results={"test_result": "data"}
        )
        
        job_dict = job.to_dict()
        
        assert job_dict['job_id'] == "test_job_123"
        assert job_dict['job_type'] == "single_page"
        assert job_dict['status'] == "running"
        assert job_dict['progress'] == 50
        assert job_dict['started_at'] == start_time.isoformat()
        assert job_dict['completed_at'] is None
        assert job_dict['results'] == {"test_result": "data"}


class TestTestingService:
    """Test cases for Testing Service"""
    
    @patch('autotest.services.testing_service.WebScraper')
    @patch('autotest.services.testing_service.WebsiteManager')
    @patch('autotest.services.testing_service.ProjectManager')
    @patch('autotest.services.testing_service.AccessibilityTester')
    def test_initialization(self, mock_tester, mock_project_mgr, mock_website_mgr, mock_scraper):
        """Test TestingService initialization"""
        config = Mock()
        config.get.side_effect = lambda key, default=None: {
            'testing.max_concurrent_jobs': 3,
            'testing.job_timeout_minutes': 30
        }.get(key, default)
        
        mock_db = Mock()
        
        # Mock the dependency constructors
        mock_tester.return_value = Mock()
        mock_project_mgr.return_value = Mock()
        mock_website_mgr.return_value = Mock()
        mock_scraper.return_value = Mock()
        
        with patch.object(TestingService, '_start_cleanup_thread'):
            service = TestingService(config, mock_db)
            
            assert service.config == config
            assert service.db_connection == mock_db
            assert isinstance(service.active_jobs, dict)
            assert isinstance(service.job_history, list)
            assert service.max_concurrent_jobs == 3
            assert service.job_timeout == 30
    
    @patch('autotest.services.testing_service.WebScraper')
    @patch('autotest.services.testing_service.WebsiteManager')
    @patch('autotest.services.testing_service.ProjectManager')
    @patch('autotest.services.testing_service.AccessibilityTester')
    @patch('threading.Thread')
    def test_test_single_page(self, mock_thread, mock_tester, mock_project_mgr, mock_website_mgr, mock_scraper):
        """Test single page testing"""
        config = Mock()
        config.get.return_value = 3
        mock_db = Mock()
        
        # Mock dependencies
        mock_tester.return_value = Mock()
        mock_project_mgr.return_value = Mock()
        mock_website_mgr.return_value = Mock()
        mock_scraper.return_value = Mock()
        
        # Mock thread to prevent actual threading
        mock_thread_instance = Mock()
        mock_thread.return_value = mock_thread_instance
        
        with patch.object(TestingService, '_start_cleanup_thread'):
            service = TestingService(config, mock_db)
            
            page_id = "test_page_123"
            job_id = service.test_single_page(page_id)
            
            assert isinstance(job_id, str)
            assert job_id in service.active_jobs
            
            # Verify job details
            job = service.active_jobs[job_id]
            assert job.job_type == "single_page"
            assert job.status == "pending"
            assert job.total_items == 1
            assert job.page_ids == [page_id]
    
    @patch('autotest.services.testing_service.WebScraper')
    @patch('autotest.services.testing_service.WebsiteManager')
    @patch('autotest.services.testing_service.ProjectManager')
    @patch('autotest.services.testing_service.AccessibilityTester')
    def test_get_job_status(self, mock_tester, mock_project_mgr, mock_website_mgr, mock_scraper):
        """Test getting job status"""
        config = Mock()
        config.get.return_value = 3
        mock_db = Mock()
        
        # Mock dependencies
        mock_tester.return_value = Mock()
        mock_project_mgr.return_value = Mock()
        mock_website_mgr.return_value = Mock()
        mock_scraper.return_value = Mock()
        
        with patch.object(TestingService, '_start_cleanup_thread'):
            service = TestingService(config, mock_db)
            
            # Create a test job manually
            test_job = TestJob(
                job_id="test_job_123",
                job_type="single_page",
                status="running",
                progress=50,
                total_items=1,
                completed_items=0,
                failed_items=0,
                started_at=datetime.now(),
                completed_at=None,
                error_message=None,
                results={}
            )
            service.active_jobs["test_job_123"] = test_job
            
            # Test getting existing job status
            status = service.get_job_status("test_job_123")
            assert status is not None
            assert status['job_id'] == "test_job_123"
            assert status['status'] == "running"
            assert status['progress'] == 50
            
            # Test getting non-existent job status
            status = service.get_job_status("non_existent")
            assert status is None
    
    @patch('autotest.services.testing_service.WebScraper')
    @patch('autotest.services.testing_service.WebsiteManager')
    @patch('autotest.services.testing_service.ProjectManager')
    @patch('autotest.services.testing_service.AccessibilityTester')
    def test_get_active_jobs(self, mock_tester, mock_project_mgr, mock_website_mgr, mock_scraper):
        """Test getting list of active jobs"""
        config = Mock()
        config.get.return_value = 3
        mock_db = Mock()
        
        # Mock dependencies
        mock_tester.return_value = Mock()
        mock_project_mgr.return_value = Mock()
        mock_website_mgr.return_value = Mock()
        mock_scraper.return_value = Mock()
        
        with patch.object(TestingService, '_start_cleanup_thread'):
            service = TestingService(config, mock_db)
            
            # Create test jobs
            job1 = TestJob("job1", "single_page", "running", 25, 1, 0, 0, datetime.now(), None, None, {})
            job2 = TestJob("job2", "batch_pages", "pending", 0, 5, 0, 0, None, None, None, {})
            
            service.active_jobs["job1"] = job1
            service.active_jobs["job2"] = job2
            
            active_jobs = service.get_active_jobs()
            
            assert isinstance(active_jobs, list)
            assert len(active_jobs) == 2
            
            # Verify job data
            job_ids = [job['job_id'] for job in active_jobs]
            assert "job1" in job_ids
            assert "job2" in job_ids
    
    @patch('autotest.services.testing_service.WebScraper')
    @patch('autotest.services.testing_service.WebsiteManager')
    @patch('autotest.services.testing_service.ProjectManager')
    @patch('autotest.services.testing_service.AccessibilityTester')
    def test_cancel_job(self, mock_tester, mock_project_mgr, mock_website_mgr, mock_scraper):
        """Test cancelling a job"""
        config = Mock()
        config.get.return_value = 3
        mock_db = Mock()
        
        # Mock dependencies
        mock_tester.return_value = Mock()
        mock_project_mgr.return_value = Mock()
        mock_website_mgr.return_value = Mock()
        mock_scraper.return_value = Mock()
        
        with patch.object(TestingService, '_start_cleanup_thread'):
            service = TestingService(config, mock_db)
            
            # Create a test job
            test_job = TestJob("job123", "single_page", "running", 50, 1, 0, 0, datetime.now(), None, None, {})
            service.active_jobs["job123"] = test_job
            
            # Test cancelling existing job
            result = service.cancel_job("job123")
            assert result is True
            assert service.active_jobs["job123"].status == "cancelled"
            
            # Test cancelling non-existent job
            result = service.cancel_job("non_existent")
            assert result is False


class TestSchedulerService:
    """Test cases for Scheduler Service"""
    
    @patch('threading.Thread')
    def test_initialization(self, mock_thread):
        """Test SchedulerService initialization"""
        config = Mock()
        config.get.side_effect = lambda key, default=None: {
            'scheduler.check_interval': 60,
            'scheduler.max_concurrent_jobs': 2
        }.get(key, default)
        
        mock_db = Mock()
        
        # Mock thread to prevent actual thread creation
        mock_thread_instance = Mock()
        mock_thread.return_value = mock_thread_instance
        
        service = SchedulerService(config, mock_db)
        
        assert service.config == config
        assert service.db_connection == mock_db
        assert hasattr(service, 'schedules')
        assert isinstance(service.schedules, dict)
    
    @patch('threading.Thread')
    def test_create_schedule(self, mock_thread):
        """Test creating a schedule"""
        config = Mock()
        config.get.return_value = 60
        mock_db = Mock()
        
        mock_thread_instance = Mock()
        mock_thread.return_value = mock_thread_instance
        
        service = SchedulerService(config, mock_db)
        
        schedule_id = service.create_schedule(
            project_id="test_project",
            schedule_type="daily",
            frequency=1
        )
        
        assert isinstance(schedule_id, str)
        assert schedule_id in service.schedules
        
        # Verify schedule details
        schedule = service.schedules[schedule_id]
        assert schedule['project_id'] == "test_project"
        assert schedule['schedule_type'] == "daily"
        assert schedule['frequency'] == 1


class TestHistoryService:
    """Test cases for History Service"""
    
    def test_initialization(self):
        """Test HistoryService initialization"""
        config = Mock()
        mock_db = Mock()
        
        service = HistoryService(config, mock_db)
        
        assert service.config == config
        assert service.db_connection == mock_db
    
    def test_create_snapshot(self):
        """Test creating a project snapshot"""
        config = Mock()
        mock_db = Mock()
        
        service = HistoryService(config, mock_db)
        
        snapshot_id = service.create_snapshot(
            project_id="test_project",
            snapshot_type="manual"
        )
        
        assert isinstance(snapshot_id, str)


class TestReportingService:
    """Test cases for Reporting Service"""
    
    def test_initialization(self):
        """Test ReportingService initialization"""
        config = Mock()
        mock_db = Mock()
        
        service = ReportingService(config, mock_db)
        
        assert service.config == config
        assert service.db_connection == mock_db
    
    def test_generate_summary_report(self):
        """Test generating summary report"""
        config = Mock()
        mock_db = Mock()
        
        service = ReportingService(config, mock_db)
        
        # Mock the _get_project_summary method that likely exists
        with patch.object(service, '_get_project_summary', return_value={"summary": "data"}):
            report = service._generate_executive_summary("test_project")
            
            assert isinstance(report, dict)
            assert "summary" in report
    
    def test_export_html(self):
        """Test exporting report as HTML"""
        config = Mock()
        mock_db = Mock()
        
        service = ReportingService(config, mock_db)
        
        # Test export with mock data
        mock_report_data = {
            "title": "Test Report",
            "violations": [],
            "summary": {"total_pages": 5, "violations": 10}
        }
        
        html_output = service.export_html(mock_report_data)
        
        assert isinstance(html_output, str)
        assert "Test Report" in html_output
    
    def test_export_json(self):
        """Test exporting report as JSON"""
        config = Mock()
        mock_db = Mock()
        
        service = ReportingService(config, mock_db)
        
        # Test export with mock data
        mock_report_data = {
            "title": "Test Report",
            "violations": [],
            "summary": {"total_pages": 5, "violations": 10}
        }
        
        json_output = service.export_json(mock_report_data)
        
        assert isinstance(json_output, str)
        # Verify it's valid JSON by attempting to parse it
        import json
        parsed = json.loads(json_output)
        assert parsed["title"] == "Test Report"