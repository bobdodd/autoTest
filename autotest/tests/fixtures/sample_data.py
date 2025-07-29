"""
Sample test data for AutoTest unit tests
"""

from datetime import datetime, timezone
from autotest.models.project import Project
from autotest.models.page import Page
from autotest.models.test_result import TestResult

# Sample HTML content for testing
SAMPLE_HTML_GOOD = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Accessible Test Page</title>
</head>
<body>
    <header>
        <h1>Main Heading</h1>
        <nav aria-label="Main navigation">
            <ul>
                <li><a href="/">Home</a></li>
                <li><a href="/about">About Us</a></li>
                <li><a href="/contact">Contact</a></li>
            </ul>
        </nav>
    </header>
    
    <main>
        <h2>Content Section</h2>
        <p>This is a well-structured paragraph with good contrast.</p>
        
        <img src="image.jpg" alt="Descriptive alternative text">
        
        <form>
            <label for="name">Full Name:</label>
            <input type="text" id="name" name="name" required>
            
            <label for="email">Email Address:</label>
            <input type="email" id="email" name="email" required>
            
            <button type="submit">Submit Form</button>
        </form>
    </main>
    
    <footer>
        <p>&copy; 2025 Accessible Website</p>
    </footer>
</body>
</html>
"""

SAMPLE_HTML_BAD = """
<!DOCTYPE html>
<html>
<head>
    <title>Inaccessible Test Page</title>
    <style>
        .poor-contrast { color: #ccc; background: #ddd; }
        .tiny-text { font-size: 8px; }
        .no-focus { outline: none; }
    </style>
</head>
<body>
    <h3>Wrong heading level</h3>
    <h1>Main heading after h3</h1>
    
    <p class="poor-contrast">This text has poor contrast</p>
    <p class="tiny-text">This text is too small</p>
    
    <img src="image1.jpg">
    <img src="image2.jpg" alt="">
    
    <form>
        <input type="text" placeholder="Name">
        <input type="email">
        <div class="no-focus" tabindex="0" onclick="submit()">Submit</div>
    </form>
    
    <a href="/page">Click here</a>
    <a href="/another"></a>
</body>
</html>
"""

# Sample CSS content
SAMPLE_CSS_GOOD = """
body {
    font-family: Arial, sans-serif;
    font-size: 16px;
    line-height: 1.5;
    color: #333;
    background: #fff;
}

.button {
    background: #0066cc;
    color: #ffffff;
    border: 2px solid #004499;
    padding: 12px 24px;
    min-height: 44px;
    min-width: 44px;
    font-size: 16px;
}

.button:focus {
    outline: 2px solid #ffcc00;
    outline-offset: 2px;
}

@media (prefers-reduced-motion: reduce) {
    * {
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
    }
}
"""

SAMPLE_CSS_BAD = """
body {
    font-size: 10px;
    line-height: 1.0;
}

.button {
    background: #ccc;
    color: #ddd;
    border: none;
    padding: 2px 4px;
}

.button:focus {
    outline: none;
}

.animated {
    animation: spin 0.1s infinite;
}

@keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
}
"""

# Sample JavaScript content
SAMPLE_JS_GOOD = """
// Good accessibility practices

// Proper keyboard event handling
document.getElementById('button').addEventListener('keydown', function(e) {
    if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        this.click();
    }
});

// Accessible modal
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

// Respects motion preferences
function animateElement(element) {
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (!prefersReducedMotion) {
        element.style.animation = 'bounce 2s infinite';
    }
}
"""

SAMPLE_JS_BAD = """
// Poor accessibility practices

// Click-only handler
document.getElementById('button').addEventListener('click', function() {
    alert('Button clicked');
});

// Poor focus management
function trapFocus(element) {
    element.focus();
    // Missing: escape key handling, focus restoration
}

// Automatic content changes
setInterval(function() {
    document.getElementById('content').innerHTML = 'Updated: ' + new Date();
}, 1000);

// Motion without preference check
function animateElement(element) {
    element.style.animation = 'bounce 2s infinite';
}

