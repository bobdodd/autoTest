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
Unit tests for AutoTest models
"""

import pytest
from datetime import datetime, timezone
from bson import ObjectId

from autotest.models.project import Project, Website
from autotest.models.page import Page
from autotest.models.test_result import TestResult, AccessibilityViolation, AccessibilityPass, TestSummary

class TestProject:
    """Test cases for Project model"""
    
    def test_project_creation(self):
        """Test basic project creation"""
        project = Project(
            project_id=None,
            name="Test Project",
            description="A test project"
        )
        
        assert project.name == "Test Project"
        assert project.description == "A test project"
        assert project.project_id is None
        assert project.websites == []
    
    def test_project_to_dict(self):
        """Test project serialization to dictionary"""
        project = Project(
            project_id="test_id",
            name="Test Project",
            description="A test project"
        )
        
        project_dict = project.to_dict()
        
        assert project_dict['name'] == "Test Project"
        assert project_dict['description'] == "A test project"
        assert 'websites' in project_dict
        assert project_dict['websites'] == []
    
    def test_project_from_dict(self):
        """Test project creation from dictionary"""
        project_data = {
            '_id': 'test_project_id',
            'name': "Dict Project",
            'description': "Created from dict",
            'created_date': datetime.now(timezone.utc),
            'last_modified': datetime.now(timezone.utc),
            'websites': []
        }
        
        project = Project.from_dict(project_data)
        
        assert project.project_id == 'test_project_id'
        assert project.name == "Dict Project"
        assert project.description == "Created from dict"
        assert len(project.websites) == 0
    
    def test_add_website(self):
        """Test adding a website to project"""
        project = Project(
            project_id="test_id",
            name="Test Project"
        )
        
        website = project.add_website(
            name="Test Website",
            url="https://example.com"
        )
        
        assert len(project.websites) == 1
        assert website.name == "Test Website"
        assert website.url == "https://example.com"
        assert website.website_id is not None
    
    def test_remove_website(self):
        """Test removing a website from project"""
        project = Project(
            project_id="test_id",
            name="Test Project"
        )
        
        website = project.add_website("Test Website", "https://example.com")
        website_id = website.website_id
        
        assert len(project.websites) == 1
        
        result = project.remove_website(website_id)
        assert result is True
        assert len(project.websites) == 0
        
        # Try to remove non-existent website
        result = project.remove_website("nonexistent")
        assert result is False

class TestWebsite:
    """Test cases for Website model"""
    
    def test_website_creation(self):
        """Test basic website creation"""
        website = Website(
            website_id="test_website_id",
            name="Test Website",
            url="https://example.com",
            created_date=datetime.now(timezone.utc)
        )
        
        assert website.website_id == "test_website_id"
        assert website.name == "Test Website"
        assert website.url == "https://example.com"
        assert website.scraping_config is not None
    
    def test_website_with_custom_config(self):
        """Test website creation with custom scraping config"""
        custom_config = {
            'max_pages': 50,
            'depth_limit': 2,
            'include_external': True
        }
        
        website = Website(
            website_id="test_id",
            name="Test Website",
            url="https://example.com",
            created_date=datetime.now(timezone.utc),
            scraping_config=custom_config
        )
        
        assert website.scraping_config['max_pages'] == 50
        assert website.scraping_config['depth_limit'] == 2
        assert website.scraping_config['include_external'] is True
    
    def test_website_to_dict(self):
        """Test website serialization to dictionary"""
        website = Website(
            website_id="test_id",
            name="Test Website",
            url="https://example.com",
            created_date=datetime.now(timezone.utc)
        )
        
        website_dict = website.to_dict()
        
        assert website_dict['website_id'] == "test_id"
        assert website_dict['name'] == "Test Website"
        assert website_dict['url'] == "https://example.com"
        assert 'scraping_config' in website_dict

class TestPage:
    """Test cases for Page model"""
    
    def test_page_creation(self):
        """Test basic page creation"""
        page = Page(
            page_id=None,
            project_id="test_project_id",
            website_id="test_website_id",
            url="https://example.com/test",
            title="Test Page"
        )
        
        assert page.url == "https://example.com/test"
        assert page.title == "Test Page"
        assert page.project_id == "test_project_id"
        assert page.website_id == "test_website_id"
        assert page.discovered_method == "manual"
    
    def test_page_to_dict(self):
        """Test page serialization to dictionary"""
        page = Page(
            page_id="test_page_id",
            project_id="test_project_id",
            website_id="test_website_id",
            url="https://example.com/test",
            title="Test Page"
        )
        
        page_dict = page.to_dict()
        
        assert page_dict['url'] == "https://example.com/test"
        assert page_dict['title'] == "Test Page"
        assert page_dict['project_id'] == "test_project_id"
        assert page_dict['website_id'] == "test_website_id"
    
    def test_page_from_dict(self):
        """Test page creation from dictionary"""
        page_data = {
            '_id': 'test_page_id',
            'project_id': 'test_project_id',
            'website_id': 'test_website_id',
            'url': 'https://example.com/test',
            'title': 'Test Page',
            'discovered_method': 'scraping'
        }
        
        page = Page.from_dict(page_data)
        
        assert page.page_id == 'test_page_id'
        assert page.project_id == 'test_project_id'
        assert page.website_id == 'test_website_id'
        assert page.url == 'https://example.com/test'
        assert page.discovered_method == 'scraping'

class TestAccessibilityViolation:
    """Test cases for AccessibilityViolation model"""
    
    def test_violation_creation(self):
        """Test basic violation creation"""
        violation = AccessibilityViolation(
            violation_id="color-contrast",
            impact="serious",
            description="Text contrast ratio is insufficient",
            help="Ensure text contrast ratio meets WCAG guidelines"
        )
        
        assert violation.violation_id == "color-contrast"
        assert violation.impact == "serious"
        assert violation.description == "Text contrast ratio is insufficient"
        assert violation.nodes == []
    
    def test_violation_to_dict(self):
        """Test violation serialization to dictionary"""
        violation = AccessibilityViolation(
            violation_id="color-contrast",
            impact="serious",
            description="Text contrast ratio is insufficient",
            help="Ensure text contrast ratio meets WCAG guidelines",
            help_url="https://dequeuniversity.com/rules/axe/color-contrast"
        )
        
        violation_dict = violation.to_dict()
        
        assert violation_dict['id'] == "color-contrast"
        assert violation_dict['impact'] == "serious"
        assert violation_dict['helpUrl'] == "https://dequeuniversity.com/rules/axe/color-contrast"
    
    def test_violation_from_dict(self):
        """Test violation creation from dictionary"""
        violation_data = {
            'id': 'alt-text',
            'impact': 'critical',
            'description': 'Image must have alternative text',
            'help': 'Add alt attribute to images',
            'helpUrl': 'https://dequeuniversity.com/rules/axe/alt-text',
            'nodes': [{'target': ['img'], 'html': '<img src="test.jpg">'}]
        }
        
        violation = AccessibilityViolation.from_dict(violation_data)
        
        assert violation.violation_id == 'alt-text'
        assert violation.impact == 'critical'
        assert len(violation.nodes) == 1

class TestTestResult:
    """Test cases for TestResult model"""
    
    def test_test_result_creation(self):
        """Test basic test result creation"""
        violation = AccessibilityViolation(
            violation_id="color-contrast",
            impact="serious",
            description="Text contrast ratio is insufficient",
            help="Ensure text contrast ratio meets WCAG guidelines"
        )
        
        result = TestResult(
            result_id=None,
            page_id="test_page_id",
            violations=[violation]
        )
        
        assert result.page_id == "test_page_id"
        assert len(result.violations) == 1
        assert result.violations[0].violation_id == "color-contrast"
        assert result.summary is not None
        assert result.summary.violations == 1
    
    def test_test_result_summary_calculation(self):
        """Test automatic summary calculation"""
        violations = [
            AccessibilityViolation("rule1", "critical", "desc1", "help1"),
            AccessibilityViolation("rule2", "serious", "desc2", "help2")
        ]
        
        passes = [
            AccessibilityPass("rule3", "desc3", "help3"),
            AccessibilityPass("rule4", "desc4", "help4"),
            AccessibilityPass("rule5", "desc5", "help5")
        ]
        
        result = TestResult(
            result_id=None,
            page_id="test_page_id",
            violations=violations,
            passes=passes,
            incomplete=[{'rule': 'incomplete1'}]
        )
        
        assert result.summary.violations == 2
        assert result.summary.passes == 3
        assert result.summary.incomplete == 1
    
    def test_test_result_to_dict(self):
        """Test test result serialization to dictionary"""
        violation = AccessibilityViolation(
            violation_id="color-contrast",
            impact="serious",
            description="Text contrast ratio is insufficient",
            help="Ensure text contrast ratio meets WCAG guidelines"
        )
        
        result = TestResult(
            result_id="test_result_id",
            page_id="test_page_id",
            violations=[violation]
        )
        
        result_dict = result.to_dict()
        
        assert result_dict['page_id'] == "test_page_id"
        assert len(result_dict['violations']) == 1
        assert result_dict['violations'][0]['id'] == "color-contrast"
        assert 'summary' in result_dict
        assert result_dict['summary']['violations'] == 1
    
    def test_test_result_from_dict(self):
        """Test test result creation from dictionary"""
        result_data = {
            '_id': 'test_result_id',
            'page_id': 'test_page_id',
            'test_date': datetime.now(timezone.utc),
            'violations': [
                {
                    'id': 'color-contrast',
                    'impact': 'serious',
                    'description': 'Poor contrast',
                    'help': 'Improve contrast'
                }
            ],
            'passes': [],
            'incomplete': [],
            'summary': {
                'violations': 1,
                'passes': 0,
                'incomplete': 0
            }
        }
        
        result = TestResult.from_dict(result_data)
        
        assert result.result_id == 'test_result_id'
        assert result.page_id == 'test_page_id'
        assert len(result.violations) == 1
        assert result.violations[0].violation_id == 'color-contrast'
        assert result.summary.violations == 1

class TestTestSummary:
    """Test cases for TestSummary model"""
    
    def test_summary_creation(self):
        """Test basic summary creation"""
        summary = TestSummary(
            violations=5,
            passes=10,
            incomplete=2
        )
        
        assert summary.violations == 5
        assert summary.passes == 10
        assert summary.incomplete == 2
    
    def test_summary_to_dict(self):
        """Test summary serialization to dictionary"""
        summary = TestSummary(violations=3, passes=7, incomplete=1)
        
        summary_dict = summary.to_dict()
        
        assert summary_dict['violations'] == 3
        assert summary_dict['passes'] == 7
        assert summary_dict['incomplete'] == 1
    
    def test_summary_from_dict(self):
        """Test summary creation from dictionary"""
        summary_data = {
            'violations': 4,
            'passes': 8,
            'incomplete': 0
        }
        
        summary = TestSummary.from_dict(summary_data)
        
        assert summary.violations == 4
        assert summary.passes == 8
        assert summary.incomplete == 0

if __name__ == '__main__':
    pytest.main([__file__])