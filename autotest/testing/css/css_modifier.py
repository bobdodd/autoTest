"""
CSS Modification Tester for AutoTest
Provides comprehensive CSS modification testing capabilities for accessibility analysis.
"""

import json
import logging
import uuid
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import WebDriverException, JavascriptException

from .css_analyzer import CSSAnalyzer


class CSSModificationTester:
    """
    Advanced CSS modification testing for accessibility improvements.
    Tests various CSS modifications and analyzes their accessibility impact.
    """
    
    def __init__(self, driver, db_connection=None):
        """
        Initialize CSS modification tester
        
        Args:
            driver: Selenium WebDriver instance
            db_connection: Optional database connection for storing results
        """
        self.driver = driver
        self.db_connection = db_connection
        self.css_analyzer = CSSAnalyzer(driver)
        self.logger = logging.getLogger(__name__)
    
    def test_css_changes(self, page_id: str, css_modifications: Dict[str, Any]) -> Dict[str, Any]:
        """
        Test CSS modifications on a page and analyze accessibility impact
        
        Args:
            page_id: Page identifier to test
            css_modifications: Dictionary of CSS modifications to test
            
        Returns:
            Comprehensive test results with before/after analysis
        """
        try:
            test_id = str(uuid.uuid4())
            
            # Initialize test session
            test_session = {
                'test_id': test_id,
                'page_id': page_id,
                'start_time': datetime.now(),
                'modifications': css_modifications,
                'results': {},
                'summary': {}
            }
            
            # Run different types of modifications
            if 'element_modifications' in css_modifications:
                test_session['results']['element_tests'] = self._test_element_modifications(
                    css_modifications['element_modifications']
                )
            
            if 'global_modifications' in css_modifications:
                test_session['results']['global_tests'] = self._test_global_modifications(
                    css_modifications['global_modifications']
                )
            
            if 'accessibility_improvements' in css_modifications:
                test_session['results']['improvement_tests'] = self._test_accessibility_improvements(
                    css_modifications['accessibility_improvements']
                )
            
            if 'responsive_modifications' in css_modifications:
                test_session['results']['responsive_tests'] = self._test_responsive_modifications(
                    css_modifications['responsive_modifications']
                )
            
            # Generate comprehensive summary
            test_session['summary'] = self._generate_test_summary(test_session['results'])
            test_session['end_time'] = datetime.now()
            test_session['duration'] = (test_session['end_time'] - test_session['start_time']).total_seconds()
            
            # Store results if database connection available
            if self.db_connection:
                self._store_test_results(test_session)
            
            return test_session
            
        except Exception as e:
            self.logger.error(f"Error testing CSS changes: {e}")
            return {'error': str(e)}
    
    def _test_element_modifications(self, element_modifications: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Test modifications on specific elements"""
        results = []
        
        for modification in element_modifications:
            try:
                # Find target elements
                selector = modification.get('selector', '')
                css_changes = modification.get('css_changes', {})
                
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                
                if not elements:
                    results.append({
                        'selector': selector,
                        'status': 'error',
                        'message': 'No elements found for selector',
                        'css_changes': css_changes
                    })
                    continue
                
                # Test each element
                element_results = []
                for i, element in enumerate(elements[:10]):  # Limit to 10 elements for performance
                    element_result = self.css_analyzer.test_style_modifications(element, css_changes)
                    element_result['element_index'] = i
                    element_results.append(element_result)
                
                results.append({
                    'selector': selector,
                    'status': 'success',
                    'css_changes': css_changes,
                    'elements_tested': len(element_results),
                    'element_results': element_results,
                    'aggregated_impact': self._aggregate_element_impacts(element_results)
                })
                
            except Exception as e:
                self.logger.error(f"Error testing element modification: {e}")
                results.append({
                    'selector': modification.get('selector', ''),
                    'status': 'error',
                    'message': str(e),
                    'css_changes': modification.get('css_changes', {})
                })
        
        return results
    
    def _test_global_modifications(self, global_modifications: Dict[str, Any]) -> Dict[str, Any]:
        """Test global CSS modifications (e.g., injecting new stylesheets)"""
        try:
            # Create unique stylesheet ID
            stylesheet_id = f"autotest-global-{uuid.uuid4().hex[:8]}"
            
            # Get baseline accessibility analysis
            baseline_analysis = self._get_page_accessibility_snapshot()
            
            # Inject global CSS
            css_rules = global_modifications.get('css_rules', '')
            self._inject_global_css(css_rules, stylesheet_id)
            
            # Get analysis after modifications
            modified_analysis = self._get_page_accessibility_snapshot()
            
            # Remove injected CSS
            self._remove_global_css(stylesheet_id)
            
            # Compare results
            comparison = self._compare_page_snapshots(baseline_analysis, modified_analysis)
            
            return {
                'status': 'success',
                'css_rules': css_rules,
                'baseline_analysis': baseline_analysis,
                'modified_analysis': modified_analysis,
                'comparison': comparison,
                'impact_assessment': self._assess_global_impact(comparison)
            }
            
        except Exception as e:
            self.logger.error(f"Error testing global modifications: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def _test_accessibility_improvements(self, improvements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Test specific accessibility improvement scenarios"""
        results = []
        
        for improvement in improvements:
            try:
                improvement_type = improvement.get('type', '')
                
                if improvement_type == 'contrast_enhancement':
                    result = self._test_contrast_improvements(improvement)
                elif improvement_type == 'focus_enhancement':
                    result = self._test_focus_improvements(improvement)
                elif improvement_type == 'font_scaling':
                    result = self._test_font_scaling(improvement)
                elif improvement_type == 'motion_reduction':
                    result = self._test_motion_reduction(improvement)
                elif improvement_type == 'layout_accessibility':
                    result = self._test_layout_accessibility(improvement)
                else:
                    result = {
                        'type': improvement_type,
                        'status': 'error',
                        'message': f'Unknown improvement type: {improvement_type}'
                    }
                
                results.append(result)
                
            except Exception as e:
                self.logger.error(f"Error testing accessibility improvement: {e}")
                results.append({
                    'type': improvement.get('type', ''),
                    'status': 'error',
                    'message': str(e)
                })
        
        return results
    
    def _test_responsive_modifications(self, responsive_mods: Dict[str, Any]) -> Dict[str, Any]:
        """Test responsive design modifications"""
        try:
            results = {}
            viewports = responsive_mods.get('viewports', [
                {'width': 320, 'height': 568, 'name': 'mobile'},
                {'width': 768, 'height': 1024, 'name': 'tablet'},
                {'width': 1440, 'height': 900, 'name': 'desktop'}
            ])
            
            # Store original viewport size
            original_size = self.driver.get_window_size()
            
            for viewport in viewports:
                try:
                    # Set viewport size
                    self.driver.set_window_size(viewport['width'], viewport['height'])
                    
                    # Test CSS modifications at this viewport
                    viewport_results = self._test_viewport_modifications(
                        responsive_mods.get('css_changes', {}),
                        viewport
                    )
                    
                    results[viewport['name']] = viewport_results
                    
                except Exception as e:
                    self.logger.error(f"Error testing viewport {viewport['name']}: {e}")
                    results[viewport['name']] = {
                        'status': 'error',
                        'message': str(e)
                    }
            
            # Restore original viewport
            self.driver.set_window_size(original_size['width'], original_size['height'])
            
            return {
                'status': 'success',
                'viewport_results': results,
                'responsive_summary': self._generate_responsive_summary(results)
            }
            
        except Exception as e:
            self.logger.error(f"Error testing responsive modifications: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def _test_contrast_improvements(self, improvement: Dict[str, Any]) -> Dict[str, Any]:
        """Test color contrast improvements"""
        try:
            target_selectors = improvement.get('selectors', [])
            contrast_adjustments = improvement.get('adjustments', {})
            
            results = []
            
            for selector in target_selectors:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                
                for element in elements[:5]:  # Test up to 5 elements
                    # Get current contrast
                    baseline_analysis = self.css_analyzer.analyze_accessibility_properties(element)
                    baseline_contrast = self._extract_contrast_info(baseline_analysis)
                    
                    # Test each contrast adjustment
                    adjustment_results = []
                    for adjustment_name, css_changes in contrast_adjustments.items():
                        modification_result = self.css_analyzer.test_style_modifications(element, css_changes)
                        after_contrast = self._extract_contrast_info(modification_result.get('after', {}))
                        
                        adjustment_results.append({
                            'adjustment_name': adjustment_name,
                            'css_changes': css_changes,
                            'baseline_contrast': baseline_contrast,
                            'improved_contrast': after_contrast,
                            'improvement_score': self._calculate_contrast_improvement_score(
                                baseline_contrast, after_contrast
                            )
                        })
                    
                    results.append({
                        'selector': selector,
                        'element_analysis': baseline_analysis,
                        'adjustments': adjustment_results
                    })
            
            return {
                'type': 'contrast_enhancement',
                'status': 'success',
                'results': results,
                'best_adjustments': self._identify_best_contrast_adjustments(results)
            }
            
        except Exception as e:
            return {
                'type': 'contrast_enhancement',
                'status': 'error',
                'message': str(e)
            }
    
    def _test_focus_improvements(self, improvement: Dict[str, Any]) -> Dict[str, Any]:
        """Test focus indicator improvements"""
        try:
            interactive_selectors = improvement.get('selectors', [
                'a', 'button', 'input', 'select', 'textarea', '[tabindex]'
            ])
            focus_styles = improvement.get('focus_styles', {})
            
            results = []
            
            for selector in interactive_selectors:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                
                for element in elements[:10]:  # Test up to 10 elements
                    try:
                        # Focus the element
                        element.click()
                        
                        # Get baseline focus analysis
                        baseline_focus = self.css_analyzer.analyze_accessibility_properties(element)
                        
                        # Test focus improvements
                        focus_results = []
                        for style_name, css_changes in focus_styles.items():
                            # Apply focus styles
                            focus_result = self.css_analyzer.test_style_modifications(element, css_changes)
                            
                            focus_results.append({
                                'style_name': style_name,
                                'css_changes': css_changes,
                                'focus_visibility_score': self._calculate_focus_visibility_score(
                                    focus_result.get('after', {})
                                ),
                                'result': focus_result
                            })
                        
                        results.append({
                            'selector': selector,
                            'baseline_focus': baseline_focus,
                            'focus_improvements': focus_results
                        })
                        
                    except Exception as e:
                        self.logger.warning(f"Could not test focus for element: {e}")
                        continue
            
            return {
                'type': 'focus_enhancement',
                'status': 'success',
                'results': results,
                'recommendations': self._generate_focus_recommendations(results)
            }
            
        except Exception as e:
            return {
                'type': 'focus_enhancement',
                'status': 'error',
                'message': str(e)
            }
    
    def _test_font_scaling(self, improvement: Dict[str, Any]) -> Dict[str, Any]:
        """Test font scaling for readability"""
        try:
            text_selectors = improvement.get('selectors', ['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'span', 'div'])
            scale_factors = improvement.get('scale_factors', [1.1, 1.25, 1.5, 2.0])
            
            results = []
            
            for selector in text_selectors:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                
                for element in elements[:5]:  # Test up to 5 elements per selector
                    # Get baseline typography analysis
                    baseline = self.css_analyzer.analyze_accessibility_properties(element)
                    baseline_font_size = baseline.get('typography_analysis', {}).get('font_size_px', 16)
                    
                    scale_results = []
                    for scale in scale_factors:
                        new_font_size = f"{baseline_font_size * scale}px"
                        css_changes = {'font-size': new_font_size}
                        
                        scale_result = self.css_analyzer.test_style_modifications(element, css_changes)
                        readability_score = scale_result.get('after', {}).get('typography_analysis', {}).get('readability_score', {})
                        
                        scale_results.append({
                            'scale_factor': scale,
                            'new_font_size': new_font_size,
                            'readability_score': readability_score,
                            'accessibility_impact': self._assess_font_scaling_impact(scale, baseline, scale_result)
                        })
                    
                    results.append({
                        'selector': selector,
                        'baseline_font_size': baseline_font_size,
                        'scaling_results': scale_results
                    })
            
            return {
                'type': 'font_scaling',
                'status': 'success',
                'results': results,
                'optimal_scales': self._identify_optimal_font_scales(results)
            }
            
        except Exception as e:
            return {
                'type': 'font_scaling',
                'status': 'error',
                'message': str(e)
            }
    
    def _test_motion_reduction(self, improvement: Dict[str, Any]) -> Dict[str, Any]:
        """Test motion reduction modifications"""
        try:
            # Find animated elements
            animated_elements = self.driver.find_elements(By.CSS_SELECTOR, 
                                                        '[style*="animation"], [class*="animate"]')
            
            motion_reductions = improvement.get('reductions', {
                'disable_animations': {'animation': 'none', 'transition': 'none'},
                'reduce_motion': {'animation-duration': '0.01s', 'transition-duration': '0.01s'},
                'respect_preference': {'animation': 'var(--reduced-motion, none)'}
            })
            
            results = []
            
            for element in animated_elements[:10]:  # Test up to 10 animated elements
                baseline_motion = self.css_analyzer.analyze_accessibility_properties(element)
                
                reduction_results = []
                for reduction_name, css_changes in motion_reductions.items():
                    reduction_result = self.css_analyzer.test_style_modifications(element, css_changes)
                    
                    reduction_results.append({
                        'reduction_type': reduction_name,
                        'css_changes': css_changes,
                        'motion_analysis': reduction_result.get('after', {}).get('motion_analysis', {}),
                        'accessibility_benefit': self._assess_motion_reduction_benefit(
                            baseline_motion, reduction_result
                        )
                    })
                
                results.append({
                    'element': {
                        'tag': element.tag_name,
                        'classes': element.get_attribute('class') or '',
                    },
                    'baseline_motion': baseline_motion.get('motion_analysis', {}),
                    'reductions': reduction_results
                })
            
            return {
                'type': 'motion_reduction',
                'status': 'success',
                'results': results,
                'recommendations': self._generate_motion_recommendations(results)
            }
            
        except Exception as e:
            return {
                'type': 'motion_reduction',
                'status': 'error',
                'message': str(e)
            }
    
    def _test_layout_accessibility(self, improvement: Dict[str, Any]) -> Dict[str, Any]:
        """Test layout accessibility improvements"""
        try:
            layout_tests = improvement.get('tests', [])
            results = []
            
            for test in layout_tests:
                test_type = test.get('type', '')
                
                if test_type == 'flexible_layout':
                    result = self._test_flexible_layout(test)
                elif test_type == 'touch_targets':
                    result = self._test_touch_targets(test)
                elif test_type == 'content_reflow':
                    result = self._test_content_reflow(test)
                else:
                    result = {
                        'type': test_type,
                        'status': 'error',
                        'message': f'Unknown layout test type: {test_type}'
                    }
                
                results.append(result)
            
            return {
                'type': 'layout_accessibility',
                'status': 'success',
                'results': results,
                'summary': self._generate_layout_summary(results)
            }
            
        except Exception as e:
            return {
                'type': 'layout_accessibility',
                'status': 'error',
                'message': str(e)
            }
    
    # Helper methods for analysis and comparison
    def _get_page_accessibility_snapshot(self) -> Dict[str, Any]:
        """Get a comprehensive accessibility snapshot of the current page"""
        try:
            # Get all interactive elements
            interactive_elements = self.driver.find_elements(By.CSS_SELECTOR, 
                'a, button, input, select, textarea, [tabindex], [role="button"], [role="link"]')
            
            snapshot = {
                'timestamp': datetime.now().isoformat(),
                'url': self.driver.current_url,
                'title': self.driver.title,
                'interactive_elements': []
            }
            
            for element in interactive_elements[:50]:  # Limit for performance
                try:
                    element_analysis = self.css_analyzer.analyze_accessibility_properties(element)
                    snapshot['interactive_elements'].append({
                        'tag_name': element.tag_name,
                        'classes': element.get_attribute('class') or '',
                        'id': element.get_attribute('id') or '',
                        'analysis': element_analysis
                    })
                except Exception:
                    continue
            
            return snapshot
            
        except Exception as e:
            self.logger.error(f"Error creating page snapshot: {e}")
            return {}
    
    def _inject_global_css(self, css_rules: str, stylesheet_id: str):
        """Inject global CSS into the page"""
        script = f"""
        var style = document.createElement('style');
        style.id = '{stylesheet_id}';
        style.textContent = `{css_rules}`;
        document.head.appendChild(style);
        """
        self.driver.execute_script(script)
    
    def _remove_global_css(self, stylesheet_id: str):
        """Remove injected global CSS"""
        script = f"""
        var style = document.getElementById('{stylesheet_id}');
        if (style) {{
            style.remove();
        }}
        """
        self.driver.execute_script(script)
    
    def _compare_page_snapshots(self, baseline: Dict[str, Any], modified: Dict[str, Any]) -> Dict[str, Any]:
        """Compare two page accessibility snapshots"""
        return {
            'elements_analyzed': {
                'baseline': len(baseline.get('interactive_elements', [])),
                'modified': len(modified.get('interactive_elements', []))
            },
            'differences': self._identify_snapshot_differences(baseline, modified),
            'improvement_score': self._calculate_improvement_score(baseline, modified)
        }
    
    # Additional helper methods would continue here...
    # (Truncated for brevity, but would include all the helper methods referenced above)
    
    def _generate_test_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive test summary"""
        summary = {
            'total_tests': 0,
            'successful_tests': 0,
            'failed_tests': 0,
            'improvements_identified': [],
            'issues_found': [],
            'recommendations': []
        }
        
        # Analyze results from all test types
        for test_type, test_results in results.items():
            if isinstance(test_results, list):
                summary['total_tests'] += len(test_results)
                summary['successful_tests'] += len([r for r in test_results if r.get('status') == 'success'])
                summary['failed_tests'] += len([r for r in test_results if r.get('status') == 'error'])
            elif isinstance(test_results, dict) and test_results.get('status') == 'success':
                summary['total_tests'] += 1
                summary['successful_tests'] += 1
        
        return summary
    
    def _store_test_results(self, test_session: Dict[str, Any]):
        """Store test results in database"""
        try:
            if self.db_connection:
                # Store in css_modification_tests collection
                collection = self.db_connection.db.css_modification_tests
                collection.insert_one(test_session)
                self.logger.info(f"Stored CSS modification test results: {test_session['test_id']}")
        except Exception as e:
            self.logger.error(f"Error storing test results: {e}")
    
    # Placeholder methods for specific analysis functions
    # These would be fully implemented in a production version
    def _aggregate_element_impacts(self, element_results): return {}
    def _assess_global_impact(self, comparison): return {}
    def _extract_contrast_info(self, analysis): return {}
    def _calculate_contrast_improvement_score(self, baseline, improved): return 0
    def _identify_best_contrast_adjustments(self, results): return []
    def _calculate_focus_visibility_score(self, analysis): return 0
    def _generate_focus_recommendations(self, results): return []
    def _assess_font_scaling_impact(self, scale, baseline, result): return {}
    def _identify_optimal_font_scales(self, results): return []
    def _assess_motion_reduction_benefit(self, baseline, result): return {}
    def _generate_motion_recommendations(self, results): return []
    def _test_flexible_layout(self, test): return {'status': 'success'}
    def _test_touch_targets(self, test): return {'status': 'success'}
    def _test_content_reflow(self, test): return {'status': 'success'}
    def _generate_layout_summary(self, results): return {}
    def _test_viewport_modifications(self, css_changes, viewport): return {}
    def _generate_responsive_summary(self, results): return {}
    def _identify_snapshot_differences(self, baseline, modified): return []
    def _calculate_improvement_score(self, baseline, modified): return 0