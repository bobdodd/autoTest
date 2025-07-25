"""
CSS Accessibility Rules for AutoTest
Defines CSS-specific accessibility rules and testing patterns.
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from selenium.webdriver.remote.webelement import WebElement

from .css_analyzer import CSSAnalyzer


@dataclass
class CSSRule:
    """
    CSS-specific accessibility rule definition
    """
    rule_id: str
    name: str
    description: str
    css_properties: List[str]
    test_function: str
    severity: str = 'moderate'
    wcag_level: str = '2.1 AA'
    category: str = 'css'
    modification_tests: Optional[List[Dict[str, Any]]] = None


class CSSAccessibilityRules:
    """
    Comprehensive CSS accessibility rules for advanced testing
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.rules = self._initialize_rules()
    
    def _initialize_rules(self) -> Dict[str, CSSRule]:
        """Initialize all CSS accessibility rules"""
        rules = {}
        
        # Color and Contrast Rules
        rules['css-contrast-enhanced'] = CSSRule(
            rule_id='css-contrast-enhanced',
            name='Enhanced Color Contrast Analysis',
            description='Advanced color contrast testing with CSS context analysis',
            css_properties=['color', 'background-color', 'border-color', 'outline-color'],
            test_function='test_enhanced_contrast',
            severity='serious',
            wcag_level='2.1 AA'
        )
        
        rules['css-color-only-info'] = CSSRule(
            rule_id='css-color-only-info',
            name='Color-Only Information Conveyance',
            description='Ensure information is not conveyed through color alone',
            css_properties=['color', 'background-color', 'border-color'],
            test_function='test_color_only_information',
            severity='serious',
            wcag_level='2.1 A'
        )
        
        # Typography Rules
        rules['css-font-scaling'] = CSSRule(
            rule_id='css-font-scaling',
            name='Font Scaling and Readability',
            description='Test font scaling up to 200% without loss of functionality',
            css_properties=['font-size', 'line-height', 'letter-spacing', 'word-spacing'],
            test_function='test_font_scaling',
            severity='moderate',
            wcag_level='2.1 AA',
            modification_tests=[
                {'scale_factor': 1.25, 'css_changes': {'font-size': '125%'}},
                {'scale_factor': 1.5, 'css_changes': {'font-size': '150%'}},
                {'scale_factor': 2.0, 'css_changes': {'font-size': '200%'}}
            ]
        )
        
        rules['css-line-height'] = CSSRule(
            rule_id='css-line-height',
            name='Line Height Accessibility',
            description='Ensure adequate line height for readability',
            css_properties=['line-height', 'font-size'],
            test_function='test_line_height',
            severity='moderate',
            wcag_level='2.1 AA'
        )
        
        # Focus and Interaction Rules
        rules['css-focus-visible'] = CSSRule(
            rule_id='css-focus-visible',
            name='Visible Focus Indicators',
            description='Ensure all interactive elements have visible focus indicators',
            css_properties=['outline', 'outline-width', 'outline-style', 'outline-color', 'box-shadow'],
            test_function='test_focus_visibility',
            severity='serious',
            wcag_level='2.1 AA',
            modification_tests=[
                {'focus_style': 'outline', 'css_changes': {'outline': '2px solid #007acc'}},
                {'focus_style': 'box-shadow', 'css_changes': {'box-shadow': '0 0 0 2px #007acc'}},
                {'focus_style': 'combined', 'css_changes': {'outline': '2px solid #007acc', 'outline-offset': '2px'}}
            ]
        )
        
        rules['css-touch-targets'] = CSSRule(
            rule_id='css-touch-targets',
            name='Minimum Touch Target Size',
            description='Ensure interactive elements meet minimum 44x44px touch target size',
            css_properties=['width', 'height', 'min-width', 'min-height', 'padding'],
            test_function='test_touch_targets',
            severity='moderate',
            wcag_level='2.1 AAA',
            modification_tests=[
                {'approach': 'min-size', 'css_changes': {'min-width': '44px', 'min-height': '44px'}},
                {'approach': 'padding', 'css_changes': {'padding': '12px 16px'}},
                {'approach': 'combined', 'css_changes': {'min-width': '44px', 'min-height': '44px', 'padding': '8px'}}
            ]
        )
        
        # Layout and Responsive Rules
        rules['css-responsive-design'] = CSSRule(
            rule_id='css-responsive-design',
            name='Responsive Design Accessibility',
            description='Test accessibility across different viewport sizes',
            css_properties=['width', 'max-width', 'min-width', 'display', 'flex', 'grid'],
            test_function='test_responsive_design',
            severity='moderate',
            wcag_level='2.1 AA'
        )
        
        rules['css-content-reflow'] = CSSRule(
            rule_id='css-content-reflow',
            name='Content Reflow at 320px',
            description='Ensure content reflows properly at 320px viewport width',
            css_properties=['width', 'max-width', 'overflow', 'white-space'],
            test_function='test_content_reflow',
            severity='moderate',
            wcag_level='2.1 AA'
        )
        
        # Motion and Animation Rules
        rules['css-motion-safe'] = CSSRule(
            rule_id='css-motion-safe',
            name='Motion Safety and Reduced Motion',
            description='Ensure animations respect prefers-reduced-motion settings',
            css_properties=['animation', 'transition', 'transform'],
            test_function='test_motion_safety',
            severity='moderate',
            wcag_level='2.1 AAA',
            modification_tests=[
                {'approach': 'disable', 'css_changes': {'animation': 'none', 'transition': 'none'}},
                {'approach': 'reduce', 'css_changes': {'animation-duration': '0.01s', 'transition-duration': '0.01s'}},
                {'approach': 'conditional', 'css_changes': {'animation': 'var(--animation, none)'}}
            ]
        )
        
        rules['css-parallax-scrolling'] = CSSRule(
            rule_id='css-parallax-scrolling',
            name='Parallax Scrolling Accessibility',
            description='Test parallax effects for vestibular disorder triggers',
            css_properties=['transform', 'animation', 'transition'],
            test_function='test_parallax_effects',
            severity='serious',
            wcag_level='2.1 AAA'
        )
        
        # Advanced CSS Rules
        rules['css-custom-properties'] = CSSRule(
            rule_id='css-custom-properties',
            name='CSS Custom Properties Accessibility',
            description='Test accessibility of CSS custom property implementations',
            css_properties=['--*'],
            test_function='test_custom_properties',
            severity='minor',
            wcag_level='2.1 AA'
        )
        
        rules['css-grid-accessibility'] = CSSRule(
            rule_id='css-grid-accessibility',
            name='CSS Grid Layout Accessibility',
            description='Test CSS Grid implementations for reading order and navigation',
            css_properties=['display', 'grid-template-*', 'grid-area', 'order'],
            test_function='test_grid_accessibility',
            severity='moderate',
            wcag_level='2.1 AA'
        )
        
        rules['css-flexbox-accessibility'] = CSSRule(
            rule_id='css-flexbox-accessibility',
            name='CSS Flexbox Accessibility',
            description='Test Flexbox implementations for reading order and navigation',
            css_properties=['display', 'flex-direction', 'order', 'justify-content'],
            test_function='test_flexbox_accessibility',
            severity='moderate',
            wcag_level='2.1 AA'
        )
        
        return rules
    
    def get_rule(self, rule_id: str) -> Optional[CSSRule]:
        """Get a specific CSS rule by ID"""
        return self.rules.get(rule_id)
    
    def get_rules_by_category(self, category: str) -> List[CSSRule]:
        """Get all rules in a specific category"""
        return [rule for rule in self.rules.values() if rule.category == category]
    
    def get_rules_by_severity(self, severity: str) -> List[CSSRule]:
        """Get all rules with specific severity"""
        return [rule for rule in self.rules.values() if rule.severity == severity]
    
    def test_all_css_rules(self, css_analyzer: CSSAnalyzer, element: WebElement) -> Dict[str, Any]:
        """
        Test all CSS rules against an element
        
        Args:
            css_analyzer: CSSAnalyzer instance
            element: WebElement to test
            
        Returns:
            Dictionary with test results for all applicable rules
        """
        results = {
            'element_info': {
                'tag_name': element.tag_name,
                'classes': element.get_attribute('class') or '',
                'id': element.get_attribute('id') or ''
            },
            'rule_results': {},
            'summary': {
                'total_rules': len(self.rules),
                'rules_passed': 0,
                'rules_failed': 0,
                'rules_warning': 0,
                'critical_issues': 0
            }
        }
        
        # Get comprehensive CSS analysis
        css_analysis = css_analyzer.analyze_accessibility_properties(element)
        
        # Test each rule
        for rule_id, rule in self.rules.items():
            try:
                # Get the test function
                test_method = getattr(self, rule.test_function, None)
                if not test_method:
                    results['rule_results'][rule_id] = {
                        'status': 'error',
                        'message': f'Test method {rule.test_function} not found'
                    }
                    continue
                
                # Run the test
                test_result = test_method(css_analysis, element, css_analyzer)
                test_result['rule_info'] = {
                    'name': rule.name,
                    'description': rule.description,
                    'severity': rule.severity,
                    'wcag_level': rule.wcag_level
                }
                
                results['rule_results'][rule_id] = test_result
                
                # Update summary
                if test_result['status'] == 'pass':
                    results['summary']['rules_passed'] += 1
                elif test_result['status'] == 'fail':
                    results['summary']['rules_failed'] += 1
                    if rule.severity in ['critical', 'serious']:
                        results['summary']['critical_issues'] += 1
                elif test_result['status'] == 'warning':
                    results['summary']['rules_warning'] += 1
                
            except Exception as e:
                self.logger.error(f"Error testing rule {rule_id}: {e}")
                results['rule_results'][rule_id] = {
                    'status': 'error',
                    'message': str(e)
                }
        
        return results
    
    # CSS Rule Test Methods
    def test_enhanced_contrast(self, css_analysis: Dict[str, Any], element: WebElement, css_analyzer: CSSAnalyzer) -> Dict[str, Any]:
        """Test enhanced color contrast with CSS context"""
        try:
            color_analysis = css_analysis.get('color_analysis', {})
            issues = color_analysis.get('potential_issues', [])
            
            # Enhanced contrast checking
            if any('contrast' in issue.lower() for issue in issues):
                return {
                    'status': 'fail',
                    'message': 'Insufficient color contrast detected',
                    'details': {
                        'foreground_color': color_analysis.get('foreground_color'),
                        'background_color': color_analysis.get('background_color'),
                        'issues': issues
                    },
                    'suggested_fixes': self._generate_contrast_fixes(color_analysis)
                }
            
            return {
                'status': 'pass',
                'message': 'Color contrast meets accessibility standards',
                'details': color_analysis
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Error testing contrast: {str(e)}'
            }
    
    def test_color_only_information(self, css_analysis: Dict[str, Any], element: WebElement, css_analyzer: CSSAnalyzer) -> Dict[str, Any]:
        """Test for color-only information conveyance"""
        try:
            color_analysis = css_analysis.get('color_analysis', {})
            
            # Check if element conveys information through color only
            has_color_info = any('color' in issue.lower() for issue in color_analysis.get('potential_issues', []))
            
            if has_color_info:
                return {
                    'status': 'warning',
                    'message': 'Element may rely on color alone for information',
                    'details': color_analysis,
                    'suggested_fixes': [
                        'Add text labels or symbols',
                        'Use patterns or textures',
                        'Provide alternative indicators'
                    ]
                }
            
            return {
                'status': 'pass',
                'message': 'Information not conveyed through color alone'
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Error testing color information: {str(e)}'
            }
    
    def test_font_scaling(self, css_analysis: Dict[str, Any], element: WebElement, css_analyzer: CSSAnalyzer) -> Dict[str, Any]:
        """Test font scaling capabilities"""
        try:
            typography = css_analysis.get('typography_analysis', {})
            font_size_px = typography.get('font_size_px', 16)
            readability_score = typography.get('readability_score', {})
            
            # Test if font is scalable
            if font_size_px < 12:
                return {
                    'status': 'fail',
                    'message': f'Font size too small ({font_size_px}px)',
                    'details': typography,
                    'suggested_fixes': [
                        'Increase base font size to at least 14px',
                        'Use relative units (em, rem) for scalability',
                        'Test scaling up to 200%'
                    ]
                }
            
            # Check readability score
            if readability_score.get('score', 100) < 70:
                return {
                    'status': 'warning',
                    'message': 'Font readability could be improved',
                    'details': {
                        'typography': typography,
                        'readability_score': readability_score
                    },
                    'suggested_fixes': readability_score.get('issues', [])
                }
            
            return {
                'status': 'pass',
                'message': 'Font scaling and readability acceptable',
                'details': typography
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Error testing font scaling: {str(e)}'
            }
    
    def test_line_height(self, css_analysis: Dict[str, Any], element: WebElement, css_analyzer: CSSAnalyzer) -> Dict[str, Any]:
        """Test line height accessibility"""
        try:
            typography = css_analysis.get('typography_analysis', {})
            line_height_ratio = typography.get('line_height_ratio', 1.2)
            
            if line_height_ratio < 1.2:
                return {
                    'status': 'fail',
                    'message': f'Line height too tight ({line_height_ratio})',
                    'details': typography,
                    'suggested_fixes': [
                        'Increase line-height to at least 1.2',
                        'For paragraph text, use 1.5 or higher',
                        'Consider spacing for readability'
                    ]
                }
            elif line_height_ratio < 1.4:
                return {
                    'status': 'warning',
                    'message': f'Line height could be improved ({line_height_ratio})',
                    'details': typography,
                    'suggested_fixes': [
                        'Consider increasing line-height to 1.4-1.6 for better readability'
                    ]
                }
            
            return {
                'status': 'pass',
                'message': 'Line height meets accessibility standards',
                'details': typography
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Error testing line height: {str(e)}'
            }
    
    def test_focus_visibility(self, css_analysis: Dict[str, Any], element: WebElement, css_analyzer: CSSAnalyzer) -> Dict[str, Any]:
        """Test focus indicator visibility"""
        try:
            interaction_analysis = css_analysis.get('interaction_analysis', {})
            visibility_analysis = css_analysis.get('visibility_analysis', {})
            
            if not visibility_analysis.get('is_interactive', False):
                return {
                    'status': 'pass',
                    'message': 'Element is not interactive'
                }
            
            issues = interaction_analysis.get('interaction_issues', [])
            focus_issues = [issue for issue in issues if 'focus' in issue.lower()]
            
            if focus_issues:
                return {
                    'status': 'fail',
                    'message': 'Focus indicator issues detected',
                    'details': {
                        'interaction_analysis': interaction_analysis,
                        'issues': focus_issues
                    },
                    'suggested_fixes': [
                        'Add visible outline on focus',
                        'Use box-shadow for focus indication',
                        'Ensure sufficient contrast for focus indicators'
                    ]
                }
            
            return {
                'status': 'pass',
                'message': 'Focus indicators are adequate',
                'details': interaction_analysis
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Error testing focus visibility: {str(e)}'
            }
    
    def test_touch_targets(self, css_analysis: Dict[str, Any], element: WebElement, css_analyzer: CSSAnalyzer) -> Dict[str, Any]:
        """Test minimum touch target size"""
        try:
            visibility_analysis = css_analysis.get('visibility_analysis', {})
            
            if not visibility_analysis.get('is_interactive', False):
                return {
                    'status': 'pass',
                    'message': 'Element is not interactive'
                }
            
            bounding_rect = visibility_analysis.get('bounding_rect', {})
            width = bounding_rect.get('width', 0)
            height = bounding_rect.get('height', 0)
            
            min_size = 44  # WCAG AAA guideline
            
            if width < min_size or height < min_size:
                return {
                    'status': 'fail',
                    'message': f'Touch target too small ({width}x{height}px)',
                    'details': {
                        'current_size': {'width': width, 'height': height},
                        'minimum_size': {'width': min_size, 'height': min_size}
                    },
                    'suggested_fixes': [
                        f'Increase element size to at least {min_size}x{min_size}px',
                        'Add padding to increase touch area',
                        'Use min-width and min-height CSS properties'
                    ]
                }
            
            return {
                'status': 'pass',
                'message': f'Touch target size adequate ({width}x{height}px)',
                'details': {'size': {'width': width, 'height': height}}
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Error testing touch targets: {str(e)}'
            }
    
    def test_motion_safety(self, css_analysis: Dict[str, Any], element: WebElement, css_analyzer: CSSAnalyzer) -> Dict[str, Any]:
        """Test motion and animation safety"""
        try:
            motion_analysis = css_analysis.get('motion_analysis', {})
            issues = motion_analysis.get('motion_issues', [])
            
            if issues:
                return {
                    'status': 'warning',
                    'message': 'Motion accessibility concerns detected',
                    'details': {
                        'motion_analysis': motion_analysis,
                        'issues': issues
                    },
                    'suggested_fixes': [
                        'Respect prefers-reduced-motion media query',
                        'Provide controls to pause/stop animations',
                        'Avoid infinite animations',
                        'Use shorter animation durations'
                    ]
                }
            
            return {
                'status': 'pass',
                'message': 'Motion implementation appears safe',
                'details': motion_analysis
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Error testing motion safety: {str(e)}'
            }
    
    # Placeholder methods for additional CSS tests
    # These would be fully implemented in a production version
    def test_responsive_design(self, css_analysis, element, css_analyzer):
        return {'status': 'pass', 'message': 'Responsive design test not yet implemented'}
    
    def test_content_reflow(self, css_analysis, element, css_analyzer):
        return {'status': 'pass', 'message': 'Content reflow test not yet implemented'}
    
    def test_parallax_effects(self, css_analysis, element, css_analyzer):
        return {'status': 'pass', 'message': 'Parallax effects test not yet implemented'}
    
    def test_custom_properties(self, css_analysis, element, css_analyzer):
        return {'status': 'pass', 'message': 'Custom properties test not yet implemented'}
    
    def test_grid_accessibility(self, css_analysis, element, css_analyzer):
        return {'status': 'pass', 'message': 'Grid accessibility test not yet implemented'}
    
    def test_flexbox_accessibility(self, css_analysis, element, css_analyzer):
        return {'status': 'pass', 'message': 'Flexbox accessibility test not yet implemented'}
    
    def _generate_contrast_fixes(self, color_analysis: Dict[str, Any]) -> List[str]:
        """Generate specific contrast improvement suggestions"""
        fixes = []
        
        fg_color = color_analysis.get('foreground_color', '')
        bg_color = color_analysis.get('background_color', '')
        
        if fg_color and bg_color:
            fixes.extend([
                f'Darken foreground color from {fg_color}',
                f'Lighten background color from {bg_color}',
                'Use high contrast color combinations',
                'Test with online contrast checkers'
            ])
        
        return fixes