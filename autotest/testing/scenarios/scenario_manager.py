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
Scenario Manager for AutoTest
Manages and orchestrates comprehensive page modification testing scenarios.
"""

import json
import logging
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict

from ..css import CSSAnalyzer, CSSModificationTester
from ..javascript import JavaScriptAnalyzer, JSDynamicTester


@dataclass
class TestScenario:
    """
    Test scenario definition combining CSS and JavaScript modifications
    """
    scenario_id: str
    name: str
    description: str
    category: str
    priority: str
    css_modifications: Optional[Dict[str, Any]] = None
    js_test_scenarios: Optional[List[str]] = None
    expected_improvements: Optional[List[str]] = None
    validation_criteria: Optional[Dict[str, Any]] = None
    wcag_compliance: Optional[str] = None


class ScenarioManager:
    """
    Comprehensive page modification testing scenario manager.
    Combines CSS and JavaScript testing for complete accessibility scenarios.
    """
    
    def __init__(self, driver, db_connection=None):
        """
        Initialize scenario manager
        
        Args:
            driver: Selenium WebDriver instance
            db_connection: Optional database connection for storing results
        """
        self.driver = driver
        self.db_connection = db_connection
        self.logger = logging.getLogger(__name__)
        
        # Initialize testing components
        self.css_analyzer = CSSAnalyzer(driver)
        self.css_modifier = CSSModificationTester(driver, db_connection)
        self.js_analyzer = JavaScriptAnalyzer(driver)
        self.js_dynamic_tester = JSDynamicTester(driver, db_connection)
        
        # Load predefined scenarios
        self.scenarios = self._initialize_scenarios()
    
    def _initialize_scenarios(self) -> Dict[str, TestScenario]:
        """Initialize comprehensive testing scenarios"""
        scenarios = {}
        
        # Keyboard Accessibility Enhancement Scenario
        scenarios['keyboard_enhancement'] = TestScenario(
            scenario_id='keyboard_enhancement',
            name='Keyboard Accessibility Enhancement',
            description='Comprehensive keyboard accessibility improvements across CSS and JavaScript',
            category='interaction',
            priority='high',
            css_modifications={
                'element_modifications': [
                    {
                        'selector': 'button, [role="button"], a, input, select, textarea',
                        'css_changes': {
                            'outline': '2px solid #007acc',
                            'outline-offset': '2px',
                            'min-width': '44px',
                            'min-height': '44px'
                        }
                    },
                    {
                        'selector': ':focus',
                        'css_changes': {
                            'outline': '2px solid #007acc',
                            'outline-offset': '2px',
                            'box-shadow': '0 0 0 4px rgba(0, 122, 204, 0.3)'
                        }
                    }
                ]
            },
            js_test_scenarios=['keyboard_navigation', 'focus_management', 'custom_controls'],
            expected_improvements=[
                'All interactive elements have visible focus indicators',
                'Minimum touch target sizes met (44x44px)',
                'Keyboard navigation works throughout interface',
                'Focus management properly implemented'
            ],
            validation_criteria={
                'focus_visibility_score': {'min': 90},
                'keyboard_accessibility_rate': {'min': 95},
                'touch_target_compliance': {'min': 100}
            },
            wcag_compliance='2.1 AA'
        )
        
        # Color Contrast Enhancement Scenario
        scenarios['contrast_enhancement'] = TestScenario(
            scenario_id='contrast_enhancement',
            name='Color Contrast Enhancement',
            description='Comprehensive color contrast improvements for accessibility',
            category='visual',
            priority='high',
            css_modifications={
                'accessibility_improvements': [
                    {
                        'type': 'contrast_enhancement',
                        'selectors': ['button', 'a', '.btn', '.link', 'input', 'select'],
                        'adjustments': {
                            'high_contrast': {
                                'color': '#000000',
                                'background-color': '#ffffff',
                                'border': '2px solid #333333'
                            },
                            'dark_theme': {
                                'color': '#ffffff',
                                'background-color': '#1a1a1a',
                                'border': '2px solid #666666'
                            },
                            'enhanced_contrast': {
                                'color': '#003366',
                                'background-color': '#f0f8ff',
                                'border': '1px solid #0066cc'
                            }
                        }
                    }
                ]
            },
            js_test_scenarios=['dynamic_content', 'loading_states'],
            expected_improvements=[
                'All text meets WCAG AA contrast ratios (4.5:1 minimum)',
                'Interactive elements have sufficient contrast',
                'Dynamic content maintains contrast requirements',
                'Loading states are visually accessible'
            ],
            validation_criteria={
                'contrast_compliance_rate': {'min': 100},
                'color_accessibility_score': {'min': 85}
            },
            wcag_compliance='2.1 AA'
        )
        
        # Form Accessibility Enhancement Scenario
        scenarios['form_enhancement'] = TestScenario(
            scenario_id='form_enhancement',
            name='Form Accessibility Enhancement',
            description='Complete form accessibility improvements including validation and error handling',
            category='forms',
            priority='high',
            css_modifications={
                'element_modifications': [
                    {
                        'selector': 'input, select, textarea',
                        'css_changes': {
                            'border': '2px solid #ccc',
                            'padding': '8px 12px',
                            'font-size': '16px',
                            'line-height': '1.5'
                        }
                    },
                    {
                        'selector': 'input:focus, select:focus, textarea:focus',
                        'css_changes': {
                            'border-color': '#007acc',
                            'outline': '2px solid #007acc',
                            'outline-offset': '2px'
                        }
                    },
                    {
                        'selector': '.error',
                        'css_changes': {
                            'color': '#d63031',
                            'background-color': '#fff5f5',
                            'border': '1px solid #fab1a0',
                            'padding': '8px',
                            'border-radius': '4px'
                        }
                    }
                ]
            },
            js_test_scenarios=['form_interactions', 'error_handling', 'dynamic_content'],
            expected_improvements=[
                'All form fields have proper labels',
                'Error messages are announced to screen readers',
                'Form validation is keyboard accessible',
                'Required fields are clearly indicated'
            ],
            validation_criteria={
                'form_accessibility_score': {'min': 90},
                'error_announcement_rate': {'min': 100},
                'label_association_rate': {'min': 100}
            },
            wcag_compliance='2.1 AA'
        )
        
        # Modal Dialog Enhancement Scenario
        scenarios['modal_enhancement'] = TestScenario(
            scenario_id='modal_enhancement',
            name='Modal Dialog Enhancement',
            description='Complete modal dialog accessibility including focus trapping and ARIA implementation',
            category='interaction',
            priority='high',
            css_modifications={
                'element_modifications': [
                    {
                        'selector': '[role="dialog"], .modal',
                        'css_changes': {
                            'border': '3px solid #007acc',
                            'box-shadow': '0 10px 30px rgba(0, 0, 0, 0.3)',
                            'background-color': '#ffffff',
                            'padding': '24px'
                        }
                    },
                    {
                        'selector': '.modal-backdrop, .overlay',
                        'css_changes': {
                            'background-color': 'rgba(0, 0, 0, 0.7)',
                            'backdrop-filter': 'blur(2px)'
                        }
                    }
                ]
            },
            js_test_scenarios=['modal_behavior', 'focus_management', 'keyboard_navigation'],
            expected_improvements=[
                'Focus is trapped within modal',
                'Focus returns to trigger element on close',
                'Modal can be closed with Escape key',
                'Proper ARIA attributes are set'
            ],
            validation_criteria={
                'modal_accessibility_score': {'min': 95},
                'focus_trap_compliance': {'min': 100},
                'keyboard_control_rate': {'min': 100}
            },
            wcag_compliance='2.1 AA'
        )
        
        # Responsive Design Enhancement Scenario
        scenarios['responsive_enhancement'] = TestScenario(
            scenario_id='responsive_enhancement',
            name='Responsive Design Enhancement',
            description='Accessibility improvements across different viewport sizes',
            category='layout',
            priority='medium',
            css_modifications={
                'responsive_modifications': {
                    'viewports': [
                        {'width': 320, 'height': 568, 'name': 'mobile'},
                        {'width': 768, 'height': 1024, 'name': 'tablet'},
                        {'width': 1440, 'height': 900, 'name': 'desktop'}
                    ],
                    'css_changes': {
                        'font-size': 'clamp(16px, 4vw, 20px)',
                        'line-height': '1.6',
                        'padding': 'clamp(8px, 2vw, 16px)',
                        'margin': 'clamp(4px, 1vw, 8px)'
                    }
                }
            },
            js_test_scenarios=['keyboard_navigation', 'dynamic_content'],
            expected_improvements=[
                'Content reflows properly at 320px width',
                'Text remains readable at all sizes',
                'Interactive elements maintain minimum sizes',
                'Keyboard navigation works across viewports'
            ],
            validation_criteria={
                'responsive_score': {'min': 85},
                'content_reflow_compliance': {'min': 100},
                'minimum_size_compliance': {'min': 95}
            },
            wcag_compliance='2.1 AA'
        )
        
        # Motion and Animation Safety Scenario
        scenarios['motion_safety'] = TestScenario(
            scenario_id='motion_safety',
            name='Motion and Animation Safety',
            description='Ensure animations respect user preferences and accessibility needs',
            category='motion',
            priority='medium',
            css_modifications={
                'accessibility_improvements': [
                    {
                        'type': 'motion_reduction',
                        'reductions': {
                            'respect_preference': {
                                'animation': 'var(--animation, none)',
                                'transition': 'var(--transition, none)',
                                'transform': 'var(--transform, none)'
                            },
                            'reduce_motion': {
                                'animation-duration': '0.01s',
                                'transition-duration': '0.01s'
                            },
                            'disable_animations': {
                                'animation': 'none',
                                'transition': 'none'
                            }
                        }
                    }
                ]
            },
            js_test_scenarios=['loading_states', 'dynamic_content'],
            expected_improvements=[
                'Animations respect prefers-reduced-motion',
                'No infinite animations without user control',
                'Motion effects do not trigger vestibular disorders',
                'Loading animations are accessible'
            ],
            validation_criteria={
                'motion_safety_score': {'min': 90},
                'reduced_motion_compliance': {'min': 100}
            },
            wcag_compliance='2.1 AAA'
        )
        
        # Complete Accessibility Overhaul Scenario
        scenarios['complete_overhaul'] = TestScenario(
            scenario_id='complete_overhaul',
            name='Complete Accessibility Overhaul',
            description='Comprehensive accessibility improvements across all categories',
            category='comprehensive',
            priority='high',
            css_modifications={
                'element_modifications': [
                    {
                        'selector': '*',
                        'css_changes': {
                            'font-family': 'system-ui, -apple-system, sans-serif',
                            'line-height': '1.6'
                        }
                    },
                    {
                        'selector': 'button, [role="button"], a, input, select, textarea',
                        'css_changes': {
                            'min-width': '44px',
                            'min-height': '44px',
                            'outline': '2px solid #007acc',
                            'outline-offset': '2px'
                        }
                    }
                ],
                'global_modifications': {
                    'css_rules': '''
                        :root {
                            --primary-color: #003366;
                            --primary-bg: #ffffff;
                            --focus-color: #007acc;
                            --error-color: #d63031;
                            --success-color: #00b894;
                        }
                        
                        @media (prefers-reduced-motion: reduce) {
                            *, *::before, *::after {
                                animation-duration: 0.01ms !important;
                                animation-iteration-count: 1 !important;
                                transition-duration: 0.01ms !important;
                            }
                        }
                        
                        .sr-only {
                            position: absolute;
                            width: 1px;
                            height: 1px;
                            padding: 0;
                            margin: -1px;
                            overflow: hidden;
                            clip: rect(0, 0, 0, 0);
                            white-space: nowrap;
                            border: 0;
                        }
                    '''
                }
            },
            js_test_scenarios=['keyboard_navigation', 'focus_management', 'modal_behavior', 'form_interactions', 'dynamic_content'],
            expected_improvements=[
                'Complete WCAG 2.1 AA compliance',
                'All interactive elements are keyboard accessible',
                'Proper focus management throughout',
                'Accessible forms with error handling',
                'Motion safety implemented'
            ],
            validation_criteria={
                'overall_accessibility_score': {'min': 95},
                'wcag_compliance_rate': {'min': 100},
                'keyboard_accessibility_rate': {'min': 100},
                'contrast_compliance_rate': {'min': 100}
            },
            wcag_compliance='2.1 AA'
        )
        
        return scenarios
    
    def get_scenario(self, scenario_id: str) -> Optional[TestScenario]:
        """Get a specific test scenario"""
        return self.scenarios.get(scenario_id)
    
    def get_scenarios_by_category(self, category: str) -> List[TestScenario]:
        """Get scenarios by category"""
        return [scenario for scenario in self.scenarios.values() if scenario.category == category]
    
    def get_scenarios_by_priority(self, priority: str) -> List[TestScenario]:
        """Get scenarios by priority"""
        return [scenario for scenario in self.scenarios.values() if scenario.priority == priority]
    
    def run_scenario(self, scenario_id: str, page_id: str) -> Dict[str, Any]:
        """
        Run a complete testing scenario
        
        Args:
            scenario_id: ID of the scenario to run
            page_id: Page ID to test scenario on
            
        Returns:
            Comprehensive scenario test results
        """
        try:
            scenario = self.get_scenario(scenario_id)
            if not scenario:
                return {'error': f'Scenario not found: {scenario_id}'}
            
            test_session = {
                'test_id': str(uuid.uuid4()),
                'scenario_id': scenario_id,
                'page_id': page_id,
                'start_time': datetime.now(),
                'scenario_info': asdict(scenario),
                'results': {},
                'validation': {},
                'summary': {}
            }
            
            self.logger.info(f"Running scenario: {scenario.name} on page {page_id}")
            
            # Run baseline analysis
            test_session['baseline'] = self._get_baseline_analysis()
            
            # Run CSS modifications if specified
            if scenario.css_modifications:
                css_results = self.css_modifier.test_css_changes(page_id, scenario.css_modifications)
                test_session['results']['css'] = css_results
            
            # Run JavaScript dynamic tests if specified
            if scenario.js_test_scenarios:
                js_results = self.js_dynamic_tester.run_dynamic_tests(page_id, scenario.js_test_scenarios)
                test_session['results']['javascript'] = js_results
            
            # Run post-modification analysis
            test_session['post_modification'] = self._get_post_modification_analysis()
            
            # Validate against criteria
            if scenario.validation_criteria:
                test_session['validation'] = self._validate_scenario_results(
                    test_session['results'], 
                    scenario.validation_criteria
                )
            
            # Generate comprehensive summary
            test_session['summary'] = self._generate_scenario_summary(test_session)
            test_session['end_time'] = datetime.now()
            test_session['duration'] = (test_session['end_time'] - test_session['start_time']).total_seconds()
            
            # Store results if database available
            if self.db_connection:
                self._store_scenario_results(test_session)
            
            return test_session
            
        except Exception as e:
            self.logger.error(f"Error running scenario {scenario_id}: {e}")
            return {'error': str(e)}
    
    def run_multiple_scenarios(self, scenario_ids: List[str], page_id: str) -> Dict[str, Any]:
        """
        Run multiple scenarios in sequence
        
        Args:
            scenario_ids: List of scenario IDs to run
            page_id: Page ID to test scenarios on
            
        Returns:
            Combined results from all scenarios
        """
        try:
            batch_session = {
                'batch_id': str(uuid.uuid4()),
                'page_id': page_id,
                'scenario_ids': scenario_ids,
                'start_time': datetime.now(),
                'scenario_results': {},
                'batch_summary': {}
            }
            
            for scenario_id in scenario_ids:
                try:
                    scenario_result = self.run_scenario(scenario_id, page_id)
                    batch_session['scenario_results'][scenario_id] = scenario_result
                    
                    # Add delay between scenarios to allow page to reset
                    if len(scenario_ids) > 1:
                        self.driver.refresh()
                        import time
                        time.sleep(2)
                        
                except Exception as e:
                    self.logger.error(f"Error in batch scenario {scenario_id}: {e}")
                    batch_session['scenario_results'][scenario_id] = {'error': str(e)}
            
            # Generate batch summary
            batch_session['batch_summary'] = self._generate_batch_summary(batch_session['scenario_results'])
            batch_session['end_time'] = datetime.now()
            batch_session['total_duration'] = (batch_session['end_time'] - batch_session['start_time']).total_seconds()
            
            return batch_session
            
        except Exception as e:
            self.logger.error(f"Error running batch scenarios: {e}")
            return {'error': str(e)}
    
    def _get_baseline_analysis(self) -> Dict[str, Any]:
        """Get baseline accessibility analysis before modifications"""
        try:
            baseline = {
                'css_analysis': {},
                'js_analysis': {},
                'timestamp': datetime.now().isoformat()
            }
            
            # Get CSS baseline
            baseline['css_analysis'] = self.css_analyzer.get_stylesheet_rules()
            
            # Get JavaScript baseline
            baseline['js_analysis'] = self.js_analyzer.analyze_page_javascript()
            
            return baseline
            
        except Exception as e:
            self.logger.error(f"Error getting baseline analysis: {e}")
            return {'error': str(e)}
    
    def _get_post_modification_analysis(self) -> Dict[str, Any]:
        """Get analysis after modifications have been applied"""
        try:
            post_analysis = {
                'css_analysis': {},
                'js_analysis': {},
                'timestamp': datetime.now().isoformat()
            }
            
            # Get post-modification CSS analysis
            post_analysis['css_analysis'] = self.css_analyzer.get_stylesheet_rules()
            
            # Get post-modification JavaScript analysis
            post_analysis['js_analysis'] = self.js_analyzer.analyze_page_javascript()
            
            return post_analysis
            
        except Exception as e:
            self.logger.error(f"Error getting post-modification analysis: {e}")
            return {'error': str(e)}
    
    def _validate_scenario_results(self, results: Dict[str, Any], criteria: Dict[str, Any]) -> Dict[str, Any]:
        """Validate scenario results against specified criteria"""
        validation = {
            'passed': 0,
            'failed': 0,
            'criteria_results': {},
            'overall_pass': True
        }
        
        try:
            for criterion, requirements in criteria.items():
                criterion_result = {
                    'criterion': criterion,
                    'requirements': requirements,
                    'actual_value': None,
                    'passed': False,
                    'message': ''
                }
                
                # Extract actual value from results (simplified logic)
                # In a full implementation, this would have sophisticated result parsing
                if 'min' in requirements:
                    # Mock validation - in real implementation, would extract actual scores
                    mock_score = 85  # Placeholder
                    criterion_result['actual_value'] = mock_score
                    criterion_result['passed'] = mock_score >= requirements['min']
                    criterion_result['message'] = f"Score: {mock_score}, Required: {requirements['min']}"
                
                validation['criteria_results'][criterion] = criterion_result
                
                if criterion_result['passed']:
                    validation['passed'] += 1
                else:
                    validation['failed'] += 1
                    validation['overall_pass'] = False
            
            return validation
            
        except Exception as e:
            self.logger.error(f"Error validating scenario results: {e}")
            return {'error': str(e)}
    
    def _generate_scenario_summary(self, test_session: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary of scenario test results"""
        summary = {
            'scenario_name': test_session.get('scenario_info', {}).get('name', 'Unknown'),
            'category': test_session.get('scenario_info', {}).get('category', 'Unknown'),
            'priority': test_session.get('scenario_info', {}).get('priority', 'Unknown'),
            'overall_success': True,
            'css_results': {},
            'js_results': {},
            'validation_summary': {},
            'improvements_achieved': [],
            'issues_found': []
        }
        
        try:
            # Summarize CSS results
            css_results = test_session.get('results', {}).get('css', {})
            if css_results and not css_results.get('error'):
                summary['css_results'] = {
                    'status': 'completed',
                    'duration': css_results.get('duration', 0),
                    'tests_run': len(css_results.get('results', {}))
                }
            
            # Summarize JavaScript results
            js_results = test_session.get('results', {}).get('javascript', {})
            if js_results and not js_results.get('error'):
                js_summary = js_results.get('summary', {})
                summary['js_results'] = {
                    'status': 'completed',
                    'total_scenarios': js_summary.get('total_scenarios', 0),
                    'passed': js_summary.get('passed', 0),
                    'failed': js_summary.get('failed', 0)
                }
            
            # Summarize validation
            validation = test_session.get('validation', {})
            if validation:
                summary['validation_summary'] = {
                    'overall_pass': validation.get('overall_pass', False),
                    'criteria_passed': validation.get('passed', 0),
                    'criteria_failed': validation.get('failed', 0)
                }
                summary['overall_success'] = validation.get('overall_pass', False)
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Error generating scenario summary: {e}")
            return {'error': str(e)}
    
    def _generate_batch_summary(self, scenario_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary of batch scenario results"""
        batch_summary = {
            'total_scenarios': len(scenario_results),
            'successful_scenarios': 0,
            'failed_scenarios': 0,
            'scenario_summaries': {},
            'overall_success_rate': 0,
            'categories_tested': set(),
            'total_improvements': 0
        }
        
        try:
            for scenario_id, result in scenario_results.items():
                if result.get('error'):
                    batch_summary['failed_scenarios'] += 1
                else:
                    batch_summary['successful_scenarios'] += 1
                    
                    # Extract scenario summary
                    scenario_summary = result.get('summary', {})
                    batch_summary['scenario_summaries'][scenario_id] = scenario_summary
                    
                    # Track categories
                    category = scenario_summary.get('category')
                    if category:
                        batch_summary['categories_tested'].add(category)
            
            # Convert set to list for JSON serialization
            batch_summary['categories_tested'] = list(batch_summary['categories_tested'])
            
            # Calculate success rate
            if batch_summary['total_scenarios'] > 0:
                batch_summary['overall_success_rate'] = (
                    batch_summary['successful_scenarios'] / batch_summary['total_scenarios'] * 100
                )
            
            return batch_summary
            
        except Exception as e:
            self.logger.error(f"Error generating batch summary: {e}")
            return {'error': str(e)}
    
    def _store_scenario_results(self, test_session: Dict[str, Any]):
        """Store scenario test results in database"""
        try:
            if self.db_connection:
                collection = self.db_connection.db.scenario_tests
                collection.insert_one(test_session)
                self.logger.info(f"Stored scenario test results: {test_session['test_id']}")
        except Exception as e:
            self.logger.error(f"Error storing scenario results: {e}")
    
    def get_available_scenarios(self) -> List[Dict[str, Any]]:
        """Get list of all available scenarios with metadata"""
        return [
            {
                'scenario_id': scenario.scenario_id,
                'name': scenario.name,
                'description': scenario.description,
                'category': scenario.category,
                'priority': scenario.priority,
                'wcag_compliance': scenario.wcag_compliance,
                'expected_improvements': scenario.expected_improvements
            }
            for scenario in self.scenarios.values()
        ]