// Missing ARIA updates
function toggleMenu() {
    const menu = document.getElementById('menu');
    menu.style.display = menu.style.display === 'none' ? 'block' : 'none';
    // Missing: aria-expanded updates
}
"""

def create_sample_project():
    """Create a sample project for testing"""
    return Project(
        name="Sample Test Project",
        description="A project created for unit testing purposes",
        created_by="test_user",
        settings={
            'max_pages': 25,
            'max_depth': 3,
            'wcag_level': 'AA',
            'check_images': True,
            'check_forms': True,
            'follow_external_links': False,
            'user_agent': 'AutoTest/1.0',
            'viewport': {'width': 1920, 'height': 1080}
        }
    )

def create_sample_pages(project_id):
    """Create sample pages for testing"""
    pages = []
    
    # Page 1: Home page
    pages.append(Page(
        url="https://example.com/",
        title="Home - Example Website",
        project_id=project_id,
        status="tested",
        metadata={
            'content_type': 'text/html',
            'charset': 'utf-8',
            'language': 'en',
            'word_count': 250,
            'has_forms': False,
            'has_images': True,
            'heading_structure': ['h1', 'h2', 'h2', 'h3'],
            'links_count': 15,
            'internal_links': 10,
            'external_links': 5
        }
    ))
    
    # Page 2: Contact page with form
    pages.append(Page(
        url="https://example.com/contact",
        title="Contact Us - Example Website",
        project_id=project_id,
        status="tested",
        metadata={
            'content_type': 'text/html',
            'charset': 'utf-8',
            'language': 'en',
            'word_count': 180,
            'has_forms': True,
            'has_images': False,
            'heading_structure': ['h1', 'h2'],
            'links_count': 8,
            'form_elements': ['input[type=text]', 'input[type=email]', 'textarea', 'button[type=submit]']
        }
    ))
    
    # Page 3: About page
    pages.append(Page(
        url="https://example.com/about",
        title="About - Example Website",
        project_id=project_id,
        status="crawled",
        metadata={
            'content_type': 'text/html',
            'charset': 'utf-8',
            'language': 'en',
            'word_count': 320,
            'has_forms': False,
            'has_images': True,
            'heading_structure': ['h1', 'h2', 'h3', 'h3'],
            'links_count': 12
        }
    ))
    
    return pages

def create_sample_test_results(page_id, project_id):
    """Create sample test results for testing"""
    results = []
    
    # Good result with minimal violations
    results.append(TestResult(
        page_id=page_id,
        project_id=project_id,
        violations=[
            {
                'rule_id': 'color_contrast',
                'severity': 'moderate',
                'impact': 'moderate',
                'description': 'Element has insufficient color contrast',
                'help_url': 'https://dequeuniversity.com/rules/axe/color-contrast',
                'elements': [
                    {
                        'target': ['.secondary-text'],
                        'html': '<span class="secondary-text">Secondary information</span>',
                        'any': [
                            {
                                'id': 'color-contrast',
                                'data': {'fgColor': '#666666', 'bgColor': '#ffffff', 'contrastRatio': 4.1},
                                'relatedNodes': []
                            }
                        ]
                    }
                ]
            }
        ],
        score=92,
        wcag_level='AA',
        test_date=datetime.now(timezone.utc),
        test_config={
            'rules_enabled': ['color_contrast', 'alt_text', 'keyboard_navigation', 'form_labels'],
            'browser': 'chrome',
            'viewport': {'width': 1920, 'height': 1080},
            'user_agent': 'AutoTest/1.0'
        }
    ))
    
    # Poor result with multiple violations
    results.append(TestResult(
        page_id=page_id,
        project_id=project_id,
        violations=[
            {
                'rule_id': 'alt_text',
                'severity': 'serious',
                'impact': 'serious',
                'description': 'Image must have alternative text',
                'elements': [{'target': ['img'], 'html': '<img src="photo.jpg">'}]
            },
            {
                'rule_id': 'form_labels',
                'severity': 'critical',
                'impact': 'critical',
                'description': 'Form input must have an associated label',
                'elements': [{'target': ['input[type="text"]'], 'html': '<input type="text" name="name">'}]
            },
            {
                'rule_id': 'heading_structure',
                'severity': 'moderate',
                'impact': 'moderate',
                'description': 'Heading levels should increase by one',
                'elements': [{'target': ['h3'], 'html': '<h3>Skipped heading level</h3>'}]
            }
        ],
        score=58,
        wcag_level='AA',
        test_date=datetime.now(timezone.utc),
        test_config={
            'rules_enabled': ['color_contrast', 'alt_text', 'keyboard_navigation', 'form_labels', 'heading_structure'],
            'browser': 'chrome',
            'viewport': {'width': 1920, 'height': 1080}
        }
    ))
    
    return results

# Test data collections
TEST_DATA = {
    'html': {
        'good': SAMPLE_HTML_GOOD,
        'bad': SAMPLE_HTML_BAD
    },
    'css': {
        'good': SAMPLE_CSS_GOOD,
        'bad': SAMPLE_CSS_BAD
    },
    'javascript': {
        'good': SAMPLE_JS_GOOD,
        'bad': SAMPLE_JS_BAD
    }
}

# Expected test results for validation
EXPECTED_VIOLATIONS = {
    'html_bad': [
        'heading_structure',
        'alt_text',
        'form_labels',
        'color_contrast',
        'keyboard_navigation',
        'link_accessibility'
    ],
    'css_bad': [
        'font_size',
        'line_height',
        'color_contrast',
        'focus_indicators',
        'touch_targets',
        'animation_safety'
    ],
    'js_bad': [
        'keyboard_handlers',
        'focus_management',
        'dynamic_content',
        'motion_preferences',
        'aria_updates'
    ]
}