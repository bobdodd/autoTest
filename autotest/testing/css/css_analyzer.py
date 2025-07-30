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
CSS Analyzer for AutoTest
Provides comprehensive CSS inspection and analysis capabilities for accessibility testing.
"""

import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import WebDriverException, JavascriptException


class CSSAnalyzer:
    """
    Comprehensive CSS analysis for accessibility testing.
    Extracts, analyzes, and reports on CSS properties relevant to accessibility.
    """
    
    def __init__(self, driver):
        """
        Initialize CSS analyzer with WebDriver instance
        
        Args:
            driver: Selenium WebDriver instance
        """
        self.driver = driver
        self.logger = logging.getLogger(__name__)
    
    def extract_all_styles(self, element: WebElement) -> Dict[str, Any]:
        """
        Extract all computed CSS styles for an element
        
        Args:
            element: WebElement to analyze
            
        Returns:
            Dictionary containing all computed CSS properties
        """
        try:
            # JavaScript to extract all computed styles
            script = """
            var element = arguments[0];
            var styles = window.getComputedStyle(element);
            var result = {};
            
            // Get all CSS properties
            for (var i = 0; i < styles.length; i++) {
                var property = styles[i];
                result[property] = styles.getPropertyValue(property);
            }
            
            // Add some derived accessibility properties
            result._accessibility = {
                isVisible: element.offsetWidth > 0 && element.offsetHeight > 0,
                isInteractive: ['A', 'BUTTON', 'INPUT', 'SELECT', 'TEXTAREA'].includes(element.tagName) ||
                              element.hasAttribute('tabindex') ||
                              element.hasAttribute('onclick'),
                boundingRect: element.getBoundingClientRect(),
                tagName: element.tagName,
                attributes: {}
            };
            
            // Get relevant attributes
            var attrs = ['aria-label', 'aria-labelledby', 'aria-describedby', 'role', 'tabindex', 'alt', 'title'];
            attrs.forEach(function(attr) {
                if (element.hasAttribute(attr)) {
                    result._accessibility.attributes[attr] = element.getAttribute(attr);
                }
            });
            
            return result;
            """
            
            return self.driver.execute_script(script, element)
            
        except (WebDriverException, JavascriptException) as e:
            self.logger.error(f"Error extracting styles: {e}")
            return {}
    
    def get_stylesheet_rules(self) -> List[Dict[str, Any]]:
        """
        Get all CSS rules from stylesheets loaded on the page
        
        Returns:
            List of CSS rules with selectors and properties
        """
        try:
            script = """
            var rules = [];
            
            // Iterate through all stylesheets
            for (var i = 0; i < document.styleSheets.length; i++) {
                try {
                    var sheet = document.styleSheets[i];
                    var cssRules = sheet.cssRules || sheet.rules;
                    
                    for (var j = 0; j < cssRules.length; j++) {
                        var rule = cssRules[j];
                        
                        if (rule.type === CSSRule.STYLE_RULE) {
                            var ruleInfo = {
                                selector: rule.selectorText,
                                properties: {},
                                href: sheet.href,
                                index: j
                            };
                            
                            // Extract properties
                            for (var k = 0; k < rule.style.length; k++) {
                                var prop = rule.style[k];
                                ruleInfo.properties[prop] = rule.style.getPropertyValue(prop);
                            }
                            
                            rules.push(ruleInfo);
                        }
                    }
                } catch (e) {
                    // Skip stylesheets we can't access (CORS issues)
                    continue;
                }
            }
            
            return rules;
            """
            
            return self.driver.execute_script(script)
            
        except (WebDriverException, JavascriptException) as e:
            self.logger.error(f"Error getting stylesheet rules: {e}")
            return []
    
    def analyze_accessibility_properties(self, element: WebElement) -> Dict[str, Any]:
        """
        Analyze CSS properties specifically relevant to accessibility
        
        Args:
            element: WebElement to analyze
            
        Returns:
            Dictionary with accessibility-focused CSS analysis
        """
        try:
            styles = self.extract_all_styles(element)
            
            if not styles:
                return {}
            
            analysis = {
                'color_analysis': self._analyze_colors(styles),
                'typography_analysis': self._analyze_typography(styles),
                'layout_analysis': self._analyze_layout(styles),
                'interaction_analysis': self._analyze_interactions(styles),
                'motion_analysis': self._analyze_motion(styles),
                'visibility_analysis': self._analyze_visibility(styles)
            }
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing accessibility properties: {e}")
            return {}
    
    def _analyze_colors(self, styles: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze color-related CSS properties for accessibility"""
        return {
            'foreground_color': styles.get('color', 'inherit'),
            'background_color': styles.get('background-color', 'transparent'),
            'border_color': styles.get('border-color', 'transparent'),
            'outline_color': styles.get('outline-color', 'invert'),
            'text_decoration_color': styles.get('text-decoration-color', 'currentcolor'),
            'color_scheme': styles.get('color-scheme', 'normal'),
            'forced_color_adjust': styles.get('forced-color-adjust', 'auto'),
            'potential_issues': self._identify_color_issues(styles)
        }
    
    def _analyze_typography(self, styles: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze typography-related CSS properties"""
        font_size = styles.get('font-size', '16px')
        line_height = styles.get('line-height', 'normal')
        
        return {
            'font_family': styles.get('font-family', 'inherit'),
            'font_size': font_size,
            'font_size_px': self._convert_to_pixels(font_size),
            'font_weight': styles.get('font-weight', 'normal'),
            'font_style': styles.get('font-style', 'normal'),
            'line_height': line_height,
            'line_height_ratio': self._calculate_line_height_ratio(font_size, line_height),
            'letter_spacing': styles.get('letter-spacing', 'normal'),
            'word_spacing': styles.get('word-spacing', 'normal'),
            'text_align': styles.get('text-align', 'start'),
            'text_transform': styles.get('text-transform', 'none'),
            'readability_score': self._calculate_readability_score(styles)
        }
    
    def _analyze_layout(self, styles: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze layout-related CSS properties"""
        return {
            'display': styles.get('display', 'inline'),
            'position': styles.get('position', 'static'),
            'width': styles.get('width', 'auto'),
            'height': styles.get('height', 'auto'),
            'min_width': styles.get('min-width', '0px'),
            'min_height': styles.get('min-height', '0px'),
            'max_width': styles.get('max-width', 'none'),
            'max_height': styles.get('max-height', 'none'),
            'overflow': styles.get('overflow', 'visible'),
            'overflow_x': styles.get('overflow-x', 'visible'),
            'overflow_y': styles.get('overflow-y', 'visible'),
            'flex_properties': self._extract_flex_properties(styles),
            'grid_properties': self._extract_grid_properties(styles),
            'accessibility_concerns': self._identify_layout_issues(styles)
        }
    
    def _analyze_interactions(self, styles: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze interaction-related CSS properties"""
        return {
            'cursor': styles.get('cursor', 'auto'),
            'pointer_events': styles.get('pointer-events', 'auto'),
            'user_select': styles.get('user-select', 'auto'),
            'touch_action': styles.get('touch-action', 'auto'),
            'focus_properties': {
                'outline': styles.get('outline', 'initial'),
                'outline_width': styles.get('outline-width', 'medium'),
                'outline_style': styles.get('outline-style', 'none'),
                'outline_color': styles.get('outline-color', 'invert'),
                'outline_offset': styles.get('outline-offset', '0px'),
                'box_shadow': styles.get('box-shadow', 'none')
            },
            'interaction_issues': self._identify_interaction_issues(styles)
        }
    
    def _analyze_motion(self, styles: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze motion and animation CSS properties"""
        return {
            'animation': styles.get('animation', 'none'),
            'animation_duration': styles.get('animation-duration', '0s'),
            'animation_timing_function': styles.get('animation-timing-function', 'ease'),
            'animation_delay': styles.get('animation-delay', '0s'),
            'animation_iteration_count': styles.get('animation-iteration-count', '1'),
            'animation_direction': styles.get('animation-direction', 'normal'),
            'animation_fill_mode': styles.get('animation-fill-mode', 'none'),
            'animation_play_state': styles.get('animation-play-state', 'running'),
            'transition': styles.get('transition', 'none'),
            'transition_duration': styles.get('transition-duration', '0s'),
            'transform': styles.get('transform', 'none'),
            'motion_issues': self._identify_motion_issues(styles)
        }
    
    def _analyze_visibility(self, styles: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze visibility and display CSS properties"""
        accessibility_info = styles.get('_accessibility', {})
        
        return {
            'visibility': styles.get('visibility', 'visible'),
            'opacity': float(styles.get('opacity', '1')),
            'display': styles.get('display', 'inline'),
            'clip': styles.get('clip', 'auto'),
            'clip_path': styles.get('clip-path', 'none'),
            'is_visible': accessibility_info.get('isVisible', True),
            'is_interactive': accessibility_info.get('isInteractive', False),
            'bounding_rect': accessibility_info.get('boundingRect', {}),
            'visibility_issues': self._identify_visibility_issues(styles, accessibility_info)
        }
    
    def test_style_modifications(self, element: WebElement, modifications: Dict[str, str]) -> Dict[str, Any]:
        """
        Test CSS modifications on an element and analyze the impact
        
        Args:
            element: WebElement to modify
            modifications: Dictionary of CSS property -> value modifications
            
        Returns:
            Analysis of before/after accessibility impact
        """
        try:
            # Get baseline analysis
            before_analysis = self.analyze_accessibility_properties(element)
            
            # Apply modifications
            modification_script = """
            var element = arguments[0];
            var modifications = arguments[1];
            var originalStyles = {};
            
            // Store original styles
            for (var prop in modifications) {
                originalStyles[prop] = element.style[prop] || '';
                element.style[prop] = modifications[prop];
            }
            
            return originalStyles;
            """
            
            original_styles = self.driver.execute_script(modification_script, element, modifications)
            
            # Get analysis after modifications
            after_analysis = self.analyze_accessibility_properties(element)
            
            # Restore original styles
            restore_script = """
            var element = arguments[0];
            var originalStyles = arguments[1];
            
            for (var prop in originalStyles) {
                if (originalStyles[prop] === '') {
                    element.style.removeProperty(prop);
                } else {
                    element.style[prop] = originalStyles[prop];
                }
            }
            """
            
            self.driver.execute_script(restore_script, element, original_styles)
            
            # Compare results
            comparison = self._compare_analyses(before_analysis, after_analysis, modifications)
            
            return {
                'before': before_analysis,
                'after': after_analysis,
                'modifications': modifications,
                'comparison': comparison,
                'accessibility_impact': self._assess_accessibility_impact(comparison)
            }
            
        except Exception as e:
            self.logger.error(f"Error testing style modifications: {e}")
            return {}
    
    def _identify_color_issues(self, styles: Dict[str, Any]) -> List[str]:
        """Identify potential color-related accessibility issues"""
        issues = []
        
        # Check for color-only information
        if styles.get('color') and not styles.get('text-decoration'):
            if 'link' in styles.get('_accessibility', {}).get('tagName', '').lower():
                issues.append("Link relies solely on color for identification")
        
        # Check for low opacity
        opacity = float(styles.get('opacity', 1))
        if opacity < 0.7:
            issues.append(f"Low opacity ({opacity}) may affect readability")
        
        return issues
    
    def _identify_layout_issues(self, styles: Dict[str, Any]) -> List[str]:
        """Identify layout-related accessibility issues"""
        issues = []
        
        # Check for fixed positioning that might block content
        if styles.get('position') == 'fixed':
            issues.append("Fixed positioning may block content for screen magnifier users")
        
        # Check for horizontal scrolling
        overflow_x = styles.get('overflow-x', 'visible')
        if overflow_x in ['scroll', 'auto']:
            issues.append("Horizontal scrolling may be problematic for some users")
        
        return issues
    
    def _identify_interaction_issues(self, styles: Dict[str, Any]) -> List[str]:
        """Identify interaction-related accessibility issues"""
        issues = []
        
        # Check for disabled pointer events on interactive elements
        if styles.get('pointer-events') == 'none':
            if styles.get('_accessibility', {}).get('isInteractive'):
                issues.append("Interactive element has pointer-events: none")
        
        # Check for missing focus indicators
        focus_props = ['outline', 'box-shadow', 'border']
        has_focus_indicator = any(
            styles.get(prop, 'none').lower() not in ['none', 'initial', '0px', 'transparent']
            for prop in focus_props
        )
        
        if not has_focus_indicator and styles.get('_accessibility', {}).get('isInteractive'):
            issues.append("Interactive element lacks visible focus indicator")
        
        return issues
    
    def _identify_motion_issues(self, styles: Dict[str, Any]) -> List[str]:
        """Identify motion and animation accessibility issues"""
        issues = []
        
        # Check for long animations
        duration = styles.get('animation-duration', '0s')
        if duration != '0s' and 'infinite' in styles.get('animation-iteration-count', '1'):
            issues.append("Infinite animation may be problematic for users with vestibular disorders")
        
        # Check for auto-playing animations
        if styles.get('animation-play-state') == 'running' and duration != '0s':
            issues.append("Auto-playing animation should respect prefers-reduced-motion")
        
        return issues
    
    def _identify_visibility_issues(self, styles: Dict[str, Any], accessibility_info: Dict[str, Any]) -> List[str]:
        """Identify visibility-related accessibility issues"""
        issues = []
        
        # Check for invisible interactive elements
        if not accessibility_info.get('isVisible', True) and accessibility_info.get('isInteractive', False):
            issues.append("Interactive element is not visible")
        
        # Check for very small elements
        rect = accessibility_info.get('boundingRect', {})
        if rect.get('width', 0) < 44 or rect.get('height', 0) < 44:
            if accessibility_info.get('isInteractive', False):
                issues.append("Interactive element smaller than minimum touch target (44px)")
        
        return issues
    
    # Helper methods
    def _convert_to_pixels(self, css_value: str) -> float:
        """Convert CSS value to pixels"""
        try:
            if css_value.endswith('px'):
                return float(css_value[:-2])
            elif css_value.endswith('em'):
                return float(css_value[:-2]) * 16  # Approximate
            elif css_value.endswith('rem'):
                return float(css_value[:-3]) * 16  # Approximate
            elif css_value.endswith('%'):
                return float(css_value[:-1]) * 0.16  # Approximate for font-size
            else:
                return 16.0  # Default
        except (ValueError, AttributeError):
            return 16.0
    
    def _calculate_line_height_ratio(self, font_size: str, line_height: str) -> float:
        """Calculate line height ratio"""
        try:
            if line_height == 'normal':
                return 1.2
            
            font_px = self._convert_to_pixels(font_size)
            
            if line_height.endswith('px'):
                line_px = float(line_height[:-2])
                return line_px / font_px
            elif line_height.replace('.', '').isdigit():
                return float(line_height)
            
            return 1.2
        except (ValueError, AttributeError):
            return 1.2
    
    def _calculate_readability_score(self, styles: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate a basic readability score based on CSS properties"""
        score = 100
        issues = []
        
        # Font size
        font_size_px = self._convert_to_pixels(styles.get('font-size', '16px'))
        if font_size_px < 14:
            score -= 20
            issues.append("Font size too small")
        
        # Line height
        line_height_ratio = self._calculate_line_height_ratio(
            styles.get('font-size', '16px'),
            styles.get('line-height', 'normal')
        )
        if line_height_ratio < 1.2:
            score -= 15
            issues.append("Line height too tight")
        
        # Letter spacing
        letter_spacing = styles.get('letter-spacing', 'normal')
        if letter_spacing != 'normal' and letter_spacing.startswith('-'):
            score -= 10
            issues.append("Negative letter spacing reduces readability")
        
        return {
            'score': max(0, score),
            'issues': issues
        }
    
    def _extract_flex_properties(self, styles: Dict[str, Any]) -> Dict[str, str]:
        """Extract flexbox-related properties"""
        return {
            'display': styles.get('display', ''),
            'flex_direction': styles.get('flex-direction', 'row'),
            'flex_wrap': styles.get('flex-wrap', 'nowrap'),
            'justify_content': styles.get('justify-content', 'flex-start'),
            'align_items': styles.get('align-items', 'stretch'),
            'align_content': styles.get('align-content', 'stretch'),
            'flex': styles.get('flex', '0 1 auto'),
            'flex_grow': styles.get('flex-grow', '0'),
            'flex_shrink': styles.get('flex-shrink', '1'),
            'flex_basis': styles.get('flex-basis', 'auto')
        }
    
    def _extract_grid_properties(self, styles: Dict[str, Any]) -> Dict[str, str]:
        """Extract CSS Grid-related properties"""
        return {
            'display': styles.get('display', ''),
            'grid_template_columns': styles.get('grid-template-columns', 'none'),
            'grid_template_rows': styles.get('grid-template-rows', 'none'),
            'grid_template_areas': styles.get('grid-template-areas', 'none'),
            'grid_column': styles.get('grid-column', 'auto'),
            'grid_row': styles.get('grid-row', 'auto'),
            'grid_area': styles.get('grid-area', 'auto'),
            'gap': styles.get('gap', 'normal'),
            'grid_gap': styles.get('grid-gap', 'normal')
        }
    
    def _compare_analyses(self, before: Dict[str, Any], after: Dict[str, Any], modifications: Dict[str, str]) -> Dict[str, Any]:
        """Compare before and after analyses"""
        comparison = {
            'color_changes': {},
            'typography_changes': {},
            'layout_changes': {},
            'interaction_changes': {},
            'motion_changes': {},
            'visibility_changes': {}
        }
        
        # Compare each category
        for category in ['color_analysis', 'typography_analysis', 'layout_analysis', 
                        'interaction_analysis', 'motion_analysis', 'visibility_analysis']:
            
            before_data = before.get(category, {})
            after_data = after.get(category, {})
            category_key = category.replace('_analysis', '_changes')
            
            for key, after_value in after_data.items():
                before_value = before_data.get(key)
                if before_value != after_value:
                    comparison[category_key][key] = {
                        'before': before_value,
                        'after': after_value,
                        'changed': True
                    }
        
        return comparison
    
    def _assess_accessibility_impact(self, comparison: Dict[str, Any]) -> Dict[str, Any]:
        """Assess the accessibility impact of the changes"""
        impact = {
            'positive_changes': [],
            'negative_changes': [],
            'neutral_changes': [],
            'overall_score': 0
        }
        
        # Analyze color changes
        color_changes = comparison.get('color_changes', {})
        # Add specific logic for assessing color impact
        
        # Analyze typography changes
        typography_changes = comparison.get('typography_changes', {})
        # Add specific logic for assessing typography impact
        
        # Continue for other categories...
        
        return impact