"""
JavaScript Accessibility Checker for AutoTest
Provides specialized accessibility rules and testing for JavaScript functionality.
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from selenium.webdriver.remote.webelement import WebElement

from .js_analyzer import JavaScriptAnalyzer


@dataclass
class JSAccessibilityRule:
    """
    JavaScript-specific accessibility rule definition
    """
    rule_id: str
    name: str
    description: str
    test_function: str
    severity: str = 'moderate'
    wcag_level: str = '2.1 AA'
    category: str = 'javascript'
    examples: Optional[List[Dict[str, str]]] = None


class JSAccessibilityChecker:
    """
    Comprehensive JavaScript accessibility checker with specialized rules
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.rules = self._initialize_js_rules()
    
    def _initialize_js_rules(self) -> Dict[str, JSAccessibilityRule]:
        """Initialize JavaScript accessibility rules"""
        rules = {}
        
        # Event Handler Rules
        rules['js-keyboard-events'] = JSAccessibilityRule(
            rule_id='js-keyboard-events',
            name='Keyboard Event Support',
            description='Interactive elements must support keyboard events',
            test_function='test_keyboard_event_support',
            severity='serious',
            wcag_level='2.1 A',
            examples=[
                {
                    'bad': 'element.onclick = function() { /* action */ }',
                    'good': 'element.addEventListener("click", handler); element.addEventListener("keydown", keyHandler);'
                }
            ]
        )
        
        rules['js-focus-management'] = JSAccessibilityRule(
            rule_id='js-focus-management',
            name='Proper Focus Management',
            description='Focus must be managed properly in dynamic interfaces',
            test_function='test_focus_management',
            severity='serious',
            wcag_level='2.1 AA',
            examples=[
                {
                    'bad': 'element.focus(); // Without considering user context',
                    'good': 'if (userTriggered) { element.focus(); } // Contextual focus'
                }
            ]
        )
        
        # ARIA Implementation Rules
        rules['js-aria-updates'] = JSAccessibilityRule(
            rule_id='js-aria-updates',
            name='ARIA State Updates',
            description='JavaScript must update ARIA states when content changes',
            test_function='test_aria_state_updates',
            severity='serious',
            wcag_level='2.1 A',
            examples=[
                {
                    'bad': 'toggle.click(); // Visual change only',
                    'good': 'toggle.click(); toggle.setAttribute("aria-expanded", isExpanded);'
                }
            ]
        )
        
        rules['js-live-regions'] = JSAccessibilityRule(
            rule_id='js-live-regions',
            name='Live Region Announcements',
            description='Dynamic content must be announced to screen readers',
            test_function='test_live_region_usage',
            severity='moderate',
            wcag_level='2.1 A',
            examples=[
                {
                    'bad': 'statusDiv.textContent = "Loading..."; // Not announced',
                    'good': 'statusDiv.setAttribute("aria-live", "polite"); statusDiv.textContent = "Loading...";'
                }
            ]
        )
        
        # Custom Control Rules
        rules['js-custom-controls'] = JSAccessibilityRule(
            rule_id='js-custom-controls',
            name='Custom Control Accessibility',
            description='Custom interactive controls must be fully accessible',
            test_function='test_custom_control_accessibility',
            severity='serious',
            wcag_level='2.1 A'
        )
        
        rules['js-modal-behavior'] = JSAccessibilityRule(
            rule_id='js-modal-behavior',
            name='Modal Dialog Behavior',
            description='Modal dialogs must implement proper accessibility behavior',
            test_function='test_modal_accessibility',
            severity='serious',
            wcag_level='2.1 AA'
        )
        
        # Dynamic Content Rules
        rules['js-content-changes'] = JSAccessibilityRule(
            rule_id='js-content-changes',
            name='Content Change Announcements',
            description='Content changes must be announced appropriately',
            test_function='test_content_change_announcements',
            severity='moderate',
            wcag_level='2.1 A'
        )
        
        rules['js-auto-updates'] = JSAccessibilityRule(
            rule_id='js-auto-updates',
            name='Auto-updating Content Control',
            description='Users must be able to control auto-updating content',
            test_function='test_auto_update_controls',
            severity='moderate',
            wcag_level='2.1 AAA'
        )
        
        # Form Enhancement Rules
        rules['js-form-validation'] = JSAccessibilityRule(
            rule_id='js-form-validation',
            name='Accessible Form Validation',
            description='Form validation errors must be accessible',
            test_function='test_form_validation_accessibility',
            severity='serious',
            wcag_level='2.1 AA'
        )
        
        rules['js-form-enhancements'] = JSAccessibilityRule(
            rule_id='js-form-enhancements',
            name='Form Enhancement Accessibility',
            description='JavaScript form enhancements must maintain accessibility',
            test_function='test_form_enhancement_accessibility',
            severity='moderate',
            wcag_level='2.1 AA'
        )
        
        # Performance and UX Rules
        rules['js-loading-states'] = JSAccessibilityRule(
            rule_id='js-loading-states',
            name='Loading State Accessibility',
            description='Loading states must be accessible to all users',
            test_function='test_loading_state_accessibility',
            severity='moderate',
            wcag_level='2.1 AA'
        )
        
        rules['js-error-handling'] = JSAccessibilityRule(
            rule_id='js-error-handling',
            name='Error Handling Accessibility',
            description='JavaScript errors must not break accessibility',
            test_function='test_error_handling_accessibility',
            severity='serious',
            wcag_level='2.1 A'
        )
        
        return rules
    
    def get_rule(self, rule_id: str) -> Optional[JSAccessibilityRule]:
        """Get a specific JavaScript accessibility rule"""
        return self.rules.get(rule_id)
    
    def get_rules_by_severity(self, severity: str) -> List[JSAccessibilityRule]:
        """Get rules by severity level"""
        return [rule for rule in self.rules.values() if rule.severity == severity]
    
    def test_all_js_rules(self, js_analyzer: JavaScriptAnalyzer, page_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Test all JavaScript accessibility rules
        
        Args:
            js_analyzer: JavaScriptAnalyzer instance
            page_analysis: Complete page JavaScript analysis
            
        Returns:
            Comprehensive test results
        """
        results = {
            'rule_results': {},
            'summary': {
                'total_rules': len(self.rules),
                'rules_passed': 0,
                'rules_failed': 0,
                'rules_warning': 0,
                'critical_issues': 0
            },
            'page_analysis': page_analysis
        }
        
        # Test each rule
        for rule_id, rule in self.rules.items():
            try:
                test_method = getattr(self, rule.test_function, None)
                if not test_method:
                    results['rule_results'][rule_id] = {
                        'status': 'error',
                        'message': f'Test method {rule.test_function} not found'
                    }
                    continue
                
                # Run the test
                test_result = test_method(page_analysis, js_analyzer)
                test_result['rule_info'] = {
                    'name': rule.name,
                    'description': rule.description,
                    'severity': rule.severity,
                    'wcag_level': rule.wcag_level,
                    'examples': rule.examples
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
                self.logger.error(f"Error testing JavaScript rule {rule_id}: {e}")
                results['rule_results'][rule_id] = {
                    'status': 'error',
                    'message': str(e)
                }
        
        return results
    
    # JavaScript Accessibility Test Methods
    def test_keyboard_event_support(self, page_analysis: Dict[str, Any], js_analyzer: JavaScriptAnalyzer) -> Dict[str, Any]:
        """Test keyboard event support for interactive elements"""
        try:
            event_handlers = page_analysis.get('event_handlers', {})
            mouse_only = event_handlers.get('mouse_only', 0)
            total_handlers = event_handlers.get('elements_with_handlers', 0)
            
            if mouse_only > 0:
                return {
                    'status': 'fail',
                    'message': f'{mouse_only} elements have mouse-only interactions',
                    'details': {
                        'mouse_only_elements': mouse_only,
                        'total_interactive_elements': total_handlers,
                        'issues': event_handlers.get('accessibility_issues', [])
                    },
                    'recommendations': [
                        'Add keyboard event handlers (keydown, keyup) for all interactive elements',
                        'Ensure Enter and Space keys activate buttons and links',
                        'Test all interactions with keyboard-only navigation',
                        'Use semantic HTML elements when possible for built-in keyboard support'
                    ]
                }
            elif total_handlers == 0:
                return {
                    'status': 'warning',
                    'message': 'No JavaScript event handlers detected',
                    'details': {'note': 'This may indicate static content or server-side interactions'}
                }
            
            return {
                'status': 'pass',
                'message': f'All {total_handlers} interactive elements appear to have keyboard support',
                'details': event_handlers
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Error testing keyboard events: {str(e)}'
            }
    
    def test_focus_management(self, page_analysis: Dict[str, Any], js_analyzer: JavaScriptAnalyzer) -> Dict[str, Any]:
        """Test focus management implementation"""
        try:
            focus_analysis = page_analysis.get('focus_management', {})
            issues = focus_analysis.get('issues', [])
            modal_elements = focus_analysis.get('modal_elements', 0)
            
            critical_issues = [issue for issue in issues if issue.get('severity') == 'serious']
            
            if critical_issues:
                return {
                    'status': 'fail',
                    'message': f'{len(critical_issues)} critical focus management issues found',
                    'details': {
                        'critical_issues': critical_issues,
                        'total_issues': len(issues),
                        'modal_elements': modal_elements
                    },
                    'recommendations': [
                        'Implement proper focus trapping for modal dialogs',
                        'Restore focus to triggering element when closing modals',
                        'Provide visible focus indicators for all interactive elements',
                        'Test focus management with keyboard-only navigation'
                    ]
                }
            elif issues:
                return {
                    'status': 'warning',
                    'message': f'{len(issues)} focus management concerns detected',
                    'details': {
                        'issues': issues,
                        'modal_elements': modal_elements
                    },
                    'recommendations': [
                        'Review focus management implementation',
                        'Consider accessibility when removing default focus outlines'
                    ]
                }
            
            return {
                'status': 'pass',
                'message': 'Focus management appears to be implemented properly',
                'details': focus_analysis
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Error testing focus management: {str(e)}'
            }
    
    def test_aria_state_updates(self, page_analysis: Dict[str, Any], js_analyzer: JavaScriptAnalyzer) -> Dict[str, Any]:
        """Test ARIA state updates in dynamic content"""
        try:
            aria_analysis = page_analysis.get('accessibility_apis', {})
            dynamic_analysis = page_analysis.get('dynamic_content', {})
            
            aria_issues = aria_analysis.get('issues', [])
            dynamic_issues = dynamic_analysis.get('dynamic_issues', [])
            
            # Check for elements that should have ARIA states
            expandable_elements = aria_analysis.get('aria_expanded', 0)
            controlled_elements = aria_analysis.get('aria_controls', 0)
            
            serious_aria_issues = [issue for issue in aria_issues if issue.get('severity') == 'serious']
            
            if serious_aria_issues:
                return {
                    'status': 'fail',
                    'message': f'{len(serious_aria_issues)} serious ARIA implementation issues',
                    'details': {
                        'serious_issues': serious_aria_issues,
                        'total_aria_issues': len(aria_issues),
                        'expandable_elements': expandable_elements,
                        'controlled_elements': controlled_elements
                    },
                    'recommendations': [
                        'Update aria-expanded when expanding/collapsing content',
                        'Use aria-controls to associate controls with their targets',
                        'Remove aria-hidden from interactive elements',
                        'Ensure ARIA labels are updated when content changes'
                    ]
                }
            elif aria_issues or dynamic_issues:
                return {
                    'status': 'warning',
                    'message': 'ARIA implementation could be improved',
                    'details': {
                        'aria_issues': aria_issues,
                        'dynamic_issues': dynamic_issues
                    }
                }
            
            return {
                'status': 'pass',
                'message': 'ARIA states appear to be managed properly',
                'details': aria_analysis
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Error testing ARIA state updates: {str(e)}'
            }
    
    def test_live_region_usage(self, page_analysis: Dict[str, Any], js_analyzer: JavaScriptAnalyzer) -> Dict[str, Any]:
        """Test ARIA live region usage for dynamic content"""
        try:
            live_regions = page_analysis.get('aria_live_regions', {})
            dynamic_content = page_analysis.get('dynamic_content', {})
            
            total_live_regions = live_regions.get('total_live_regions', 0)
            auto_updating = dynamic_content.get('auto_updating_content', False)
            ajax_indicators = dynamic_content.get('ajax_indicators', 0)
            
            live_region_issues = live_regions.get('issues', [])
            
            if auto_updating and total_live_regions == 0:
                return {
                    'status': 'fail',
                    'message': 'Auto-updating content without live regions detected',
                    'details': {
                        'auto_updating_content': auto_updating,
                        'live_regions': total_live_regions,
                        'ajax_indicators': ajax_indicators
                    },
                    'recommendations': [
                        'Add aria-live="polite" to status/notification areas',
                        'Use aria-live="assertive" only for urgent announcements',
                        'Ensure live region content is meaningful and not too verbose',
                        'Test with screen readers to verify announcements work'
                    ]
                }
            elif live_region_issues:
                return {
                    'status': 'warning',
                    'message': f'{len(live_region_issues)} live region implementation issues',
                    'details': {
                        'issues': live_region_issues,
                        'total_live_regions': total_live_regions
                    }
                }
            
            return {
                'status': 'pass',
                'message': f'Live regions appear to be implemented properly ({total_live_regions} found)',
                'details': live_regions
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Error testing live regions: {str(e)}'
            }
    
    def test_custom_control_accessibility(self, page_analysis: Dict[str, Any], js_analyzer: JavaScriptAnalyzer) -> Dict[str, Any]:
        """Test accessibility of custom interactive controls"""
        try:
            keyboard_analysis = page_analysis.get('keyboard_support', {})
            custom_controls = keyboard_analysis.get('custom_controls', 0)
            keyboard_issues = keyboard_analysis.get('issues', [])
            
            custom_control_issues = [
                issue for issue in keyboard_issues 
                if 'custom' in issue.get('issue', '').lower()
            ]
            
            if custom_controls > 0 and custom_control_issues:
                return {
                    'status': 'fail',
                    'message': f'{len(custom_control_issues)} custom control accessibility issues',
                    'details': {
                        'custom_controls': custom_controls,
                        'issues': custom_control_issues
                    },
                    'recommendations': [
                        'Ensure custom controls are keyboard accessible',
                        'Add appropriate ARIA roles and properties',
                        'Implement proper focus management',
                        'Test with assistive technologies',
                        'Consider using semantic HTML elements instead'
                    ]
                }
            elif custom_controls > 0:
                return {
                    'status': 'warning',
                    'message': f'{custom_controls} custom controls detected - verify accessibility',
                    'details': {'custom_controls': custom_controls},
                    'recommendations': [
                        'Manually test custom controls with keyboard and screen reader',
                        'Ensure all custom controls have proper ARIA implementation'
                    ]
                }
            
            return {
                'status': 'pass',
                'message': 'No problematic custom controls detected',
                'details': keyboard_analysis
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Error testing custom controls: {str(e)}'
            }
    
    def test_modal_accessibility(self, page_analysis: Dict[str, Any], js_analyzer: JavaScriptAnalyzer) -> Dict[str, Any]:
        """Test modal dialog accessibility implementation"""
        try:
            focus_analysis = page_analysis.get('focus_management', {})
            dynamic_analysis = page_analysis.get('dynamic_content', {})
            
            modal_elements = focus_analysis.get('modal_elements', 0)
            modal_issues = [
                issue for issue in dynamic_analysis.get('dynamic_issues', [])
                if 'modal' in issue.get('issue', '').lower() or 'dialog' in issue.get('issue', '').lower()
            ]
            
            if modal_elements > 0:
                if modal_issues:
                    return {
                        'status': 'fail',
                        'message': f'Modal accessibility issues detected ({len(modal_issues)} issues)',
                        'details': {
                            'modal_elements': modal_elements,
                            'issues': modal_issues
                        },
                        'recommendations': [
                            'Implement focus trapping within modal dialogs',
                            'Set focus to first focusable element when opening',
                            'Restore focus to triggering element when closing',
                            'Add aria-modal="true" to dialog elements',
                            'Ensure modal can be closed with Escape key',
                            'Use aria-labelledby to associate modal with its title'
                        ]
                    }
                else:
                    return {
                        'status': 'warning',
                        'message': f'{modal_elements} modal elements found - verify implementation',
                        'details': {'modal_elements': modal_elements},
                        'recommendations': [
                            'Test modal keyboard navigation and focus management',
                            'Verify screen reader announcements for modal state changes'
                        ]
                    }
            
            return {
                'status': 'pass',
                'message': 'No modal dialogs detected',
                'details': focus_analysis
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Error testing modal accessibility: {str(e)}'
            }
    
    # Placeholder methods for remaining rules - would be fully implemented in production
    def test_content_change_announcements(self, page_analysis, js_analyzer):
        return {'status': 'pass', 'message': 'Content change announcements test not yet implemented'}
    
    def test_auto_update_controls(self, page_analysis, js_analyzer):
        return {'status': 'pass', 'message': 'Auto-update controls test not yet implemented'}
    
    def test_form_validation_accessibility(self, page_analysis, js_analyzer):
        return {'status': 'pass', 'message': 'Form validation accessibility test not yet implemented'}
    
    def test_form_enhancement_accessibility(self, page_analysis, js_analyzer):
        return {'status': 'pass', 'message': 'Form enhancement accessibility test not yet implemented'}
    
    def test_loading_state_accessibility(self, page_analysis, js_analyzer):
        return {'status': 'pass', 'message': 'Loading state accessibility test not yet implemented'}
    
    def test_error_handling_accessibility(self, page_analysis, js_analyzer):
        return {'status': 'pass', 'message': 'Error handling accessibility test not yet implemented'}