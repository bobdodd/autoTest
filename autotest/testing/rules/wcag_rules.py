"""
WCAG 2.1 compliance rules for AutoTest accessibility testing
"""

import re
import colorsys
from typing import Dict, List, Optional, Any, Tuple
from urllib.parse import urlparse

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import WebDriverException

from autotest.utils.logger import LoggerMixin


class WCAGRules(LoggerMixin):
    """WCAG 2.1 compliance test rules implementation"""
    
    def __init__(self, driver: webdriver.Chrome | webdriver.Firefox):
        """
        Initialize WCAG rules
        
        Args:
            driver: Selenium WebDriver instance
        """
        self.driver = driver
    
    def test_color_contrast_advanced(self) -> Dict[str, Any]:
        """
        Advanced color contrast testing (WCAG 2.1 AA compliance)
        Tests for 4.5:1 ratio for normal text, 3:1 for large text
        """
        try:
            # Get all text elements
            text_elements = self.driver.find_elements(
                By.CSS_SELECTOR, 
                "p, h1, h2, h3, h4, h5, h6, span, div, a, li, td, th, label, button"
            )
            
            violations = []
            passes = []
            
            for element in text_elements[:20]:  # Limit for performance
                try:
                    text_content = element.get_attribute("textContent").strip()
                    if not text_content or len(text_content) < 3:
                        continue
                    
                    # Get computed styles
                    color = self._get_computed_style(element, 'color')
                    background_color = self._get_computed_style(element, 'backgroundColor')
                    font_size = self._get_computed_style(element, 'fontSize')
                    font_weight = self._get_computed_style(element, 'fontWeight')
                    
                    # Parse colors
                    text_rgb = self._parse_color(color)
                    bg_rgb = self._parse_color(background_color)
                    
                    if not text_rgb or not bg_rgb:
                        continue
                    
                    # Calculate contrast ratio
                    contrast_ratio = self._calculate_contrast_ratio(text_rgb, bg_rgb)
                    
                    # Determine if text is large (18pt+ or 14pt+ bold)
                    font_size_px = self._parse_font_size(font_size)
                    is_bold = self._is_bold_font(font_weight)
                    is_large_text = (font_size_px >= 18) or (font_size_px >= 14 and is_bold)
                    
                    # Check compliance
                    required_ratio = 3.0 if is_large_text else 4.5
                    
                    if contrast_ratio < required_ratio:
                        violations.append({
                            'target': [element.tag_name],
                            'html': element.get_attribute('outerHTML')[:200],
                            'data': {
                                'contrast_ratio': round(contrast_ratio, 2),
                                'required_ratio': required_ratio,
                                'text_color': color,
                                'background_color': background_color,
                                'font_size': font_size,
                                'is_large_text': is_large_text
                            }
                        })
                    else:
                        passes.append({
                            'target': [element.tag_name],
                            'html': element.get_attribute('outerHTML')[:200],
                            'data': {
                                'contrast_ratio': round(contrast_ratio, 2),
                                'required_ratio': required_ratio
                            }
                        })
                        
                except Exception as e:
                    self.logger.debug(f"Error checking contrast for element: {e}")
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
                    'status': 'incomplete',
                    'reason': 'No text elements found for contrast testing'
                }
                
        except Exception as e:
            return {
                'status': 'incomplete',
                'reason': f'Error testing color contrast: {str(e)}'
            }
    
    def test_keyboard_navigation(self) -> Dict[str, Any]:
        """
        Test keyboard navigation functionality
        """
        try:
            # Get all focusable elements
            focusable_elements = self.driver.find_elements(
                By.CSS_SELECTOR,
                'a[href], button, input, select, textarea, [tabindex]:not([tabindex="-1"])'
            )
            
            if not focusable_elements:
                return {
                    'status': 'pass',
                    'nodes': [{'target': ['body'], 'html': 'No focusable elements found'}]
                }
            
            violations = []
            passes = []
            
            for element in focusable_elements[:10]:  # Limit for performance
                try:
                    # Focus the element
                    self.driver.execute_script("arguments[0].focus()", element)
                    
                    # Check if element is actually focused
                    focused_element = self.driver.switch_to.active_element
                    
                    if focused_element == element:
                        # Check for visible focus indicator
                        outline = self._get_computed_style(element, 'outline')
                        outline_width = self._get_computed_style(element, 'outlineWidth')
                        box_shadow = self._get_computed_style(element, 'boxShadow')
                        border = self._get_computed_style(element, 'border')
                        
                        has_focus_indicator = (
                            outline != 'none' and outline_width != '0px' or
                            box_shadow != 'none' or
                            'focus' in element.get_attribute('class') or ''
                        )
                        
                        if has_focus_indicator:
                            passes.append({
                                'target': [element.tag_name],
                                'html': element.get_attribute('outerHTML')[:200]
                            })
                        else:
                            violations.append({
                                'target': [element.tag_name],
                                'html': element.get_attribute('outerHTML')[:200],
                                'data': {
                                    'outline': outline,
                                    'box_shadow': box_shadow
                                }
                            })
                    
                except Exception as e:
                    self.logger.debug(f"Error testing keyboard focus: {e}")
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
                'reason': f'Error testing keyboard navigation: {str(e)}'
            }
    
    def test_aria_labels_and_roles(self) -> Dict[str, Any]:
        """
        Test ARIA labels and roles for accessibility
        """
        try:
            # Elements that should have ARIA attributes
            interactive_elements = self.driver.find_elements(
                By.CSS_SELECTOR,
                'button, input, select, textarea, a, [role="button"], [role="link"], [role="tab"]'
            )
            
            violations = []
            passes = []
            
            for element in interactive_elements:
                try:
                    aria_label = element.get_attribute('aria-label')
                    aria_labelledby = element.get_attribute('aria-labelledby')
                    aria_describedby = element.get_attribute('aria-describedby')
                    role = element.get_attribute('role')
                    text_content = element.get_attribute('textContent').strip()
                    
                    # Check if element has accessible name
                    has_accessible_name = bool(aria_label or aria_labelledby or text_content)
                    
                    # Special checks for form inputs
                    if element.tag_name.lower() in ['input', 'select', 'textarea']:
                        input_type = element.get_attribute('type')
                        if input_type not in ['hidden', 'submit', 'button', 'reset']:
                            # Form inputs need labels
                            label_for = None
                            input_id = element.get_attribute('id')
                            if input_id:
                                try:
                                    label_for = self.driver.find_element(
                                        By.CSS_SELECTOR, f'label[for="{input_id}"]'
                                    )
                                except:
                                    pass
                            
                            if not (aria_label or aria_labelledby or label_for):
                                violations.append({
                                    'target': [element.tag_name],
                                    'html': element.get_attribute('outerHTML')[:200],
                                    'data': {'missing': 'label or aria-label'}
                                })
                                continue
                    
                    # Check for proper ARIA usage
                    if role:
                        valid_roles = [
                            'button', 'link', 'tab', 'tabpanel', 'dialog', 'alert',
                            'navigation', 'main', 'banner', 'contentinfo', 'search',
                            'region', 'article', 'section', 'aside', 'heading',
                            'list', 'listitem', 'table', 'row', 'cell'
                        ]
                        
                        if role not in valid_roles:
                            violations.append({
                                'target': [element.tag_name],
                                'html': element.get_attribute('outerHTML')[:200],
                                'data': {'invalid_role': role}
                            })
                            continue
                    
                    if has_accessible_name:
                        passes.append({
                            'target': [element.tag_name],
                            'html': element.get_attribute('outerHTML')[:200]
                        })
                    else:
                        violations.append({
                            'target': [element.tag_name],
                            'html': element.get_attribute('outerHTML')[:200],
                            'data': {'missing': 'accessible name'}
                        })
                        
                except Exception as e:
                    self.logger.debug(f"Error checking ARIA attributes: {e}")
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
                    'nodes': [{'target': ['body'], 'html': 'No interactive elements found'}]
                }
                
        except Exception as e:
            return {
                'status': 'incomplete',
                'reason': f'Error testing ARIA attributes: {str(e)}'
            }
    
    def test_landmark_regions(self) -> Dict[str, Any]:
        """
        Test for proper landmark regions (WCAG 2.1)
        """
        try:
            # Check for main landmark
            main_elements = self.driver.find_elements(
                By.CSS_SELECTOR, 'main, [role="main"]'
            )
            
            # Check for navigation landmarks
            nav_elements = self.driver.find_elements(
                By.CSS_SELECTOR, 'nav, [role="navigation"]'
            )
            
            # Check for banner (header)
            banner_elements = self.driver.find_elements(
                By.CSS_SELECTOR, 'header, [role="banner"]'
            )
            
            # Check for contentinfo (footer)
            footer_elements = self.driver.find_elements(
                By.CSS_SELECTOR, 'footer, [role="contentinfo"]'
            )
            
            violations = []
            passes = []
            
            # Check main content area
            if not main_elements:
                violations.append({
                    'target': ['body'],
                    'html': 'Missing main content landmark',
                    'data': {'missing_landmark': 'main'}
                })
            else:
                passes.append({
                    'target': ['main'],
                    'html': main_elements[0].get_attribute('outerHTML')[:200]
                })
            
            # Multiple main elements is a violation
            if len(main_elements) > 1:
                violations.append({
                    'target': ['main'],
                    'html': 'Multiple main landmarks found',
                    'data': {'count': len(main_elements)}
                })
            
            # Check for navigation (recommended but not required)
            if nav_elements:
                passes.append({
                    'target': ['nav'],
                    'html': nav_elements[0].get_attribute('outerHTML')[:200]
                })
            
            # Check for proper landmark structure
            all_landmarks = self.driver.find_elements(
                By.CSS_SELECTOR, 
                'main, nav, header, footer, aside, section, [role="main"], [role="navigation"], [role="banner"], [role="contentinfo"], [role="complementary"], [role="region"]'
            )
            
            for landmark in all_landmarks:
                try:
                    # Check if landmark has accessible name when required
                    role = landmark.get_attribute('role') or landmark.tag_name.lower()
                    
                    if role in ['region', 'navigation'] and len(self.driver.find_elements(By.CSS_SELECTOR, f'[role="{role}"], {role}')) > 1:
                        # Multiple regions/navs should have labels
                        aria_label = landmark.get_attribute('aria-label')
                        aria_labelledby = landmark.get_attribute('aria-labelledby')
                        
                        if not (aria_label or aria_labelledby):
                            violations.append({
                                'target': [landmark.tag_name],
                                'html': landmark.get_attribute('outerHTML')[:200],
                                'data': {'missing_label_for_multiple': role}
                            })
                        else:
                            passes.append({
                                'target': [landmark.tag_name],
                                'html': landmark.get_attribute('outerHTML')[:200]
                            })
                    
                except Exception as e:
                    self.logger.debug(f"Error checking landmark: {e}")
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
                'reason': f'Error testing landmark regions: {str(e)}'
            }
    
    def test_table_accessibility(self) -> Dict[str, Any]:
        """
        Test data table accessibility
        """
        try:
            tables = self.driver.find_elements(By.TAG_NAME, 'table')
            
            if not tables:
                return {
                    'status': 'pass',
                    'nodes': [{'target': ['body'], 'html': 'No tables found'}]
                }
            
            violations = []
            passes = []
            
            for table in tables:
                try:
                    # Check for table headers
                    th_elements = table.find_elements(By.TAG_NAME, 'th')
                    thead_elements = table.find_elements(By.TAG_NAME, 'thead')
                    
                    # Check for caption
                    caption_elements = table.find_elements(By.TAG_NAME, 'caption')
                    
                    # Check for summary or aria-label
                    summary = table.get_attribute('summary')
                    aria_label = table.get_attribute('aria-label')
                    aria_labelledby = table.get_attribute('aria-labelledby')
                    
                    # Data tables should have headers
                    if not th_elements and not thead_elements:
                        violations.append({
                            'target': ['table'],
                            'html': table.get_attribute('outerHTML')[:200],
                            'data': {'missing': 'table headers'}
                        })
                        continue
                    
                    # Check header scope attributes
                    header_issues = []
                    for th in th_elements:
                        scope = th.get_attribute('scope')
                        if not scope:
                            header_issues.append('Missing scope attribute')
                    
                    # Complex tables should have caption or description
                    rows = table.find_elements(By.TAG_NAME, 'tr')
                    is_complex = len(rows) > 5 or len(th_elements) > 3
                    
                    if is_complex and not (caption_elements or summary or aria_label or aria_labelledby):
                        violations.append({
                            'target': ['table'],
                            'html': table.get_attribute('outerHTML')[:200],
                            'data': {'missing': 'table caption or description'}
                        })
                        continue
                    
                    if header_issues:
                        violations.append({
                            'target': ['table'],
                            'html': table.get_attribute('outerHTML')[:200],
                            'data': {'header_issues': header_issues}
                        })
                    else:
                        passes.append({
                            'target': ['table'],
                            'html': table.get_attribute('outerHTML')[:200]
                        })
                        
                except Exception as e:
                    self.logger.debug(f"Error checking table accessibility: {e}")
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
                'reason': f'Error testing table accessibility: {str(e)}'
            }
    
    def test_media_alternatives(self) -> Dict[str, Any]:
        """
        Test multimedia content for alternatives (WCAG 2.1)
        """
        try:
            violations = []
            passes = []
            
            # Check video elements
            videos = self.driver.find_elements(By.TAG_NAME, 'video')
            for video in videos:
                try:
                    # Check for captions/subtitles
                    tracks = video.find_elements(By.TAG_NAME, 'track')
                    caption_tracks = [t for t in tracks if t.get_attribute('kind') == 'captions']
                    subtitle_tracks = [t for t in tracks if t.get_attribute('kind') == 'subtitles']
                    
                    if not (caption_tracks or subtitle_tracks):
                        violations.append({
                            'target': ['video'],
                            'html': video.get_attribute('outerHTML')[:200],
                            'data': {'missing': 'captions or subtitles'}
                        })
                    else:
                        passes.append({
                            'target': ['video'],
                            'html': video.get_attribute('outerHTML')[:200]
                        })
                        
                except Exception as e:
                    self.logger.debug(f"Error checking video: {e}")
                    continue
            
            # Check audio elements
            audios = self.driver.find_elements(By.TAG_NAME, 'audio')
            for audio in audios:
                try:
                    # Audio should have transcript or description
                    # This is difficult to test automatically, so we'll mark as incomplete
                    passes.append({
                        'target': ['audio'],
                        'html': audio.get_attribute('outerHTML')[:200],
                        'data': {'note': 'Manual verification needed for transcript'}
                    })
                    
                except Exception as e:
                    self.logger.debug(f"Error checking audio: {e}")
                    continue
            
            # Check for embedded media (iframe, object, embed)
            embedded_media = self.driver.find_elements(By.CSS_SELECTOR, 'iframe, object, embed')
            for media in embedded_media:
                try:
                    title = media.get_attribute('title')
                    aria_label = media.get_attribute('aria-label')
                    
                    if not (title or aria_label):
                        violations.append({
                            'target': [media.tag_name],
                            'html': media.get_attribute('outerHTML')[:200],
                            'data': {'missing': 'title or aria-label for embedded media'}
                        })
                    else:
                        passes.append({
                            'target': [media.tag_name],
                            'html': media.get_attribute('outerHTML')[:200]
                        })
                        
                except Exception as e:
                    self.logger.debug(f"Error checking embedded media: {e}")
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
                    'nodes': [{'target': ['body'], 'html': 'No multimedia content found'}]
                }
                
        except Exception as e:
            return {
                'status': 'incomplete',
                'reason': f'Error testing media alternatives: {str(e)}'
            }
    
    # Helper methods
    
    def _get_computed_style(self, element, property_name: str) -> str:
        """Get computed CSS style for an element"""
        try:
            return self.driver.execute_script(
                f"return window.getComputedStyle(arguments[0]).{property_name}",
                element
            )
        except Exception:
            return ""
    
    def _parse_color(self, color_string: str) -> Optional[Tuple[int, int, int]]:
        """Parse CSS color string to RGB tuple"""
        if not color_string:
            return None
        
        # Handle rgb() format
        rgb_match = re.match(r'rgb\((\d+),\s*(\d+),\s*(\d+)\)', color_string)
        if rgb_match:
            return tuple(int(x) for x in rgb_match.groups())
        
        # Handle rgba() format (ignore alpha for contrast calculation)
        rgba_match = re.match(r'rgba\((\d+),\s*(\d+),\s*(\d+),\s*[\d.]+\)', color_string)
        if rgba_match:
            return tuple(int(x) for x in rgba_match.groups())
        
        # Handle transparent
        if color_string == 'transparent' or color_string == 'rgba(0, 0, 0, 0)':
            return (255, 255, 255)  # Assume white background for transparent
        
        # Handle hex colors (basic implementation)
        if color_string.startswith('#'):
            try:
                hex_color = color_string[1:]
                if len(hex_color) == 3:
                    hex_color = ''.join([c*2 for c in hex_color])
                if len(hex_color) == 6:
                    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            except ValueError:
                pass
        
        return None
    
    def _calculate_contrast_ratio(self, rgb1: Tuple[int, int, int], rgb2: Tuple[int, int, int]) -> float:
        """Calculate contrast ratio between two colors"""
        def relative_luminance(rgb):
            """Calculate relative luminance of a color"""
            r, g, b = [x / 255.0 for x in rgb]
            
            def gamma_correct(c):
                return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
            
            r, g, b = map(gamma_correct, [r, g, b])
            return 0.2126 * r + 0.7152 * g + 0.0722 * b
        
        l1 = relative_luminance(rgb1)
        l2 = relative_luminance(rgb2)
        
        # Ensure l1 is the lighter color
        if l1 < l2:
            l1, l2 = l2, l1
        
        return (l1 + 0.05) / (l2 + 0.05)
    
    def _parse_font_size(self, font_size_string: str) -> float:
        """Parse font size string to pixels"""
        if not font_size_string:
            return 16.0  # Default font size
        
        if font_size_string.endswith('px'):
            try:
                return float(font_size_string[:-2])
            except ValueError:
                return 16.0
        
        # Handle other units (simplified)
        if font_size_string.endswith('pt'):
            try:
                pt_size = float(font_size_string[:-2])
                return pt_size * 1.33  # Rough conversion pt to px
            except ValueError:
                return 16.0
        
        return 16.0
    
    def _is_bold_font(self, font_weight_string: str) -> bool:
        """Check if font weight is bold"""
        if not font_weight_string:
            return False
        
        if font_weight_string in ['bold', 'bolder']:
            return True
        
        try:
            weight = int(font_weight_string)
            return weight >= 700
        except ValueError:
            return False