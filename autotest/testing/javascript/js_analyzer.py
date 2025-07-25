"""
JavaScript Analyzer for AutoTest
Provides comprehensive JavaScript analysis for accessibility testing.
"""

import json
import logging
from typing import Dict, List, Any, Optional
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import WebDriverException, JavascriptException


class JavaScriptAnalyzer:
    """
    Comprehensive JavaScript analysis for accessibility testing.
    Analyzes JavaScript code, event handlers, and dynamic behavior.
    """
    
    def __init__(self, driver):
        """
        Initialize JavaScript analyzer with WebDriver instance
        
        Args:
            driver: Selenium WebDriver instance
        """
        self.driver = driver
        self.logger = logging.getLogger(__name__)
    
    def analyze_page_javascript(self) -> Dict[str, Any]:
        """
        Analyze all JavaScript on the current page
        
        Returns:
            Comprehensive JavaScript analysis results
        """
        try:
            analysis = {
                'scripts': self._analyze_scripts(),
                'event_handlers': self._analyze_event_handlers(),
                'dynamic_content': self._analyze_dynamic_content(),
                'accessibility_apis': self._analyze_accessibility_apis(),
                'keyboard_support': self._analyze_keyboard_support(),
                'aria_live_regions': self._analyze_aria_live_regions(),
                'focus_management': self._analyze_focus_management(),
                'error_handling': self._analyze_error_handling(),
                'performance_impact': self._analyze_performance_impact()
            }
            
            # Generate overall accessibility score
            analysis['accessibility_score'] = self._calculate_accessibility_score(analysis)
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing page JavaScript: {e}")
            return {'error': str(e)}
    
    def _analyze_scripts(self) -> Dict[str, Any]:
        """Analyze all script tags and JavaScript sources"""
        try:
            script = """
            var scripts = [];
            var scriptTags = document.querySelectorAll('script');
            
            for (var i = 0; i < scriptTags.length; i++) {
                var script = scriptTags[i];
                var scriptInfo = {
                    src: script.src || null,
                    type: script.type || 'text/javascript',
                    async: script.async,
                    defer: script.defer,
                    integrity: script.integrity || null,
                    crossorigin: script.crossOrigin || null,
                    hasInlineCode: !script.src && script.textContent.length > 0,
                    codeLength: script.textContent.length,
                    accessibility_concerns: []
                };
                
                // Check for accessibility concerns in inline scripts
                if (scriptInfo.hasInlineCode) {
                    var code = script.textContent.toLowerCase();
                    
                    // Check for problematic patterns
                    if (code.includes('onclick') || code.includes('onmouseover')) {
                        scriptInfo.accessibility_concerns.push('Uses inline event handlers - may not be keyboard accessible');
                    }
                    
                    if (code.includes('alert(') && !code.includes('aria')) {
                        scriptInfo.accessibility_concerns.push('Alert dialogs may not be announced to screen readers');
                    }
                    
                    if (code.includes('settimeout') || code.includes('setinterval')) {
                        scriptInfo.accessibility_concerns.push('Automatic content changes may not respect user preferences');
                    }
                    
                    if (code.includes('focus()') && !code.includes('blur()')) {
                        scriptInfo.accessibility_concerns.push('Focus management may trap users');
                    }
                }
                
                scripts.push(scriptInfo);
            }
            
            return {
                total_scripts: scripts.length,
                external_scripts: scripts.filter(s => s.src).length,
                inline_scripts: scripts.filter(s => s.hasInlineCode).length,
                async_scripts: scripts.filter(s => s.async).length,
                defer_scripts: scripts.filter(s => s.defer).length,
                scripts_with_integrity: scripts.filter(s => s.integrity).length,
                scripts: scripts,
                total_concerns: scripts.reduce((sum, s) => sum + s.accessibility_concerns.length, 0)
            };
            """
            
            return self.driver.execute_script(script)
            
        except Exception as e:
            self.logger.error(f"Error analyzing scripts: {e}")
            return {'error': str(e)}
    
    def _analyze_event_handlers(self) -> Dict[str, Any]:
        """Analyze JavaScript event handlers for accessibility"""
        try:
            script = """
            var eventAnalysis = {
                elements_with_handlers: 0,
                keyboard_accessible: 0,
                mouse_only: 0,
                touch_accessible: 0,
                handler_types: {},
                accessibility_issues: []
            };
            
            // Get all elements
            var allElements = document.querySelectorAll('*');
            
            for (var i = 0; i < allElements.length; i++) {
                var element = allElements[i];
                var hasHandlers = false;
                var hasKeyboardHandler = false;
                var hasMouseHandler = false;
                var hasTouchHandler = false;
                
                // Check for event listeners (approximate detection)
                var eventAttributes = [
                    'onclick', 'onmousedown', 'onmouseup', 'onmouseover', 'onmouseout',
                    'onkeydown', 'onkeyup', 'onkeypress',
                    'ontouchstart', 'ontouchend', 'ontouchmove',
                    'onfocus', 'onblur', 'onchange', 'oninput'
                ];
                
                eventAttributes.forEach(function(attr) {
                    if (element.getAttribute(attr)) {
                        hasHandlers = true;
                        eventAnalysis.handler_types[attr] = (eventAnalysis.handler_types[attr] || 0) + 1;
                        
                        if (attr.startsWith('onkey')) hasKeyboardHandler = true;
                        if (attr.startsWith('onmouse')) hasMouseHandler = true;
                        if (attr.startsWith('ontouch')) hasTouchHandler = true;
                    }
                });
                
                // Check for common interactive patterns
                if (hasHandlers) {
                    eventAnalysis.elements_with_handlers++;
                    
                    if (hasKeyboardHandler) eventAnalysis.keyboard_accessible++;
                    if (hasMouseHandler && !hasKeyboardHandler) {
                        eventAnalysis.mouse_only++;
                        eventAnalysis.accessibility_issues.push({
                            element: element.tagName + (element.className ? '.' + element.className.split(' ')[0] : ''),
                            issue: 'Mouse-only interaction - not keyboard accessible',
                            suggestion: 'Add keyboard event handlers (onkeydown, onkeyup)'
                        });
                    }
                    if (hasTouchHandler) eventAnalysis.touch_accessible++;
                }
                
                // Check for interactive elements without proper handlers
                var interactiveTags = ['BUTTON', 'A', 'INPUT', 'SELECT', 'TEXTAREA'];
                var hasRole = element.getAttribute('role');
                var isInteractive = interactiveTags.includes(element.tagName) || 
                                  (hasRole && ['button', 'link', 'menuitem'].includes(hasRole));
                
                if (isInteractive && !hasHandlers && element.getAttribute('onclick')) {
                    eventAnalysis.accessibility_issues.push({
                        element: element.tagName + (element.id ? '#' + element.id : ''),
                        issue: 'Interactive element may not be fully accessible',
                        suggestion: 'Ensure keyboard and screen reader accessibility'
                    });
                }
            }
            
            return eventAnalysis;
            """
            
            return self.driver.execute_script(script)
            
        except Exception as e:
            self.logger.error(f"Error analyzing event handlers: {e}")
            return {'error': str(e)}
    
    def _analyze_dynamic_content(self) -> Dict[str, Any]:
        """Analyze dynamic content changes and their accessibility impact"""
        try:
            script = """
            var dynamicAnalysis = {
                mutation_observers: 0,
                timers: {
                    setTimeout_calls: 0,
                    setInterval_calls: 0
                },
                ajax_indicators: 0,
                dynamic_issues: [],
                auto_updating_content: false
            };
            
            // Check for MutationObserver usage (good practice)
            if (window.MutationObserver) {
                // This is a rough estimation - actual usage would need instrumentation
                dynamicAnalysis.mutation_observers = document.querySelectorAll('[data-observer]').length;
            }
            
            // Check for elements that commonly indicate dynamic content
            var loadingIndicators = document.querySelectorAll('[aria-busy="true"], .loading, .spinner, [role="progressbar"]');
            dynamicAnalysis.ajax_indicators = loadingIndicators.length;
            
            // Check for auto-updating content
            var autoUpdateElements = document.querySelectorAll('[data-refresh], [data-update], .auto-update');
            if (autoUpdateElements.length > 0) {
                dynamicAnalysis.auto_updating_content = true;
                dynamicAnalysis.dynamic_issues.push({
                    issue: 'Auto-updating content detected',
                    elements: autoUpdateElements.length,
                    suggestion: 'Ensure users can pause/control auto-updates and changes are announced'
                });
            }
            
            // Check for elements with aria-live regions
            var liveRegions = document.querySelectorAll('[aria-live]');
            dynamicAnalysis.aria_live_regions = liveRegions.length;
            
            // Check for common dynamic content patterns that may cause issues
            var modalElements = document.querySelectorAll('[role="dialog"], .modal, .popup');
            if (modalElements.length > 0) {
                dynamicAnalysis.dynamic_issues.push({
                    issue: 'Modal/dialog elements found',
                    elements: modalElements.length,
                    suggestion: 'Ensure proper focus management and keyboard trap implementation'
                });
            }
            
            return dynamicAnalysis;
            """
            
            return self.driver.execute_script(script)
            
        except Exception as e:
            self.logger.error(f"Error analyzing dynamic content: {e}")
            return {'error': str(e)}
    
    def _analyze_accessibility_apis(self) -> Dict[str, Any]:
        """Analyze usage of accessibility APIs and ARIA"""
        try:
            script = """
            var ariaAnalysis = {
                aria_labels: document.querySelectorAll('[aria-label]').length,
                aria_labelledby: document.querySelectorAll('[aria-labelledby]').length,
                aria_describedby: document.querySelectorAll('[aria-describedby]').length,
                aria_hidden: document.querySelectorAll('[aria-hidden]').length,
                aria_expanded: document.querySelectorAll('[aria-expanded]').length,
                aria_controls: document.querySelectorAll('[aria-controls]').length,
                aria_live: document.querySelectorAll('[aria-live]').length,
                roles: {},
                landmark_roles: 0,
                widget_roles: 0,
                issues: []
            };
            
            // Count different ARIA roles
            var elementsWithRoles = document.querySelectorAll('[role]');
            var landmarkRoles = ['banner', 'main', 'navigation', 'contentinfo', 'complementary', 'search'];
            var widgetRoles = ['button', 'checkbox', 'radio', 'slider', 'tab', 'tabpanel', 'menu', 'menuitem'];
            
            for (var i = 0; i < elementsWithRoles.length; i++) {
                var role = elementsWithRoles[i].getAttribute('role');
                ariaAnalysis.roles[role] = (ariaAnalysis.roles[role] || 0) + 1;
                
                if (landmarkRoles.includes(role)) ariaAnalysis.landmark_roles++;
                if (widgetRoles.includes(role)) ariaAnalysis.widget_roles++;
            }
            
            // Check for common ARIA issues
            var ariaHiddenInteractive = document.querySelectorAll('[aria-hidden="true"] button, [aria-hidden="true"] a, [aria-hidden="true"] input');
            if (ariaHiddenInteractive.length > 0) {
                ariaAnalysis.issues.push({
                    issue: 'Interactive elements hidden from screen readers',
                    count: ariaHiddenInteractive.length,
                    severity: 'serious',
                    suggestion: 'Remove aria-hidden from interactive elements or provide alternative access'
                });
            }
            
            // Check for missing aria-live on dynamic content
            var dynamicContent = document.querySelectorAll('.alert, .status, .error, .success');
            var dynamicWithoutLive = 0;
            for (var i = 0; i < dynamicContent.length; i++) {
                if (!dynamicContent[i].getAttribute('aria-live')) {
                    dynamicWithoutLive++;
                }
            }
            
            if (dynamicWithoutLive > 0) {
                ariaAnalysis.issues.push({
                    issue: 'Dynamic content without aria-live',
                    count: dynamicWithoutLive,
                    severity: 'moderate',
                    suggestion: 'Add aria-live attributes to announce dynamic changes'
                });
            }
            
            return ariaAnalysis;
            """
            
            return self.driver.execute_script(script)
            
        except Exception as e:
            self.logger.error(f"Error analyzing accessibility APIs: {e}")
            return {'error': str(e)}
    
    def _analyze_keyboard_support(self) -> Dict[str, Any]:
        """Analyze keyboard accessibility support"""
        try:
            script = """
            var keyboardAnalysis = {
                focusable_elements: 0,
                tabindex_positive: 0,
                tabindex_negative: 0,
                tabindex_zero: 0,
                keyboard_traps: [],
                skip_links: 0,
                custom_controls: 0,
                issues: []
            };
            
            // Find all focusable elements
            var focusableSelectors = [
                'a[href]', 'button:not([disabled])', 'input:not([disabled])', 
                'select:not([disabled])', 'textarea:not([disabled])', 
                '[tabindex]:not([tabindex="-1"])', '[contenteditable="true"]'
            ];
            
            var focusableElements = document.querySelectorAll(focusableSelectors.join(','));
            keyboardAnalysis.focusable_elements = focusableElements.length;
            
            // Analyze tabindex usage
            var elementsWithTabindex = document.querySelectorAll('[tabindex]');
            for (var i = 0; i < elementsWithTabindex.length; i++) {
                var tabindex = parseInt(elementsWithTabindex[i].getAttribute('tabindex'));
                if (tabindex > 0) keyboardAnalysis.tabindex_positive++;
                else if (tabindex === 0) keyboardAnalysis.tabindex_zero++;
                else if (tabindex === -1) keyboardAnalysis.tabindex_negative++;
            }
            
            // Check for positive tabindex (potential issue)
            if (keyboardAnalysis.tabindex_positive > 0) {
                keyboardAnalysis.issues.push({
                    issue: 'Positive tabindex values detected',
                    count: keyboardAnalysis.tabindex_positive,
                    severity: 'moderate',
                    suggestion: 'Avoid positive tabindex values - use logical DOM order instead'
                });
            }
            
            // Look for skip links
            var skipLinks = document.querySelectorAll('a[href*="#main"], a[href*="#content"], a[href*="#skip"]');
            keyboardAnalysis.skip_links = skipLinks.length;
            
            // Identify custom interactive controls
            var customControls = document.querySelectorAll('[role="button"]:not(button), [role="link"]:not(a), [role="checkbox"]:not(input), [role="radio"]:not(input)');
            keyboardAnalysis.custom_controls = customControls.length;
            
            if (keyboardAnalysis.custom_controls > 0) {
                keyboardAnalysis.issues.push({
                    issue: 'Custom interactive controls detected',
                    count: keyboardAnalysis.custom_controls,
                    severity: 'moderate',
                    suggestion: 'Ensure custom controls are keyboard accessible with proper event handlers'
                });
            }
            
            return keyboardAnalysis;
            """
            
            return self.driver.execute_script(script)
            
        except Exception as e:
            self.logger.error(f"Error analyzing keyboard support: {e}")
            return {'error': str(e)}
    
    def _analyze_aria_live_regions(self) -> Dict[str, Any]:
        """Analyze ARIA live regions for dynamic content announcements"""
        try:
            script = """
            var liveRegionAnalysis = {
                total_live_regions: 0,
                polite_regions: 0,
                assertive_regions: 0,
                off_regions: 0,
                atomic_regions: 0,
                relevant_specified: 0,
                issues: []
            };
            
            var liveRegions = document.querySelectorAll('[aria-live]');
            liveRegionAnalysis.total_live_regions = liveRegions.length;
            
            for (var i = 0; i < liveRegions.length; i++) {
                var region = liveRegions[i];
                var live = region.getAttribute('aria-live');
                var atomic = region.getAttribute('aria-atomic');
                var relevant = region.getAttribute('aria-relevant');
                
                // Count live region types
                if (live === 'polite') liveRegionAnalysis.polite_regions++;
                else if (live === 'assertive') liveRegionAnalysis.assertive_regions++;
                else if (live === 'off') liveRegionAnalysis.off_regions++;
                
                if (atomic) liveRegionAnalysis.atomic_regions++;
                if (relevant) liveRegionAnalysis.relevant_specified++;
                
                // Check for potential issues
                if (live === 'assertive' && !atomic) {
                    liveRegionAnalysis.issues.push({
                        element: region.tagName + (region.className ? '.' + region.className.split(' ')[0] : ''),
                        issue: 'Assertive live region without aria-atomic',
                        severity: 'minor',
                        suggestion: 'Consider adding aria-atomic="true" for assertive regions'
                    });
                }
                
                // Check if live region is empty
                if (!region.textContent.trim()) {
                    liveRegionAnalysis.issues.push({
                        element: region.tagName + (region.id ? '#' + region.id : ''),
                        issue: 'Empty live region',
                        severity: 'minor',
                        suggestion: 'Ensure live regions have meaningful content when active'
                    });
                }
            }
            
            return liveRegionAnalysis;
            """
            
            return self.driver.execute_script(script)
            
        except Exception as e:
            self.logger.error(f"Error analyzing ARIA live regions: {e}")
            return {'error': str(e)}
    
    def _analyze_focus_management(self) -> Dict[str, Any]:
        """Analyze focus management implementation"""
        try:
            script = """
            var focusAnalysis = {
                focus_calls: 0,
                blur_calls: 0,
                focus_traps: 0,
                modal_elements: 0,
                focus_indicators: {
                    outline_removed: 0,
                    custom_indicators: 0
                },
                issues: []
            };
            
            // Check for modal/dialog elements that need focus management
            var modals = document.querySelectorAll('[role="dialog"], .modal, .overlay, .popup');
            focusAnalysis.modal_elements = modals.length;
            
            // Check for elements with outline removed (potential accessibility issue)
            var allElements = document.querySelectorAll('*');
            var outlineRemoved = 0;
            var customFocusIndicators = 0;
            
            for (var i = 0; i < Math.min(100, allElements.length); i++) { // Sample first 100 elements
                var element = allElements[i];
                var styles = window.getComputedStyle(element);
                
                if (styles.outline === 'none' || styles.outlineWidth === '0px') {
                    outlineRemoved++;
                    
                    // Check if there's a custom focus indicator
                    if (styles.boxShadow !== 'none' || styles.border !== 'none' || styles.backgroundColor !== 'rgba(0, 0, 0, 0)') {
                        customFocusIndicators++;
                    }
                }
            }
            
            focusAnalysis.focus_indicators.outline_removed = outlineRemoved;
            focusAnalysis.focus_indicators.custom_indicators = customFocusIndicators;
            
            // Identify potential focus management issues
            if (focusAnalysis.modal_elements > 0 && focusAnalysis.focus_calls === 0) {
                focusAnalysis.issues.push({
                    issue: 'Modal elements without apparent focus management',
                    count: focusAnalysis.modal_elements,
                    severity: 'serious',
                    suggestion: 'Implement proper focus management for modal dialogs'
                });
            }
            
            if (outlineRemoved > customFocusIndicators) {
                focusAnalysis.issues.push({
                    issue: 'Focus outline removed without custom indicators',
                    count: outlineRemoved - customFocusIndicators,
                    severity: 'moderate',
                    suggestion: 'Provide custom focus indicators when removing default outline'
                });
            }
            
            return focusAnalysis;
            """
            
            return self.driver.execute_script(script)
            
        except Exception as e:
            self.logger.error(f"Error analyzing focus management: {e}")
            return {'error': str(e)}
    
    def _analyze_error_handling(self) -> Dict[str, Any]:
        """Analyze JavaScript error handling for accessibility"""
        try:
            script = """
            var errorAnalysis = {
                error_boundaries: 0,
                try_catch_blocks: 0, // Approximate
                console_errors: [],
                graceful_degradation: {
                    noscript_tags: document.querySelectorAll('noscript').length,
                    fallback_content: 0
                },
                accessibility_considerations: []
            };
            
            // Check for noscript tags (good for graceful degradation)
            if (errorAnalysis.graceful_degradation.noscript_tags === 0) {
                errorAnalysis.accessibility_considerations.push({
                    issue: 'No noscript fallbacks detected',
                    severity: 'minor',
                    suggestion: 'Consider providing noscript fallbacks for critical functionality'
                });
            }
            
            // Check for elements that might need error handling
            var formElements = document.querySelectorAll('form input[required], form select[required], form textarea[required]');
            if (formElements.length > 0) {
                errorAnalysis.accessibility_considerations.push({
                    issue: 'Required form elements detected',
                    count: formElements.length,
                    suggestion: 'Ensure form validation errors are announced to screen readers'
                });
            }
            
            return errorAnalysis;
            """
            
            return self.driver.execute_script(script)
            
        except Exception as e:
            self.logger.error(f"Error analyzing error handling: {e}")
            return {'error': str(e)}
    
    def _analyze_performance_impact(self) -> Dict[str, Any]:
        """Analyze JavaScript performance impact on accessibility"""
        try:
            script = """
            var performanceAnalysis = {
                heavy_scripts: 0,
                blocking_scripts: 0,
                performance_issues: [],
                accessibility_impact: []
            };
            
            // Check script loading patterns
            var scripts = document.querySelectorAll('script');
            var blockingScripts = 0;
            var asyncScripts = 0;
            
            for (var i = 0; i < scripts.length; i++) {
                var script = scripts[i];
                if (!script.async && !script.defer && script.src) {
                    blockingScripts++;
                }
                if (script.async) asyncScripts++;
            }
            
            performanceAnalysis.blocking_scripts = blockingScripts;
            
            // Performance timing (if available)
            if (window.performance && window.performance.timing) {
                var timing = window.performance.timing;
                var loadTime = timing.loadEventEnd - timing.navigationStart;
                
                if (loadTime > 3000) { // More than 3 seconds
                    performanceAnalysis.accessibility_impact.push({
                        issue: 'Slow page load time',
                        value: loadTime + 'ms',
                        impact: 'May affect users with cognitive disabilities who need faster response times'
                    });
                }
            }
            
            // Check for potentially heavy animations
            var animatedElements = document.querySelectorAll('[style*="animation"], .animate, [data-animate]');
            if (animatedElements.length > 10) {
                performanceAnalysis.accessibility_impact.push({
                    issue: 'Many animated elements detected',
                    count: animatedElements.length,
                    impact: 'May cause issues for users with vestibular disorders or slow devices'
                });
            }
            
            return performanceAnalysis;
            """
            
            return self.driver.execute_script(script)
            
        except Exception as e:
            self.logger.error(f"Error analyzing performance impact: {e}")
            return {'error': str(e)}
    
    def _calculate_accessibility_score(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall JavaScript accessibility score"""
        try:
            score = 100
            deductions = []
            
            # Analyze script issues
            scripts = analysis.get('scripts', {})
            if scripts.get('total_concerns', 0) > 0:
                deduction = min(scripts['total_concerns'] * 5, 20)
                score -= deduction
                deductions.append(f"Script accessibility concerns: -{deduction}")
            
            # Analyze event handler issues
            events = analysis.get('event_handlers', {})
            mouse_only = events.get('mouse_only', 0)
            if mouse_only > 0:
                deduction = min(mouse_only * 10, 30)
                score -= deduction
                deductions.append(f"Mouse-only interactions: -{deduction}")
            
            # Analyze ARIA issues
            aria = analysis.get('accessibility_apis', {})
            aria_issues = len(aria.get('issues', []))
            if aria_issues > 0:
                deduction = min(aria_issues * 8, 25)
                score -= deduction
                deductions.append(f"ARIA implementation issues: -{deduction}")
            
            # Analyze keyboard support
            keyboard = analysis.get('keyboard_support', {})
            keyboard_issues = len(keyboard.get('issues', []))
            if keyboard_issues > 0:
                deduction = min(keyboard_issues * 10, 25)
                score -= deduction
                deductions.append(f"Keyboard accessibility issues: -{deduction}")
            
            # Analyze focus management
            focus = analysis.get('focus_management', {})
            focus_issues = len(focus.get('issues', []))
            if focus_issues > 0:
                deduction = min(focus_issues * 8, 20)
                score -= deduction
                deductions.append(f"Focus management issues: -{deduction}")
            
            score = max(0, score)
            
            # Determine grade
            if score >= 90:
                grade = 'A'
                status = 'Excellent'
            elif score >= 80:
                grade = 'B'
                status = 'Good'
            elif score >= 70:
                grade = 'C'
                status = 'Fair'
            elif score >= 60:
                grade = 'D'
                status = 'Poor'
            else:
                grade = 'F'
                status = 'Critical'
            
            return {
                'score': score,
                'grade': grade,
                'status': status,
                'deductions': deductions,
                'total_issues': sum(len(section.get('issues', [])) for section in analysis.values() if isinstance(section, dict))
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating accessibility score: {e}")
            return {
                'score': 0,
                'grade': 'F',
                'status': 'Error calculating score',
                'deductions': [f'Calculation error: {str(e)}'],
                'total_issues': 0
            }
    
    def test_javascript_accessibility(self, element: WebElement) -> Dict[str, Any]:
        """
        Test JavaScript accessibility for a specific element
        
        Args:
            element: WebElement to test for JavaScript accessibility
            
        Returns:
            Detailed accessibility test results for the element
        """
        try:
            # Get element information
            tag_name = element.tag_name
            element_id = element.get_attribute('id') or ''
            class_name = element.get_attribute('class') or ''
            
            # Test JavaScript-related accessibility
            script = """
            var element = arguments[0];
            var results = {
                element_info: {
                    tag: element.tagName,
                    id: element.id,
                    classes: element.className,
                    role: element.getAttribute('role')
                },
                event_handlers: {},
                keyboard_accessibility: {},
                aria_support: {},
                focus_management: {},
                issues: [],
                recommendations: []
            };
            
            // Check for event handlers
            var eventProps = ['onclick', 'onmousedown', 'onmouseup', 'onmouseover', 'onmouseout',
                             'onkeydown', 'onkeyup', 'onkeypress', 'onfocus', 'onblur'];
            
            eventProps.forEach(function(prop) {
                if (element[prop] || element.getAttribute(prop)) {
                    results.event_handlers[prop] = true;
                }
            });
            
            // Analyze keyboard accessibility
            var hasKeyboardHandler = results.event_handlers.onkeydown || 
                                   results.event_handlers.onkeyup || 
                                   results.event_handlers.onkeypress;
            var hasMouseHandler = results.event_handlers.onclick || 
                                results.event_handlers.onmousedown || 
                                results.event_handlers.onmouseup;
            
            results.keyboard_accessibility = {
                has_keyboard_handlers: hasKeyboardHandler,
                has_mouse_handlers: hasMouseHandler,
                is_focusable: element.tabIndex >= 0 || ['A', 'BUTTON', 'INPUT', 'SELECT', 'TEXTAREA'].includes(element.tagName),
                tabindex: element.tabIndex
            };
            
            // Check ARIA support
            var ariaProps = ['aria-label', 'aria-labelledby', 'aria-describedby', 'aria-expanded', 
                           'aria-controls', 'aria-hidden', 'aria-live'];
            
            ariaProps.forEach(function(prop) {
                var value = element.getAttribute(prop);
                if (value !== null) {
                    results.aria_support[prop] = value;
                }
            });
            
            // Identify issues
            if (hasMouseHandler && !hasKeyboardHandler) {
                results.issues.push({
                    type: 'keyboard_accessibility',
                    severity: 'serious',
                    message: 'Element has mouse handlers but no keyboard handlers',
                    recommendation: 'Add keyboard event handlers (onkeydown/onkeyup) for accessibility'
                });
            }
            
            if (results.keyboard_accessibility.is_focusable && !results.aria_support['aria-label'] && 
                !results.aria_support['aria-labelledby'] && !element.textContent.trim()) {
                results.issues.push({
                    type: 'labeling',
                    severity: 'serious',
                    message: 'Focusable element lacks accessible name',
                    recommendation: 'Add aria-label, aria-labelledby, or visible text content'
                });
            }
            
            if (element.getAttribute('role') === 'button' && element.tagName !== 'BUTTON') {
                if (!hasKeyboardHandler) {
                    results.issues.push({
                        type: 'custom_control',
                        severity: 'serious',
                        message: 'Custom button role without keyboard support',
                        recommendation: 'Add keyboard event handlers for Enter and Space keys'
                    });
                }
            }
            
            return results;
            """
            
            return self.driver.execute_script(script, element)
            
        except Exception as e:
            self.logger.error(f"Error testing element JavaScript accessibility: {e}")
            return {
                'error': str(e),
                'element_info': {
                    'tag': tag_name,
                    'id': element_id,
                    'classes': class_name
                }
            }