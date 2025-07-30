# AutoTest Developer Guide

Complete guide for developers working on the AutoTest accessibility testing platform.

## Table of Contents

1. [Development Environment Setup](#development-environment-setup)
2. [Architecture Overview](#architecture-overview)
3. [Codebase Structure](#codebase-structure)
4. [Development Workflow](#development-workflow)
5. [Testing Guidelines](#testing-guidelines)
6. [Code Standards](#code-standards)
7. [Database Schema](#database-schema)
8. [API Development](#api-development)
9. [Frontend Development](#frontend-development)
10. [Debugging Guide](#debugging-guide)
11. [Performance Guidelines](#performance-guidelines)
12. [Contributing Guidelines](#contributing-guidelines)

## Development Environment Setup

### Prerequisites
- Python 3.8+
- MongoDB 4.4+
- Git
- Modern IDE (VS Code, PyCharm recommended)

### Quick Setup
```bash
# Clone repository
git clone https://github.com/bobdodd/autoTest.git
cd autoTest

# Setup virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Start development server
python -m autotest.web.app
```

### Development Dependencies
```text
# requirements-dev.txt
pytest==7.4.3
pytest-cov==4.1.0
pytest-mock==3.12.0
black==23.11.0
flake8==6.1.0
mypy==1.7.1
sphinx==7.2.6
pre-commit==3.5.0
```

## Architecture Overview

### High-Level Architecture
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Web Layer     │    │   Service Layer  │    │   Data Layer    │
│                 │    │                  │    │                 │
│ • Flask App     │◄──►│ • Testing Svc    │◄──►│ • MongoDB       │
│ • Routes        │    │ • Report Svc     │    │ • Collections   │
│ • Templates     │    │ • Scheduler Svc  │    │ • Indexes       │
│ • Static Files  │    │ • History Svc    │    │ • Queries       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Core Layer    │    │   Utils Layer    │    │   Models Layer  │
│                 │    │                  │    │                 │
│ • Accessibility │    │ • Config         │    │ • Project       │
│ • Scraper       │    │ • Logger         │    │ • Page          │
│ • Database      │    │ • Validators     │    │ • TestResult    │
│ • Managers      │    │ • Helpers        │    │ • Collections   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Component Responsibilities

#### Web Layer (`autotest/web/`)
- **Flask Application**: Main web server setup
- **Routes**: HTTP endpoints and request handling
- **Templates**: Jinja2 HTML templates
- **Static Files**: CSS, JavaScript, images

#### Service Layer (`autotest/services/`)
- **Testing Service**: Orchestrates accessibility testing
- **Reporting Service**: Generates reports and exports
- **Scheduler Service**: Manages automated testing
- **History Service**: Tracks changes over time

#### Core Layer (`autotest/core/`)
- **Accessibility Tester**: Core testing engine
- **Scraper**: Website crawling and page discovery
- **Database**: MongoDB connection and operations
- **Managers**: Business logic for projects and websites

#### Utils Layer (`autotest/utils/`)
- **Config**: Configuration management
- **Logger**: Centralized logging
- **Validators**: Input validation utilities

#### Models Layer (`autotest/models/`)
- **Data Models**: MongoDB document models
- **Schemas**: Data validation schemas
- **Collections**: Database collection interfaces

## Codebase Structure

```
autotest/
├── __init__.py
├── main.py                     # Application entry point
├── core/                       # Core business logic
│   ├── __init__.py
│   ├── accessibility_tester.py # Main testing engine
│   ├── database.py            # MongoDB operations
│   ├── project_manager.py     # Project business logic
│   ├── scraper.py            # Website crawling
│   └── website_manager.py    # Website management
├── models/                    # Data models
│   ├── __init__.py
│   ├── page.py              # Page model
│   ├── project.py           # Project model
│   └── test_result.py       # Test result model
├── services/                 # Service layer
│   ├── history_service.py   # Historical data
│   ├── reporting_service.py # Report generation
│   ├── scheduler_service.py # Test scheduling
│   └── testing_service.py   # Testing orchestration
├── testing/                 # Testing framework
│   ├── checkers/           # Accessibility checkers
│   ├── css/               # CSS analysis
│   ├── javascript/        # JS analysis
│   ├── reporters/         # Result reporting
│   ├── rules/            # WCAG rules
│   └── scenarios/        # Test scenarios
├── utils/                   # Utilities
│   ├── __init__.py
│   ├── config.py          # Configuration
│   └── logger.py          # Logging
├── web/                     # Web interface
│   ├── __init__.py
│   ├── app.py            # Flask application
│   ├── routes/           # HTTP routes
│   ├── static/           # Static assets
│   └── templates/        # HTML templates
└── tests/                   # Test suite
    ├── conftest.py         # Test configuration
    ├── fixtures/           # Test data
    └── unit/              # Unit tests
```

## Development Workflow

### 1. Feature Development
```bash
# Create feature branch
git checkout -b feature/accessibility-enhancement

# Make changes with tests
# Run tests frequently
pytest autotest/tests/

# Check code quality
black autotest/
flake8 autotest/
mypy autotest/

# Commit with clear messages
git commit -m "Add enhanced color contrast checking"
```

### 2. Testing Workflow
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=autotest --cov-report=html

# Run specific test file
pytest autotest/tests/unit/test_accessibility_rules.py

# Run with verbose output
pytest -v
```

### 3. Code Quality Checks
```bash
# Format code
black autotest/

# Check style
flake8 autotest/

# Type checking
mypy autotest/

# Security check
bandit -r autotest/
```

## Testing Guidelines

### Test Structure
```python
# autotest/tests/unit/test_example.py
import pytest
from unittest.mock import Mock, patch
from autotest.core.accessibility_tester import AccessibilityTester

class TestAccessibilityTester:
    """Test accessibility testing functionality"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.config = Mock()
        self.tester = AccessibilityTester(self.config)
    
    def test_color_contrast_detection(self):
        """Test color contrast detection"""
        # Arrange
        html = '<div style="color: #000; background: #fff;">Text</div>'
        
        # Act
        results = self.tester.check_color_contrast(html)
        
        # Assert
        assert len(results) == 0  # No violations
        assert results.is_valid
    
    @patch('autotest.core.scraper.requests.get')
    def test_page_scraping(self, mock_get):
        """Test page scraping with mocked requests"""
        # Arrange
        mock_response = Mock()
        mock_response.text = '<html><body>Test</body></html>'
        mock_get.return_value = mock_response
        
        # Act
        content = self.tester.scrape_page('http://example.com')
        
        # Assert
        assert 'Test' in content
        mock_get.assert_called_once()
```

### Test Categories

#### Unit Tests
- Test individual functions and methods
- Mock external dependencies
- Fast execution (<1s per test)
- High coverage (>90%)

#### Integration Tests
- Test component interactions
- Use test database
- Moderate execution time (<10s per test)
- Focus on critical paths

#### End-to-End Tests
- Test complete user workflows
- Use real browser automation
- Slower execution (<60s per test)
- Cover major user scenarios

### Test Data Management
```python
# autotest/tests/fixtures/sample_data.py
class SampleData:
    """Test data fixtures"""
    
    @staticmethod
    def valid_html():
        return '''
        <html>
            <head><title>Test Page</title></head>
            <body>
                <h1>Main Heading</h1>
                <p>Content paragraph</p>
            </body>
        </html>
        '''
    
    @staticmethod
    def invalid_html():
        return '''
        <html>
            <body>
                <div style="color: #ccc; background: #ddd;">
                    Low contrast text
                </div>
            </body>
        </html>
        '''
```

## Code Standards

### Python Style Guide

#### Formatting (Black)
```python
# Good
def check_accessibility(page_content: str, rules: List[str]) -> TestResult:
    """Check accessibility compliance for page content."""
    results = []
    
    for rule in rules:
        violations = apply_rule(page_content, rule)
        results.extend(violations)
    
    return TestResult(violations=results)

# Avoid
def check_accessibility(page_content,rules):
    results=[]
    for rule in rules:
        violations=apply_rule(page_content,rule)
        results.extend(violations)
    return TestResult(violations=results)
```

#### Type Hints
```python
from typing import List, Dict, Optional, Union
from datetime import datetime

def generate_report(
    project_id: str,
    test_results: List[TestResult],
    format_type: str = "html"
) -> Optional[Dict[str, Union[str, int]]]:
    """Generate accessibility report."""
    pass
```

#### Documentation
```python
def analyze_color_contrast(element: BeautifulSoup) -> ContrastResult:
    """
    Analyze color contrast for accessibility compliance.
    
    Args:
        element: BeautifulSoup element to analyze
        
    Returns:
        ContrastResult containing:
        - contrast_ratio: Calculated contrast ratio
        - passes_aa: Whether passes WCAG AA (4.5:1)
        - passes_aaa: Whether passes WCAG AAA (7:1)
        - foreground_color: Computed foreground color
        - background_color: Computed background color
        
    Raises:
        ValueError: If element has no computable colors
        
    Example:
        >>> element = soup.find('p')
        >>> result = analyze_color_contrast(element)
        >>> print(f"Contrast ratio: {result.contrast_ratio}")
    """
    pass
```

### Database Conventions

#### Collection Naming
- Use snake_case: `test_results`, `scheduled_tests`
- Use plural nouns: `projects`, `pages`
- Be descriptive: `accessibility_violations`

#### Document Structure
```python
# Good document structure
{
    "_id": ObjectId("..."),
    "project_id": "proj_123",
    "created_at": ISODate("..."),
    "updated_at": ISODate("..."),
    "status": "active",
    "metadata": {
        "version": 1,
        "source": "web_ui"
    }
}
```

#### Index Strategy
```python
# Essential indexes
db.test_results.createIndex({"project_id": 1, "created_at": -1})
db.pages.createIndex({"website_id": 1, "url": 1}, {"unique": True})
db.scheduled_tests.createIndex({"next_run": 1, "status": 1})
```

## Database Schema

### Collections Overview

#### projects
```javascript
{
    "_id": ObjectId("..."),
    "project_id": "proj_123",
    "name": "Company Website",
    "description": "Main corporate website accessibility testing",
    "created_at": ISODate("2025-01-01T00:00:00Z"),
    "updated_at": ISODate("2025-01-15T10:30:00Z"),
    "status": "active",
    "settings": {
        "wcag_level": "AA",
        "test_frequency": "weekly",
        "notification_emails": ["dev@company.com"]
    },
    "websites": ["web_456", "web_789"]
}
```

#### websites
```javascript
{
    "_id": ObjectId("..."),
    "website_id": "web_456",
    "project_id": "proj_123",
    "name": "Main Website",
    "base_url": "https://company.com",
    "created_at": ISODate("2025-01-01T00:00:00Z"),
    "last_crawled": ISODate("2025-01-15T09:00:00Z"),
    "crawl_settings": {
        "max_pages": 100,
        "follow_external": false,
        "ignore_patterns": ["/admin/*", "/*.pdf"]
    },
    "page_count": 25
}
```

#### pages
```javascript
{
    "_id": ObjectId("..."),
    "page_id": "page_789",
    "website_id": "web_456",
    "url": "https://company.com/about",
    "title": "About Us - Company",
    "discovered_at": ISODate("2025-01-01T00:00:00Z"),
    "last_tested": ISODate("2025-01-15T09:15:00Z"),
    "status": "active",
    "metadata": {
        "content_type": "text/html",
        "status_code": 200,
        "page_size": 15420
    }
}
```

#### test_results
```javascript
{
    "_id": ObjectId("..."),
    "result_id": "result_101112",
    "page_id": "page_789",
    "project_id": "proj_123",
    "test_date": ISODate("2025-01-15T09:15:00Z"),
    "wcag_level": "AA",
    "violations": [
        {
            "rule_id": "color-contrast",
            "severity": "serious",
            "description": "Elements must have sufficient color contrast",
            "element": "<p class='light-text'>Low contrast text</p>",
            "xpath": "//p[@class='light-text']",
            "fix_suggestions": [
                "Increase contrast ratio to at least 4.5:1",
                "Use darker text color or lighter background"
            ]
        }
    ],
    "summary": {
        "total_violations": 3,
        "serious": 1,
        "moderate": 2,
        "minor": 0,
        "compliance_score": 85.5
    }
}
```

### Index Strategy
```javascript
// Performance indexes
db.test_results.createIndex({"project_id": 1, "test_date": -1})
db.test_results.createIndex({"page_id": 1, "test_date": -1})
db.pages.createIndex({"website_id": 1, "url": 1}, {"unique": true})
db.websites.createIndex({"project_id": 1})
db.scheduled_tests.createIndex({"next_run": 1, "status": 1})

// Query optimization indexes
db.test_results.createIndex({"test_date": -1, "summary.compliance_score": 1})
db.violations.createIndex({"rule_id": 1, "severity": 1})
```

## API Development

### RESTful Conventions

#### URL Patterns
```
GET    /api/projects              # List projects
POST   /api/projects              # Create project
GET    /api/projects/{id}         # Get project
PUT    /api/projects/{id}         # Update project
DELETE /api/projects/{id}         # Delete project

GET    /api/projects/{id}/websites    # List project websites
POST   /api/projects/{id}/websites    # Add website to project

GET    /api/testing/run/{project_id}  # Start test
GET    /api/testing/status/{test_id}  # Check test status
GET    /api/testing/results/{test_id} # Get test results
```

#### Response Format
```python
# Success Response
{
    "success": True,
    "data": {
        "project_id": "proj_123",
        "name": "Website Testing",
        "created_at": "2025-01-15T10:30:00Z"
    },
    "message": "Project created successfully"
}

# Error Response
{
    "success": False,
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "Invalid project name",
        "details": {
            "field": "name",
            "constraint": "must be 3-100 characters"
        }
    }
}
```

#### API Implementation
```python
from flask import Blueprint, request, jsonify
from autotest.services.testing_service import TestingService

api = Blueprint('api', __name__, url_prefix='/api')

@api.route('/testing/run/<project_id>', methods=['POST'])
def run_accessibility_test(project_id: str):
    """Start accessibility test for project."""
    try:
        # Validate request
        data = request.get_json() or {}
        test_type = data.get('test_type', 'full')
        
        # Start test
        testing_service = TestingService()
        test_id = testing_service.start_test(
            project_id=project_id,
            test_type=test_type
        )
        
        return jsonify({
            "success": True,
            "data": {
                "test_id": test_id,
                "status": "started",
                "estimated_duration": "5-10 minutes"
            }
        })
        
    except ValueError as e:
        return jsonify({
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": str(e)
            }
        }), 400
    except Exception as e:
        return jsonify({
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "Test could not be started"
            }
        }), 500
```

## Frontend Development

### Template Structure
```html
<!-- autotest/web/templates/base.html -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}AutoTest{% endblock %}</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/main.css') }}">
</head>
<body>
    <header class="main-header">
        {% include 'components/navigation.html' %}
    </header>
    
    <main class="main-content">
        {% block content %}{% endblock %}
    </main>
    
    <footer class="main-footer">
        {% include 'components/footer.html' %}
    </footer>
    
    <script src="{{ url_for('static', filename='js/main.js') }}"></script>
    {% block scripts %}{% endblock %}
</body>
</html>
```

### Accessibility Standards
```css
/* Ensure keyboard focus visibility */
.btn:focus, .form-control:focus {
    outline: 2px solid #007bff;
    outline-offset: 2px;
}

/* Maintain color contrast ratios */
.text-primary { color: #0066cc; } /* 4.5:1 contrast */
.bg-light { background-color: #f8f9fa; }

/* Responsive font sizes */
.heading-large { font-size: clamp(1.5rem, 4vw, 2.5rem); }

/* Skip link for screen readers */
.skip-link {
    position: absolute;
    top: -40px;
    left: 6px;
    z-index: 1000;
}
.skip-link:focus {
    top: 6px;
}
```

### JavaScript Guidelines
```javascript
// Use semantic HTML and ARIA labels
class AccessibilityHelper {
    static announceToScreenReader(message) {
        const announcement = document.createElement('div');
        announcement.setAttribute('aria-live', 'polite');
        announcement.setAttribute('aria-atomic', 'true');
        announcement.style.position = 'absolute';
        announcement.style.left = '-10000px';
        announcement.textContent = message;
        
        document.body.appendChild(announcement);
        setTimeout(() => document.body.removeChild(announcement), 1000);
    }
    
    static trapFocus(container) {
        const focusableElements = container.querySelectorAll(
            'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        const firstElement = focusableElements[0];
        const lastElement = focusableElements[focusableElements.length - 1];
        
        container.addEventListener('keydown', (e) => {
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
}
```

## Debugging Guide

### Common Issues

#### Database Connection Issues
```python
# Debug database connection
from autotest.core.database import DatabaseConnection
from autotest.utils.config import Config

config = Config()
db = DatabaseConnection(config)

try:
    db.connect()
    print("Database connection successful")
    
    # Test basic operations
    result = db.db.projects.find_one()
    print(f"Sample document: {result}")
    
except Exception as e:
    print(f"Database error: {e}")
    print(f"Connection string: {config.get('database.mongodb_uri')}")
```

#### Testing Engine Issues
```python
# Debug accessibility testing
from autotest.core.accessibility_tester import AccessibilityTester

tester = AccessibilityTester()

# Test with simple HTML
html = '<html><body><h1>Test</h1></body></html>'
results = tester.test_html(html)

print(f"Test results: {results}")
print(f"Violations found: {len(results.violations)}")
```

### Logging Configuration
```python
# autotest/utils/logger.py
import logging
import sys
from typing import Optional

def setup_development_logging(level: str = "DEBUG") -> logging.Logger:
    """Setup detailed logging for development."""
    logger = logging.getLogger('autotest')
    logger.setLevel(getattr(logging, level.upper()))
    
    # Console handler with detailed format
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
    )
    console_handler.setFormatter(formatter)
    
    logger.addHandler(console_handler)
    return logger
```

### Performance Profiling
```python
# Profile slow operations
import cProfile
import pstats
from autotest.services.testing_service import TestingService

def profile_testing():
    """Profile accessibility testing performance."""
    profiler = cProfile.Profile()
    
    profiler.enable()
    
    # Run test
    service = TestingService()
    service.run_full_test("project_123")
    
    profiler.disable()
    
    # Analyze results
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(20)  # Top 20 slowest functions

if __name__ == '__main__':
    profile_testing()
```

## Performance Guidelines

### Database Optimization

#### Query Optimization
```python
# Good: Use indexes and projections
def get_recent_test_results(project_id: str, limit: int = 10):
    return db.test_results.find(
        {"project_id": project_id},
        {"violations": 0, "raw_html": 0}  # Exclude large fields
    ).sort("test_date", -1).limit(limit)

# Avoid: Full table scans
def get_test_by_url(url: str):  # Missing index on url
    return db.test_results.find({"page_url": url})
```

#### Aggregation Pipelines
```python
def get_compliance_trends(project_id: str, days: int = 30):
    """Get compliance score trends using aggregation."""
    pipeline = [
        {
            "$match": {
                "project_id": project_id,
                "test_date": {
                    "$gte": datetime.now() - timedelta(days=days)
                }
            }
        },
        {
            "$group": {
                "_id": {
                    "$dateToString": {
                        "format": "%Y-%m-%d",
                        "date": "$test_date"
                    }
                },
                "avg_score": {"$avg": "$summary.compliance_score"},
                "test_count": {"$sum": 1}
            }
        },
        {"$sort": {"_id": 1}}
    ]
    
    return list(db.test_results.aggregate(pipeline))
```

### Caching Strategy
```python
from functools import lru_cache
import hashlib

class TestingCache:
    """Cache test results for repeated content."""
    
    def __init__(self):
        self._cache = {}
    
    def get_content_hash(self, html_content: str) -> str:
        """Generate hash for HTML content."""
        return hashlib.md5(html_content.encode()).hexdigest()
    
    @lru_cache(maxsize=1000)
    def get_cached_result(self, content_hash: str):
        """Get cached test result."""
        return self._cache.get(content_hash)
    
    def cache_result(self, content_hash: str, result):
        """Cache test result."""
        self._cache[content_hash] = result
```

### Memory Management
```python
def process_large_website(website_id: str):
    """Process large websites efficiently."""
    batch_size = 50
    
    # Process pages in batches
    page_cursor = db.pages.find(
        {"website_id": website_id, "status": "active"}
    ).batch_size(batch_size)
    
    for page_batch in batch_cursor:
        # Process batch
        results = []
        for page in page_batch:
            result = test_page(page)
            results.append(result)
        
        # Save batch results
        db.test_results.insert_many(results)
        
        # Clear memory
        del results
        del page_batch
```

## Contributing Guidelines

### Pull Request Process

1. **Fork Repository**
   ```bash
   git fork https://github.com/bobdodd/autoTest.git
   ```

2. **Create Feature Branch**
   ```bash
   git checkout -b feature/wcag-2.2-support
   ```

3. **Development**
   - Write code following style guidelines
   - Add comprehensive tests
   - Update documentation

4. **Quality Checks**
   ```bash
   # Format code
   black autotest/
   
   # Run tests
   pytest --cov=autotest
   
   # Check types
   mypy autotest/
   
   # Security scan
   bandit -r autotest/
   ```

5. **Submit PR**
   - Clear description of changes
   - Link to related issues
   - Include screenshots for UI changes

### Code Review Checklist

#### Functionality
- [ ] Code solves the stated problem
- [ ] Edge cases are handled
- [ ] Error handling is appropriate
- [ ] Performance impact is considered

#### Quality
- [ ] Code follows style guidelines
- [ ] Functions are well-documented
- [ ] Tests provide good coverage
- [ ] No security vulnerabilities

#### Design
- [ ] Code fits architectural patterns
- [ ] Interfaces are clean and logical
- [ ] Dependencies are appropriate
- [ ] Database changes are documented

### Release Process

1. **Version Bump**
   ```bash
   # Update version in setup.py and __init__.py
   git tag v1.1.0
   ```

2. **Update Documentation**
   - Update changelog
   - Review and update README
   - Generate API documentation

3. **Testing**
   ```bash
   # Full test suite
   pytest autotest/tests/
   
   # Integration tests
   pytest autotest/tests/integration/
   
   # Manual testing checklist
   ```

4. **Release**
   ```bash
   git push origin main --tags
   ```

---

This developer guide provides the foundation for contributing to AutoTest. For questions or clarifications, please open an issue or discussion on GitHub.

*Developer Guide - AutoTest Version 1.0*