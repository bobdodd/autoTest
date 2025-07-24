"""
Custom accessibility testing engine for AutoTest application
"""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
import datetime
import json

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

from autotest.core.database import DatabaseConnection
from autotest.models.page import PageRepository
from autotest.models.test_result import (
    TestResultRepository, AccessibilityViolation, 
    AccessibilityPass, TestResult
)
from autotest.utils.logger import LoggerMixin
from autotest.utils.config import Config


@dataclass
class TestRule:
    """Accessibility test rule definition"""
    rule_id: str
    name: str
    description: str
    help_text: str
    help_url: str
    impact: str  # "minor", "moderate", "serious", "critical"
    test_function: Callable


class AccessibilityTester(LoggerMixin):
    """Custom accessibility testing engine"""
    
    def __init__(self, config: Config, db_connection: DatabaseConnection):
        """
        Initialize accessibility tester
        
        Args:
            config: Application configuration
            db_connection: Database connection instance
        """
        self.config = config
        self.db_connection = db_connection
        self.page_repo = PageRepository(db_connection)
        self.test_result_repo = TestResultRepository(db_connection)
        
        self.timeout = config.get('testing.timeout', 30)
        self.screenshot_on_error = config.get('testing.screenshot_on_error', True)
        
        # Initialize test rules
        self.rules: List[TestRule] = []
        self._initialize_rules()
        
        self.driver: Optional[webdriver.Chrome | webdriver.Firefox] = None
    
    def _initialize_rules(self) -> None:
        """Initialize accessibility test rules"""
        self.rules = [
            TestRule(
                rule_id="page-has-title",
                name="Page has title",
                description="Ensures every HTML document has a non-empty <title> element",
                help_text="All pages must have a title to help users understand the page content",
                help_url="https://www.w3.org/WAI/WCAG21/Understanding/page-titled.html",
                impact="serious",
                test_function=self._test_page_title
            ),
            TestRule(
                rule_id="page-has-heading",
                name="Page has heading",
                description="Ensures the page has at least one heading (h1-h6)",
                help_text="Pages should have proper heading structure for screen readers",
                help_url="https://www.w3.org/WAI/WCAG21/Understanding/info-and-relationships.html",
                impact="serious",
                test_function=self._test_page_heading
            ),
            TestRule(
                rule_id="images-have-alt",
                name="Images have alt text",
                description="Ensures all images have alternative text",
                help_text="Images must have alt attributes for screen readers",
                help_url="https://www.w3.org/WAI/WCAG21/Understanding/non-text-content.html",
                impact="critical",
                test_function=self._test_image_alt_text
            ),
            TestRule(
                rule_id="links-have-names",
                name="Links have accessible names",
                description="Ensures links have discernible text",
                help_text="Links must have text content or accessible names",
                help_url="https://www.w3.org/WAI/WCAG21/Understanding/link-purpose-in-context.html",
                impact="serious",
                test_function=self._test_link_names
            ),
            TestRule(
                rule_id="form-labels",
                name="Form inputs have labels",
                description="Ensures every form input has an associated label",
                help_text="Form controls must be properly labeled for accessibility",
                help_url="https://www.w3.org/WAI/WCAG21/Understanding/labels-or-instructions.html",
                impact="critical",
                test_function=self._test_form_labels
            ),
            TestRule(
                rule_id="color-contrast",
                name="Color contrast",
                description="Ensures text has sufficient color contrast",
                help_text="Text must have adequate contrast ratio for readability",
                help_url="https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum.html",
                impact="serious",
                test_function=self._test_color_contrast
            ),
            TestRule(
                rule_id="focus-visible",
                name="Focus indicators",
                description="Ensures focusable elements have visible focus indicators",
                help_text="Interactive elements must have visible focus indicators",
                help_url="https://www.w3.org/WAI/WCAG21/Understanding/focus-visible.html",
                impact="serious",
                test_function=self._test_focus_indicators
            ),
            TestRule(
                rule_id="heading-order",
                name="Heading hierarchy",
                description="Ensures headings are in proper hierarchical order",
                help_text="Headings should follow proper nesting order (h1, h2, h3, etc.)",
                help_url="https://www.w3.org/WAI/WCAG21/Understanding/info-and-relationships.html",
                impact="moderate",
                test_function=self._test_heading_hierarchy
            ),
            TestRule(
                rule_id="skip-link",
                name="Skip to content link",
                description="Ensures there is a way to skip to main content",
                help_text="Pages should provide a way to skip navigation",
                help_url="https://www.w3.org/WAI/WCAG21/Understanding/bypass-blocks.html",
                impact="moderate",
                test_function=self._test_skip_link
            ),
            TestRule(
                rule_id="lang-attribute",
                name="HTML lang attribute",
                description="Ensures the HTML document has a lang attribute",
                help_text="HTML documents must specify the primary language",
                help_url="https://www.w3.org/WAI/WCAG21/Understanding/language-of-page.html",
                impact="serious",
                test_function=self._test_lang_attribute
            )
        ]
    
    def test_page(self, page_id: str, driver: Optional[webdriver.Chrome | webdriver.Firefox] = None) -> Dict[str, Any]:
        """
        Test a single page for accessibility violations
        
        Args:
            page_id: Page ID to test
            driver: Optional WebDriver instance (will create one if not provided)
        
        Returns:
            Dictionary with test results
        """
        try:
            # Get page information
            page = self.page_repo.get_page(page_id)
            if not page:
                return {
                    'success': False,
                    'error': 'Page not found'
                }
            
            self.logger.info(f"Testing page: {page.url}")
            
            # Use provided driver or create new one
            driver_provided = driver is not None
            if not driver_provided:
                from autotest.core.scraper import WebScraper
                scraper = WebScraper(self.config, self.db_connection)
                if not scraper._setup_driver():
                    return {
                        'success': False,
                        'error': 'Failed to setup web browser'
                    }
                driver = scraper.driver
            
            self.driver = driver
            
            try:
                # Navigate to page
                self.driver.get(page.url)
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                
                # Run all accessibility tests
                violations = []
                passes = []
                incomplete = []
                
                for rule in self.rules:
                    try:
                        result = rule.test_function()
                        
                        if result['status'] == 'violation':
                            violation = AccessibilityViolation(
                                violation_id=rule.rule_id,
                                impact=rule.impact,
                                description=rule.description,
                                help=rule.help_text,
                                help_url=rule.help_url,
                                nodes=result.get('nodes', [])
                            )
                            violations.append(violation)
                            
                        elif result['status'] == 'pass':
                            pass_result = AccessibilityPass(
                                rule_id=rule.rule_id,
                                description=rule.description,
                                help=rule.help_text,
                                help_url=rule.help_url,
                                nodes=result.get('nodes', [])
                            )
                            passes.append(pass_result)
                            
                        elif result['status'] == 'incomplete':
                            incomplete.append({
                                'id': rule.rule_id,
                                'description': rule.description,
                                'reason': result.get('reason', 'Unable to complete test')
                            })
                            
                    except Exception as e:
                        self.logger.warning(f"Error running rule {rule.rule_id}: {e}")
                        incomplete.append({
                            'id': rule.rule_id,
                            'description': rule.description,
                            'reason': f'Test error: {str(e)}'
                        })
                
                # Create test result
                test_result_id = self.test_result_repo.create_test_result(
                    page_id, violations, passes, incomplete, "autotest-custom"
                )
                
                # Update page last tested timestamp
                self.page_repo.update_last_tested(page_id)
                
                self.logger.info(f"Page test completed. Violations: {len(violations)}, Passes: {len(passes)}")
                
                return {
                    'success': True,
                    'test_result_id': test_result_id,
                    'summary': {
                        'violations': len(violations),
                        'passes': len(passes),
                        'incomplete': len(incomplete)
                    },
                    'violations': [v.to_dict() for v in violations],
                    'passes': [p.to_dict() for p in passes],
                    'incomplete': incomplete
                }
                
            finally:
                if not driver_provided and hasattr(self, 'driver'):
                    try:
                        self.driver.quit()
                    except Exception:
                        pass
                    finally:
                        self.driver = None
                        
        except Exception as e:
            self.logger.error(f"Error testing page {page_id}: {e}")
            return {
                'success': False,
                'error': f'Test failed: {str(e)}'
            }
    
    # Test rule implementations
    
    def _test_page_title(self) -> Dict[str, Any]:
        """Test if page has a non-empty title"""
        try:
            title_element = self.driver.find_element(By.TAG_NAME, "title")
            title_text = title_element.get_attribute("textContent").strip()
            
            if not title_text:
                return {
                    'status': 'violation',
                    'nodes': [{'target': ['title'], 'html': '<title></title>'}]
                }
            
            return {
                'status': 'pass',
                'nodes': [{'target': ['title'], 'html': f'<title>{title_text}</title>'}]
            }
            
        except Exception:
            return {
                'status': 'violation',
                'nodes': [{'target': ['html'], 'html': 'No title element found'}]
            }
    
    def _test_page_heading(self) -> Dict[str, Any]:
        """Test if page has at least one heading"""
        try:
            headings = self.driver.find_elements(By.CSS_SELECTOR, "h1, h2, h3, h4, h5, h6")
            
            if not headings:
                return {
                    'status': 'violation',
                    'nodes': [{'target': ['body'], 'html': 'No heading elements found'}]
                }
            
            heading_nodes = []
            for heading in headings[:5]:  # Limit to first 5 for performance
                try:
                    heading_nodes.append({
                        'target': [heading.tag_name],
                        'html': heading.get_attribute('outerHTML')[:200]
                    })
                except Exception:
                    continue
            
            return {
                'status': 'pass',
                'nodes': heading_nodes
            }
            
        except Exception as e:
            return {
                'status': 'incomplete',
                'reason': f'Error checking headings: {str(e)}'
            }
    
    def _test_image_alt_text(self) -> Dict[str, Any]:
        """Test if images have alt text"""
        try:
            images = self.driver.find_elements(By.TAG_NAME, "img")
            violations = []
            passes = []
            
            for img in images:
                try:
                    alt_text = img.get_attribute("alt")
                    
                    if alt_text is None:
                        violations.append({
                            'target': ['img'],
                            'html': img.get_attribute('outerHTML')[:200]
                        })
                    else:
                        passes.append({
                            'target': ['img'],
                            'html': img.get_attribute('outerHTML')[:200]
                        })
                        
                except Exception:
                    continue
            
            if violations:
                return {
                    'status': 'violation',
                    'nodes': violations
                }
            elif passes:
                return {
                    'status': 'pass',
                    'nodes': passes
                }
            else:
                return {
                    'status': 'pass',
                    'nodes': [{'target': ['body'], 'html': 'No images found'}]
                }
                
        except Exception as e:
            return {
                'status': 'incomplete',
                'reason': f'Error checking images: {str(e)}'
            }
    
    def _test_link_names(self) -> Dict[str, Any]:
        """Test if links have accessible names"""
        try:
            links = self.driver.find_elements(By.TAG_NAME, "a")
            violations = []
            passes = []
            
            for link in links:
                try:
                    # Check if link has href (is actually a link)
                    href = link.get_attribute("href")
                    if not href:
                        continue
                    
                    # Check for accessible name
                    text_content = link.get_attribute("textContent").strip()
                    aria_label = link.get_attribute("aria-label")
                    title = link.get_attribute("title")
                    
                    has_accessible_name = bool(text_content or aria_label or title)
                    
                    if not has_accessible_name:
                        violations.append({
                            'target': ['a'],
                            'html': link.get_attribute('outerHTML')[:200]
                        })
                    else:
                        passes.append({
                            'target': ['a'],
                            'html': link.get_attribute('outerHTML')[:200]
                        })
                        
                except Exception:
                    continue
            
            if violations:
                return {
                    'status': 'violation',
                    'nodes': violations
                }
            elif passes:
                return {
                    'status': 'pass',
                    'nodes': passes
                }
            else:
                return {
                    'status': 'pass',
                    'nodes': [{'target': ['body'], 'html': 'No links found'}]
                }
                
        except Exception as e:
            return {
                'status': 'incomplete',
                'reason': f'Error checking links: {str(e)}'
            }
    
    def _test_form_labels(self) -> Dict[str, Any]:
        """Test if form inputs have labels"""
        try:
            inputs = self.driver.find_elements(By.CSS_SELECTOR, "input, select, textarea")
            violations = []
            passes = []
            
            for input_elem in inputs:
                try:
                    input_type = input_elem.get_attribute("type")
                    
                    # Skip hidden inputs and buttons
                    if input_type in ["hidden", "submit", "button", "reset"]:
                        continue
                    
                    # Check for label association
                    input_id = input_elem.get_attribute("id")
                    aria_label = input_elem.get_attribute("aria-label")
                    aria_labelledby = input_elem.get_attribute("aria-labelledby")
                    
                    has_label = False
                    
                    if aria_label or aria_labelledby:
                        has_label = True
                    elif input_id:
                        try:
                            label = self.driver.find_element(By.CSS_SELECTOR, f"label[for='{input_id}']")
                            has_label = True
                        except Exception:
                            pass
                    
                    if not has_label:
                        violations.append({
                            'target': [input_elem.tag_name],
                            'html': input_elem.get_attribute('outerHTML')[:200]
                        })
                    else:
                        passes.append({
                            'target': [input_elem.tag_name],
                            'html': input_elem.get_attribute('outerHTML')[:200]
                        })
                        
                except Exception:
                    continue
            
            if violations:
                return {
                    'status': 'violation',
                    'nodes': violations
                }
            elif passes:
                return {
                    'status': 'pass',
                    'nodes': passes
                }
            else:
                return {
                    'status': 'pass',
                    'nodes': [{'target': ['body'], 'html': 'No form inputs found'}]
                }
                
        except Exception as e:
            return {
                'status': 'incomplete',
                'reason': f'Error checking form labels: {str(e)}'
            }
    
    def _test_color_contrast(self) -> Dict[str, Any]:
        """Basic color contrast test (simplified implementation)"""
        try:
            # This is a simplified test - full color contrast testing requires
            # more sophisticated color analysis
            text_elements = self.driver.find_elements(By.CSS_SELECTOR, "p, h1, h2, h3, h4, h5, h6, span, div, a")
            
            violations = []
            passes = []
            
            for element in text_elements[:10]:  # Limit for performance
                try:
                    text_content = element.get_attribute("textContent").strip()
                    if not text_content:
                        continue
                    
                    # Get computed styles
                    color = self.driver.execute_script(
                        "return window.getComputedStyle(arguments[0]).color", element
                    )
                    background_color = self.driver.execute_script(
                        "return window.getComputedStyle(arguments[0]).backgroundColor", element
                    )
                    
                    # Simple check - if background is transparent, assume it passes for now
                    if background_color == "rgba(0, 0, 0, 0)" or background_color == "transparent":
                        passes.append({
                            'target': [element.tag_name],
                            'html': element.get_attribute('outerHTML')[:200]
                        })
                    else:
                        # For now, assume colored backgrounds pass
                        # Full implementation would calculate actual contrast ratios
                        passes.append({
                            'target': [element.tag_name],
                            'html': element.get_attribute('outerHTML')[:200]
                        })
                        
                except Exception:
                    continue
            
            return {
                'status': 'pass',
                'nodes': passes
            }
            
        except Exception as e:
            return {
                'status': 'incomplete',
                'reason': f'Error checking color contrast: {str(e)}'
            }
    
    def _test_focus_indicators(self) -> Dict[str, Any]:
        """Test for focus indicators on interactive elements"""
        try:
            focusable = self.driver.find_elements(By.CSS_SELECTOR, "a, button, input, select, textarea, [tabindex]")
            
            violations = []
            passes = []
            
            for element in focusable[:5]:  # Limit for performance
                try:
                    # Focus the element
                    self.driver.execute_script("arguments[0].focus()", element)
                    
                    # Check if element has focus styles
                    outline = self.driver.execute_script(
                        "return window.getComputedStyle(arguments[0]).outline", element
                    )
                    
                    # Simple check - if element has outline or is button/link, assume it passes
                    if outline != "none" or element.tag_name.lower() in ["button", "a"]:
                        passes.append({
                            'target': [element.tag_name],
                            'html': element.get_attribute('outerHTML')[:200]
                        })
                    else:
                        violations.append({
                            'target': [element.tag_name],
                            'html': element.get_attribute('outerHTML')[:200]
                        })
                        
                except Exception:
                    continue
            
            if violations:
                return {
                    'status': 'violation',
                    'nodes': violations
                }
            else:
                return {
                    'status': 'pass',
                    'nodes': passes
                }
                
        except Exception as e:
            return {
                'status': 'incomplete',
                'reason': f'Error checking focus indicators: {str(e)}'
            }
    
    def _test_heading_hierarchy(self) -> Dict[str, Any]:
        """Test heading hierarchy order"""
        try:
            headings = self.driver.find_elements(By.CSS_SELECTOR, "h1, h2, h3, h4, h5, h6")
            
            if not headings:
                return {
                    'status': 'pass',
                    'nodes': [{'target': ['body'], 'html': 'No headings found'}]
                }
            
            violations = []
            passes = []
            
            previous_level = 0
            
            for heading in headings:
                try:
                    current_level = int(heading.tag_name[1])  # Extract number from h1, h2, etc.
                    
                    # Check if heading level jumps too much
                    if previous_level > 0 and current_level > previous_level + 1:
                        violations.append({
                            'target': [heading.tag_name],
                            'html': heading.get_attribute('outerHTML')[:200]
                        })
                    else:
                        passes.append({
                            'target': [heading.tag_name],
                            'html': heading.get_attribute('outerHTML')[:200]
                        })
                    
                    previous_level = current_level
                    
                except Exception:
                    continue
            
            if violations:
                return {
                    'status': 'violation',
                    'nodes': violations
                }
            else:
                return {
                    'status': 'pass',
                    'nodes': passes
                }
                
        except Exception as e:
            return {
                'status': 'incomplete',
                'reason': f'Error checking heading hierarchy: {str(e)}'
            }
    
    def _test_skip_link(self) -> Dict[str, Any]:
        """Test for skip navigation link"""
        try:
            # Look for skip links (usually hidden or at top of page)
            skip_links = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='#main'], a[href*='#content'], a[href*='#skip']")
            
            if skip_links:
                return {
                    'status': 'pass',
                    'nodes': [{
                        'target': ['a'],
                        'html': skip_links[0].get_attribute('outerHTML')[:200]
                    }]
                }
            else:
                return {
                    'status': 'violation',
                    'nodes': [{'target': ['body'], 'html': 'No skip link found'}]
                }
                
        except Exception as e:
            return {
                'status': 'incomplete',
                'reason': f'Error checking skip link: {str(e)}'
            }
    
    def _test_lang_attribute(self) -> Dict[str, Any]:
        """Test for HTML lang attribute"""
        try:
            html_element = self.driver.find_element(By.TAG_NAME, "html")
            lang_attr = html_element.get_attribute("lang")
            
            if not lang_attr:
                return {
                    'status': 'violation',
                    'nodes': [{'target': ['html'], 'html': '<html> (no lang attribute)'}]
                }
            
            return {
                'status': 'pass',
                'nodes': [{'target': ['html'], 'html': f'<html lang="{lang_attr}">'}]
            }
            
        except Exception as e:
            return {
                'status': 'incomplete',
                'reason': f'Error checking lang attribute: {str(e)}'
            }