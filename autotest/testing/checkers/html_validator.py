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
HTML semantic validation checker for AutoTest
"""

import re
from typing import Dict, List, Optional, Any, Set
from collections import Counter

from selenium import webdriver
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup

from autotest.utils.logger import LoggerMixin


class HTMLSemanticValidator(LoggerMixin):
    """HTML semantic structure validator"""
    
    def __init__(self, driver: webdriver.Chrome | webdriver.Firefox):
        """
        Initialize HTML validator
        
        Args:
            driver: Selenium WebDriver instance
        """
        self.driver = driver
    
    def validate_html_structure(self) -> Dict[str, Any]:
        """
        Validate overall HTML structure and semantics
        """
        try:
            # Get page source and parse with BeautifulSoup
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            violations = []
            passes = []
            
            # Check basic HTML structure
            html_element = soup.find('html')
            if not html_element:
                violations.append({
                    'target': ['document'],
                    'html': 'Missing <html> element',
                    'data': {'missing': 'html element'}
                })
            else:
                passes.append({
                    'target': ['html'],
                    'html': str(html_element)[:200]
                })
            
            # Check for head element
            head_element = soup.find('head')
            if not head_element:
                violations.append({
                    'target': ['document'],
                    'html': 'Missing <head> element',
                    'data': {'missing': 'head element'}
                })
            else:
                passes.append({
                    'target': ['head'],
                    'html': str(head_element)[:200]
                })
            
            # Check for body element
            body_element = soup.find('body')
            if not body_element:
                violations.append({
                    'target': ['document'],
                    'html': 'Missing <body> element',
                    'data': {'missing': 'body element'}
                })
            else:
                passes.append({
                    'target': ['body'],
                    'html': str(body_element)[:200]
                })
            
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
                'reason': f'Error validating HTML structure: {str(e)}'
            }
    
    def validate_semantic_elements(self) -> Dict[str, Any]:
        """
        Validate proper use of HTML5 semantic elements
        """
        try:
            violations = []
            passes = []
            
            # Check for semantic HTML5 elements
            semantic_elements = {
                'header': 'Page or section header',
                'nav': 'Navigation links',
                'main': 'Main content area',
                'article': 'Independent content',
                'section': 'Thematic grouping',
                'aside': 'Sidebar content',
                'footer': 'Page or section footer'
            }
            
            found_semantics = []
            
            for element_name, description in semantic_elements.items():
                elements = self.driver.find_elements(By.TAG_NAME, element_name)
                if elements:
                    found_semantics.append(element_name)
                    passes.append({
                        'target': [element_name],
                        'html': elements[0].get_attribute('outerHTML')[:200],
                        'data': {'description': description}
                    })
            
            # Check for proper nesting
            main_elements = self.driver.find_elements(By.TAG_NAME, 'main')
            if len(main_elements) > 1:
                violations.append({
                    'target': ['main'],
                    'html': 'Multiple <main> elements found',
                    'data': {'count': len(main_elements), 'issue': 'Only one main element allowed'}
                })
            
            # Check for divitis (excessive div usage without semantic meaning)
            divs = self.driver.find_elements(By.TAG_NAME, 'div')
            total_elements = len(self.driver.find_elements(By.CSS_SELECTOR, '*'))
            
            if len(divs) > total_elements * 0.3:  # More than 30% divs might indicate divitis
                violations.append({
                    'target': ['div'],
                    'html': f'{len(divs)} div elements found',
                    'data': {
                        'div_count': len(divs),
                        'total_elements': total_elements,
                        'percentage': round((len(divs) / total_elements) * 100, 1),
                        'issue': 'Excessive div usage - consider semantic alternatives'
                    }
                })
            
            # Check for proper use of headings vs styling
            styled_headings = self.driver.find_elements(
                By.CSS_SELECTOR, 
                'div[class*="head"], div[class*="title"], span[class*="head"], span[class*="title"]'
            )
            
            for element in styled_headings[:5]:  # Check first 5
                text_content = element.get_attribute('textContent').strip()
                if text_content and len(text_content) < 100:  # Likely a heading
                    violations.append({
                        'target': [element.tag_name],
                        'html': element.get_attribute('outerHTML')[:200],
                        'data': {
                            'issue': 'Element appears to be a heading but uses generic HTML',
                            'suggestion': 'Use h1-h6 elements for headings'
                        }
                    })
            
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
                'reason': f'Error validating semantic elements: {str(e)}'
            }
    
    def validate_list_structure(self) -> Dict[str, Any]:
        """
        Validate proper list structure and usage
        """
        try:
            violations = []
            passes = []
            
            # Check ordered lists
            ol_elements = self.driver.find_elements(By.TAG_NAME, 'ol')
            for ol in ol_elements:
                try:
                    # Check if ol contains only li elements as direct children
                    direct_children = ol.find_elements(By.XPATH, './*')
                    non_li_children = [child for child in direct_children 
                                     if child.tag_name.lower() != 'li']
                    
                    if non_li_children:
                        violations.append({
                            'target': ['ol'],
                            'html': ol.get_attribute('outerHTML')[:200],
                            'data': {
                                'issue': 'Ordered list contains non-li direct children',
                                'invalid_children': [child.tag_name for child in non_li_children]
                            }
                        })
                    else:
                        passes.append({
                            'target': ['ol'],
                            'html': ol.get_attribute('outerHTML')[:200]
                        })
                        
                except Exception as e:
                    self.logger.debug(f"Error checking ol element: {e}")
                    continue
            
            # Check unordered lists
            ul_elements = self.driver.find_elements(By.TAG_NAME, 'ul')
            for ul in ul_elements:
                try:
                    # Check if ul contains only li elements as direct children
                    direct_children = ul.find_elements(By.XPATH, './*')
                    non_li_children = [child for child in direct_children 
                                     if child.tag_name.lower() != 'li']
                    
                    if non_li_children:
                        violations.append({
                            'target': ['ul'],
                            'html': ul.get_attribute('outerHTML')[:200],
                            'data': {
                                'issue': 'Unordered list contains non-li direct children',
                                'invalid_children': [child.tag_name for child in non_li_children]
                            }
                        })
                    else:
                        passes.append({
                            'target': ['ul'],
                            'html': ul.get_attribute('outerHTML')[:200]
                        })
                        
                except Exception as e:
                    self.logger.debug(f"Error checking ul element: {e}")
                    continue
            
            # Check definition lists
            dl_elements = self.driver.find_elements(By.TAG_NAME, 'dl')
            for dl in dl_elements:
                try:
                    # Check if dl contains only dt and dd elements
                    direct_children = dl.find_elements(By.XPATH, './*')
                    invalid_children = [child for child in direct_children 
                                      if child.tag_name.lower() not in ['dt', 'dd']]
                    
                    if invalid_children:
                        violations.append({
                            'target': ['dl'],
                            'html': dl.get_attribute('outerHTML')[:200],
                            'data': {
                                'issue': 'Definition list contains invalid direct children',
                                'invalid_children': [child.tag_name for child in invalid_children]
                            }
                        })
                    else:
                        passes.append({
                            'target': ['dl'],
                            'html': dl.get_attribute('outerHTML')[:200]
                        })
                        
                except Exception as e:
                    self.logger.debug(f"Error checking dl element: {e}")
                    continue
            
            # Check for fake lists (divs/spans that should be lists)
            potential_lists = self.driver.find_elements(
                By.CSS_SELECTOR,
                'div[class*="list"], div[class*="menu"], div[class*="nav"] > div, div[class*="item"]'
            )
            
            for element in potential_lists[:5]:  # Check first 5
                try:
                    # Look for repeated similar child elements
                    children = element.find_elements(By.XPATH, './*')
                    if len(children) >= 3:  # 3 or more similar children might be a list
                        # Check if children have similar classes/structure
                        child_tags = [child.tag_name for child in children]
                        if len(set(child_tags)) == 1 and child_tags[0] == 'div':
                            violations.append({
                                'target': ['div'],
                                'html': element.get_attribute('outerHTML')[:200],
                                'data': {
                                    'issue': 'Element appears to be a list but uses div elements',
                                    'suggestion': 'Consider using ul/ol with li elements'
                                }
                            })
                            
                except Exception as e:
                    self.logger.debug(f"Error checking potential list: {e}")
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
                    'nodes': [{'target': ['body'], 'html': 'No list elements found'}]
                }
                
        except Exception as e:
            return {
                'status': 'incomplete',
                'reason': f'Error validating list structure: {str(e)}'
            }
    
    def validate_form_structure(self) -> Dict[str, Any]:
        """
        Validate form structure and semantics
        """
        try:
            violations = []
            passes = []
            
            forms = self.driver.find_elements(By.TAG_NAME, 'form')
            
            if not forms:
                return {
                    'status': 'pass',
                    'nodes': [{'target': ['body'], 'html': 'No forms found'}]
                }
            
            for form in forms:
                try:
                    # Check for fieldset usage in complex forms
                    inputs = form.find_elements(By.CSS_SELECTOR, 'input, select, textarea')
                    fieldsets = form.find_elements(By.TAG_NAME, 'fieldset')
                    
                    # Forms with many inputs should use fieldsets
                    if len(inputs) > 5 and not fieldsets:
                        violations.append({
                            'target': ['form'],
                            'html': form.get_attribute('outerHTML')[:200],
                            'data': {
                                'issue': 'Complex form should use fieldset elements for grouping',
                                'input_count': len(inputs)
                            }
                        })
                    else:
                        passes.append({
                            'target': ['form'],
                            'html': form.get_attribute('outerHTML')[:200]
                        })
                    
                    # Check fieldset structure
                    for fieldset in fieldsets:
                        legends = fieldset.find_elements(By.TAG_NAME, 'legend')
                        if not legends:
                            violations.append({
                                'target': ['fieldset'],
                                'html': fieldset.get_attribute('outerHTML')[:200],
                                'data': {'issue': 'Fieldset missing legend element'}
                            })
                        elif len(legends) > 1:
                            violations.append({
                                'target': ['fieldset'],
                                'html': fieldset.get_attribute('outerHTML')[:200],
                                'data': {'issue': 'Multiple legend elements in fieldset'}
                            })
                        else:
                            passes.append({
                                'target': ['fieldset'],
                                'html': fieldset.get_attribute('outerHTML')[:200]
                            })
                    
                    # Check for proper button usage
                    buttons = form.find_elements(By.TAG_NAME, 'button')
                    input_buttons = form.find_elements(By.CSS_SELECTOR, 'input[type="submit"], input[type="button"], input[type="reset"]')
                    
                    # Forms should have submit mechanism
                    if not buttons and not input_buttons:
                        violations.append({
                            'target': ['form'],
                            'html': form.get_attribute('outerHTML')[:200],
                            'data': {'issue': 'Form has no submit button'}
                        })
                    
                except Exception as e:
                    self.logger.debug(f"Error checking form: {e}")
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
                'reason': f'Error validating form structure: {str(e)}'
            }
    
    def validate_heading_structure(self) -> Dict[str, Any]:
        """
        Validate heading hierarchy and structure
        """
        try:
            violations = []
            passes = []
            
            # Get all headings
            headings = self.driver.find_elements(By.CSS_SELECTOR, 'h1, h2, h3, h4, h5, h6')
            
            if not headings:
                violations.append({
                    'target': ['body'],
                    'html': 'No heading elements found',
                    'data': {'issue': 'Page should have at least one heading'}
                })
                return {
                    'status': 'violation',
                    'nodes': violations
                }
            
            # Extract heading levels
            heading_levels = []
            for heading in headings:
                level = int(heading.tag_name[1])  # Extract number from h1, h2, etc.
                heading_levels.append((level, heading))
            
            # Check for h1
            h1_headings = [h for level, h in heading_levels if level == 1]
            if not h1_headings:
                violations.append({
                    'target': ['body'],
                    'html': 'No h1 heading found',
                    'data': {'issue': 'Page should have exactly one h1 heading'}
                })
            elif len(h1_headings) > 1:
                violations.append({
                    'target': ['h1'],
                    'html': f'{len(h1_headings)} h1 headings found',
                    'data': {
                        'issue': 'Multiple h1 headings found',
                        'count': len(h1_headings)
                    }
                })
            else:
                passes.append({
                    'target': ['h1'],
                    'html': h1_headings[0].get_attribute('outerHTML')[:200]
                })
            
            # Check heading hierarchy (no skipping levels)
            previous_level = 0
            for level, heading in heading_levels:
                if previous_level > 0 and level > previous_level + 1:
                    violations.append({
                        'target': [heading.tag_name],
                        'html': heading.get_attribute('outerHTML')[:200],
                        'data': {
                            'issue': f'Heading level jumps from h{previous_level} to h{level}',
                            'previous_level': previous_level,
                            'current_level': level
                        }
                    })
                else:
                    passes.append({
                        'target': [heading.tag_name],
                        'html': heading.get_attribute('outerHTML')[:200]
                    })
                
                previous_level = level
            
            # Check for empty headings
            for level, heading in heading_levels:
                text_content = heading.get_attribute('textContent').strip()
                if not text_content:
                    violations.append({
                        'target': [heading.tag_name],
                        'html': heading.get_attribute('outerHTML')[:200],
                        'data': {'issue': 'Empty heading element'}
                    })
            
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
                'reason': f'Error validating heading structure: {str(e)}'
            }
    
    def validate_document_metadata(self) -> Dict[str, Any]:
        """
        Validate document metadata elements
        """
        try:
            violations = []
            passes = []
            
            # Check meta viewport
            viewport_meta = self.driver.find_elements(
                By.CSS_SELECTOR, 'meta[name="viewport"]'
            )
            
            if not viewport_meta:
                violations.append({
                    'target': ['head'],
                    'html': 'Missing viewport meta tag',
                    'data': {
                        'issue': 'Missing viewport meta tag',
                        'suggestion': 'Add <meta name="viewport" content="width=device-width, initial-scale=1">'
                    }
                })
            else:
                passes.append({
                    'target': ['meta'],
                    'html': viewport_meta[0].get_attribute('outerHTML')
                })
            
            # Check meta description
            description_meta = self.driver.find_elements(
                By.CSS_SELECTOR, 'meta[name="description"]'
            )
            
            if not description_meta:
                violations.append({
                    'target': ['head'],
                    'html': 'Missing meta description',
                    'data': {
                        'issue': 'Missing meta description',
                        'suggestion': 'Add meta description for SEO and accessibility'
                    }
                })
            else:
                description_content = description_meta[0].get_attribute('content')
                if not description_content or len(description_content.strip()) < 10:
                    violations.append({
                        'target': ['meta'],
                        'html': description_meta[0].get_attribute('outerHTML'),
                        'data': {'issue': 'Meta description is too short or empty'}
                    })
                else:
                    passes.append({
                        'target': ['meta'],
                        'html': description_meta[0].get_attribute('outerHTML')
                    })
            
            # Check charset declaration
            charset_meta = self.driver.find_elements(
                By.CSS_SELECTOR, 'meta[charset], meta[http-equiv="Content-Type"]'
            )
            
            if not charset_meta:
                violations.append({
                    'target': ['head'],
                    'html': 'Missing charset declaration',
                    'data': {
                        'issue': 'Missing charset declaration',
                        'suggestion': 'Add <meta charset="utf-8"> in head'
                    }
                })
            else:
                passes.append({
                    'target': ['meta'],
                    'html': charset_meta[0].get_attribute('outerHTML')
                })
            
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
                'reason': f'Error validating document metadata: {str(e)}'
            }