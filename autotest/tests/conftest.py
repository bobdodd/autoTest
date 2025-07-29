"""
Pytest configuration and shared fixtures for AutoTest testing
"""

import pytest
import sys
import os
from pathlib import Path
from unittest.mock import Mock, patch
import tempfile
import shutil

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from autotest.utils.config import Config
from autotest.utils.logger import setup_logger
from autotest.models.project import Project
from autotest.models.page import Page
from autotest.models.test_result import TestResult

# Test configuration
TEST_CONFIG = {
    'mongodb': {
        'uri': 'mongodb://localhost:27017',
        'database': 'autotest_test'
    },
    'logging': {
        'level': 'DEBUG',
        'file': None  # Don't write logs to file during tests
    },
    'selenium': {
        'headless': True,
        'timeout': 10,
        'implicit_wait': 5
    },
    'scraping': {
        'max_pages': 5,
        'max_depth': 2,
        'delay': 0.1,  # Faster for tests
        'respect_robots': False  # Skip robots.txt during tests
    }
}

@pytest.fixture(scope="session")
def test_config():
    """Provide test configuration"""
    return TEST_CONFIG

@pytest.fixture(scope="session")
def logger():
    """Provide logger for tests"""
    return setup_logger('autotest_test', level='DEBUG')

@pytest.fixture(scope="function")
def temp_dir():
    """Create temporary directory for test files"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture(scope="function")
def mock_mongodb():
    """Mock MongoDB database operations"""
    with patch('autotest.core.database.MongoClient') as mock_client:
        mock_db = Mock()
        mock_collection = Mock()
        
        # Configure mock collection
        mock_collection.find.return_value = []
        mock_collection.find_one.return_value = None
        mock_collection.insert_one.return_value = Mock(inserted_id='mock_id')
        mock_collection.update_one.return_value = Mock(modified_count=1)
        mock_collection.delete_one.return_value = Mock(deleted_count=1)
        
        mock_db.__getitem__.return_value = mock_collection
        mock_client.return_value.__getitem__.return_value = mock_db
        
        yield {
            'client': mock_client,
            'db': mock_db,
            'collection': mock_collection
        }

@pytest.fixture(scope="function")
def mock_selenium():
    """Mock Selenium WebDriver"""
    with patch('autotest.core.scraper.webdriver') as mock_webdriver:
        mock_driver = Mock()
        mock_driver.get.return_value = None
        mock_driver.find_elements.return_value = []
        mock_driver.find_element.return_value = Mock()
        mock_driver.page_source = "<html><body><h1>Test Page</h1></body></html>"
        mock_driver.title = "Test Page"
        mock_driver.current_url = "https://example.com"
        
        mock_webdriver.Chrome.return_value = mock_driver
        mock_webdriver.Firefox.return_value = mock_driver
        mock_webdriver.ChromeOptions.return_value = Mock()
        mock_webdriver.FirefoxOptions.return_value = Mock()
        
        yield mock_driver

@pytest.fixture(scope="function")
def sample_project():
    """Create a sample project for testing"""
    return Project(
        name="Test Project",
        description="A test project for unit testing",
        created_by="test_user",
        settings={
            'max_pages': 10,
            'max_depth': 2,
            'follow_external_links': False,
            'check_images': True,
            'check_forms': True,
            'wcag_level': 'AA'
        }
    )

@pytest.fixture(scope="function")
def sample_page():
    """Create a sample page for testing"""
    return Page(
        url="https://example.com/test-page",
        title="Test Page",
        project_id="test_project_id",
        status="discovered",
        metadata={
            'content_type': 'text/html',
            'charset': 'utf-8',
            'language': 'en',
            'word_count': 150,
            'has_forms': True,
            'has_images': True,
            'heading_structure': ['h1', 'h2', 'h2', 'h3']
        }
    )

@pytest.fixture(scope="function")
def sample_test_result():
    """Create a sample test result for testing"""
    return TestResult(
        page_id="test_page_id",
        project_id="test_project_id",
        violations=[
            {
                'rule_id': 'color_contrast',
                'severity': 'serious',
                'impact': 'serious',
                'description': 'Text contrast ratio is insufficient',
                'help_url': 'https://dequeuniversity.com/rules/axe/color-contrast',
                'elements': [
                    {
                        'target': ['button.submit'],
                        'html': '<button class="submit">Submit</button>',
                        'any': [
                            {
                                'id': 'color-contrast',
                                'data': {'fgColor': '#777777', 'bgColor': '#ffffff', 'contrastRatio': 2.85},
                                'relatedNodes': []
                            }
                        ]
                    }
                ]
            }
        ],
        score=75,
        wcag_level='AA',
        test_date='2025-01-25T10:00:00Z',
        test_config={
            'rules_enabled': ['color_contrast', 'alt_text', 'keyboard_navigation'],
            'browser': 'chrome',
            'viewport': {'width': 1920, 'height': 1080}
        }
    )

@pytest.fixture(scope="function")
def sample_html_content():
    """Provide sample HTML content for testing"""
    return '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Test Page</title>
        <style>
            .low-contrast { color: #777; background: #fff; }
            .good-contrast { color: #000; background: #fff; }
        </style>
    </head>
    <body>
        <header>
            <h1>Main Heading</h1>
            <nav aria-label="Main navigation">
                <ul>
                    <li><a href="/">Home</a></li>
                    <li><a href="/about">About</a></li>
                    <li><a href="/contact">Contact</a></li>
                </ul>
            </nav>
        </header>
        
        <main>
            <h2>Content Section</h2>
            <p>This is a paragraph with good contrast.</p>
            <p class="low-contrast">This paragraph has poor contrast.</p>
            
            <img src="image.jpg" alt="Test image">
            <img src="decorative.jpg" alt="">
            <img src="missing-alt.jpg">
            
            <form>
                <label for="name">Name:</label>
                <input type="text" id="name" name="name" required>
                
                <label for="email">Email:</label>
                <input type="email" id="email" name="email">
                
                <input type="text" name="unlabeled">
                
                <button type="submit">Submit</button>
            </form>
            
            <div tabindex="0">Focusable div without role</div>
            <div role="button">Button without keyboard handler</div>
        </main>
        
        <footer>
            <p>&copy; 2025 Test Site</p>
        </footer>
    </body>
    </html>
    '''

@pytest.fixture(scope="function") 
def sample_css_content():
    """Provide sample CSS content for testing"""
    return '''
    /* Test CSS with accessibility issues */
    body {
        font-family: Arial, sans-serif;
        font-size: 10px; /* Too small */
        line-height: 1.0; /* Too tight */
    }
    
    .button {
        background: #ccc;
        color: #ddd; /* Poor contrast */
        border: none;
        padding: 2px 4px; /* Too small touch target */
    }
    
    .button:focus {
        outline: none; /* Removes focus indicator */
    }
    
    .animated {
        animation: spin 0.1s infinite; /* Too fast animation */
    }
    
    @keyframes spin {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }
    
    .hidden-content {
        position: absolute;
        left: -9999px; /* Screen reader accessible hiding */
    }
    
    .good-button {
        background: #0066cc;
        color: #ffffff;
        border: 2px solid #004499;
        padding: 12px 24px;
        min-height: 44px;
        min-width: 44px;
    }
    
    .good-button:focus {
        outline: 2px solid #ffcc00;
        outline-offset: 2px;
    }
    '''

@pytest.fixture(scope="function")
def sample_javascript_content():
    """Provide sample JavaScript content for testing"""
    return '''
    // Test JavaScript with accessibility issues
    
    // Good: Proper keyboard event handling
    document.getElementById('good-button').addEventListener('keydown', function(e) {
        if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            this.click();
        }
    });
    
    // Bad: Click-only handler
    document.getElementById('bad-button').addEventListener('click', function() {
        alert('Button clicked');
    });
    
    // Bad: Focus trap without escape
    function trapFocus(element) {
        element.focus();
        // Missing: escape key handling, focus restoration
    }
    
    // Good: Accessible modal
    function showModal(modalId) {
        const modal = document.getElementById(modalId);
        const focusableElements = modal.querySelectorAll('button, input, select, textarea, [tabindex="0"]');
        const firstElement = focusableElements[0];
        const lastElement = focusableElements[focusableElements.length - 1];
        
        modal.setAttribute('aria-hidden', 'false');
        firstElement.focus();
        
        modal.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                hideModal(modalId);
            }
            
            if (e.key === 'Tab') {
                if (e.shiftKey && document.activeElement === firstElement) {
                    e.preventDefault();
                    lastElement.focus();
                } else if (!e.shiftKey && document.activeElement === lastElement) {
                    e.preventDefault();
                    firstElement.focus();
                }
            }
        });
    }
    
    // Bad: Automatic content changes
    setInterval(function() {
        document.getElementById('content').innerHTML = 'Updated: ' + new Date();
    }, 1000);
    
    // Bad: Motion without respect for prefers-reduced-motion
    function animateElement(element) {
        element.style.animation = 'bounce 2s infinite';
    }
    
    // Good: Respects motion preferences
    function animateElementSafely(element) {
        const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        if (!prefersReducedMotion) {
            element.style.animation = 'bounce 2s infinite';
        }
    }
    '''

# Custom assertions for testing
class AccessibilityAssertions:
    """Custom assertions for accessibility testing"""
    
    @staticmethod
    def assert_violation_present(violations, rule_id):
        """Assert that a specific violation is present"""
        violation_ids = [v.get('rule_id') for v in violations]
        assert rule_id in violation_ids, f"Expected violation '{rule_id}' not found in {violation_ids}"
    
    @staticmethod
    def assert_violation_not_present(violations, rule_id):
        """Assert that a specific violation is not present"""
        violation_ids = [v.get('rule_id') for v in violations]
        assert rule_id not in violation_ids, f"Unexpected violation '{rule_id}' found in {violation_ids}"
    
    @staticmethod
    def assert_score_range(score, min_score, max_score):
        """Assert that accessibility score is within expected range"""
        assert min_score <= score <= max_score, f"Score {score} not in range [{min_score}, {max_score}]"
    
    @staticmethod
    def assert_wcag_level(result, expected_level):
        """Assert WCAG compliance level"""
        assert result.get('wcag_level') == expected_level, f"Expected WCAG level {expected_level}, got {result.get('wcag_level')}"

@pytest.fixture(scope="session")
def accessibility_assertions():
    """Provide accessibility-specific assertions"""
    return AccessibilityAssertions()

# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "e2e: End-to-end tests")
    config.addinivalue_line("markers", "slow: Slow running tests")
    config.addinivalue_line("markers", "accessibility: Accessibility-specific tests")
    config.addinivalue_line("markers", "database: Tests requiring database")
    config.addinivalue_line("markers", "selenium: Tests requiring Selenium WebDriver")