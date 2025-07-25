"""
Modification Scenarios for AutoTest
Provides specific modification patterns and templates for accessibility testing.
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class ModificationTemplate:
    """
    Template for common accessibility modifications
    """
    template_id: str
    name: str
    description: str
    category: str
    css_modifications: Optional[Dict[str, Any]] = None
    js_scenarios: Optional[List[str]] = None
    use_cases: Optional[List[str]] = None


class ModificationScenarios:
    """
    Predefined modification scenarios for common accessibility improvements
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.templates = self._initialize_templates()
    
    def _initialize_templates(self) -> Dict[str, ModificationTemplate]:
        """Initialize modification templates"""
        templates = {}
        
        # Focus Enhancement Templates
        templates['focus_ring_enhancement'] = ModificationTemplate(
            template_id='focus_ring_enhancement',
            name='Focus Ring Enhancement',
            description='Improve focus indicators for keyboard navigation',
            category='focus',
            css_modifications={
                'element_modifications': [
                    {
                        'selector': 'a, button, input, select, textarea, [tabindex]:not([tabindex="-1"])',
                        'css_changes': {
                            'outline': '2px solid #4A90E2',
                            'outline-offset': '2px',
                            'border-radius': '4px'
                        }
                    },
                    {
                        'selector': ':focus-visible',
                        'css_changes': {
                            'outline': '3px solid #4A90E2',
                            'outline-offset': '2px',
                            'box-shadow': '0 0 0 5px rgba(74, 144, 226, 0.3)'
                        }
                    }
                ]
            },
            js_scenarios=['keyboard_navigation', 'focus_management'],
            use_cases=[
                'Improving keyboard navigation visibility',
                'Meeting WCAG focus indicator requirements',
                'Enhancing user experience for keyboard users'
            ]
        )
        
        templates['high_contrast_focus'] = ModificationTemplate(
            template_id='high_contrast_focus',
            name='High Contrast Focus Indicators',
            description='High contrast focus indicators for better visibility',
            category='focus',
            css_modifications={
                'element_modifications': [
                    {
                        'selector': ':focus',
                        'css_changes': {
                            'outline': '4px solid #FFFF00',
                            'outline-offset': '2px',
                            'background-color': '#000000',
                            'color': '#FFFFFF'
                        }
                    }
                ]
            },
            use_cases=[
                'Users with low vision',
                'High contrast mode compatibility',
                'Extreme visibility requirements'
            ]
        )
        
        # Color Contrast Templates
        templates['wcag_aa_contrast'] = ModificationTemplate(
            template_id='wcag_aa_contrast',
            name='WCAG AA Contrast Compliance',
            description='Ensure all text meets WCAG AA contrast requirements',
            category='contrast',
            css_modifications={
                'element_modifications': [
                    {
                        'selector': 'body, p, div, span, li, td, th',
                        'css_changes': {
                            'color': '#212529',
                            'background-color': '#ffffff'
                        }
                    },
                    {
                        'selector': 'button, .btn',
                        'css_changes': {
                            'color': '#ffffff',
                            'background-color': '#0056b3',
                            'border': '2px solid #004085'
                        }
                    },
                    {
                        'selector': 'a, .link',
                        'css_changes': {
                            'color': '#0056b3',
                            'text-decoration': 'underline'
                        }
                    }
                ]
            },
            use_cases=[
                'WCAG 2.1 AA compliance',
                'General accessibility improvements',
                'Color blindness accommodation'
            ]
        )
        
        templates['dark_mode_contrast'] = ModificationTemplate(
            template_id='dark_mode_contrast',
            name='Dark Mode High Contrast',
            description='High contrast dark mode implementation',
            category='contrast',
            css_modifications={
                'global_modifications': {
                    'css_rules': '''
                        :root {
                            --bg-primary: #121212;
                            --bg-secondary: #1e1e1e;
                            --text-primary: #ffffff;
                            --text-secondary: #b3b3b3;
                            --accent-color: #66b3ff;
                            --border-color: #404040;
                        }
                        
                        body {
                            background-color: var(--bg-primary);
                            color: var(--text-primary);
                        }
                        
                        button, .btn {
                            background-color: var(--accent-color);
                            color: #000000;
                            border: 2px solid var(--accent-color);
                        }
                        
                        input, select, textarea {
                            background-color: var(--bg-secondary);
                            color: var(--text-primary);
                            border: 2px solid var(--border-color);
                        }
                    '''
                }
            },
            use_cases=[
                'Dark mode accessibility',
                'Reduced eye strain',
                'High contrast requirements'
            ]
        )
        
        # Touch Target Templates
        templates['minimum_touch_targets'] = ModificationTemplate(
            template_id='minimum_touch_targets',
            name='Minimum Touch Target Sizes',
            description='Ensure all interactive elements meet minimum touch target requirements',
            category='touch',
            css_modifications={
                'element_modifications': [
                    {
                        'selector': 'button, a, input[type="button"], input[type="submit"], [role="button"]',
                        'css_changes': {
                            'min-width': '44px',
                            'min-height': '44px',
                            'padding': '12px 16px',
                            'display': 'inline-flex',
                            'align-items': 'center',
                            'justify-content': 'center'
                        }
                    },
                    {
                        'selector': 'input[type="checkbox"], input[type="radio"]',
                        'css_changes': {
                            'width': '20px',
                            'height': '20px',
                            'margin': '12px'
                        }
                    }
                ]
            },
            js_scenarios=['keyboard_navigation'],
            use_cases=[
                'Mobile accessibility',
                'WCAG AAA compliance',
                'Motor impairment accommodation',
                'Touch screen optimization'
            ]
        )
        
        templates['enhanced_touch_targets'] = ModificationTemplate(
            template_id='enhanced_touch_targets',
            name='Enhanced Touch Targets',
            description='Larger touch targets for better accessibility',
            category='touch',
            css_modifications={
                'element_modifications': [
                    {
                        'selector': 'button, a, [role="button"]',
                        'css_changes': {
                            'min-width': '48px',
                            'min-height': '48px',
                            'padding': '16px 20px',
                            'margin': '4px'
                        }
                    }
                ]
            },
            use_cases=[
                'Enhanced mobile experience',
                'Elderly users',
                'Motor disability accommodation'
            ]
        )
        
        # Typography Templates
        templates['readable_typography'] = ModificationTemplate(
            template_id='readable_typography',
            name='Readable Typography',
            description='Optimize typography for maximum readability',
            category='typography',
            css_modifications={
                'element_modifications': [
                    {
                        'selector': 'body, p, div, span, li',
                        'css_changes': {
                            'font-family': 'system-ui, -apple-system, "Segoe UI", sans-serif',
                            'font-size': '18px',
                            'line-height': '1.6',
                            'letter-spacing': '0.02em'
                        }
                    },
                    {
                        'selector': 'h1, h2, h3, h4, h5, h6',
                        'css_changes': {
                            'font-family': 'system-ui, -apple-system, "Segoe UI", sans-serif',
                            'line-height': '1.4',
                            'margin-bottom': '0.8em'
                        }
                    }
                ]
            },
            use_cases=[
                'Dyslexia accommodation',
                'Low vision support',
                'General readability improvement',
                'Cognitive accessibility'
            ]
        )
        
        templates['dyslexia_friendly'] = ModificationTemplate(
            template_id='dyslexia_friendly',
            name='Dyslexia-Friendly Typography',
            description='Typography optimized for users with dyslexia',
            category='typography',
            css_modifications={
                'element_modifications': [
                    {
                        'selector': 'body, p, div, span, li',
                        'css_changes': {
                            'font-family': '"OpenDyslexic", "Comic Sans MS", sans-serif',
                            'font-size': '16px',
                            'line-height': '1.8',
                            'letter-spacing': '0.08em',
                            'word-spacing': '0.16em'
                        }
                    }
                ]
            },
            use_cases=[
                'Dyslexia support',
                'Reading difficulties',
                'Cognitive accessibility'
            ]
        )
        
        # Form Enhancement Templates
        templates['accessible_forms'] = ModificationTemplate(
            template_id='accessible_forms',
            name='Accessible Form Design',
            description='Comprehensive form accessibility improvements',
            category='forms',
            css_modifications={
                'element_modifications': [
                    {
                        'selector': 'input, select, textarea',
                        'css_changes': {
                            'border': '2px solid #6c757d',
                            'border-radius': '4px',
                            'padding': '12px 16px',
                            'font-size': '16px',
                            'line-height': '1.5',
                            'background-color': '#ffffff'
                        }
                    },
                    {
                        'selector': 'input:focus, select:focus, textarea:focus',
                        'css_changes': {
                            'border-color': '#4A90E2',
                            'outline': '2px solid #4A90E2',
                            'outline-offset': '2px',
                            'box-shadow': '0 0 0 4px rgba(74, 144, 226, 0.25)'
                        }
                    },
                    {
                        'selector': 'label',
                        'css_changes': {
                            'display': 'block',
                            'font-weight': '600',
                            'margin-bottom': '8px',
                            'color': '#212529'
                        }
                    },
                    {
                        'selector': '.error, [aria-invalid="true"]',
                        'css_changes': {
                            'border-color': '#dc3545',
                            'background-color': '#fff5f5'
                        }
                    },
                    {
                        'selector': '.error-message',
                        'css_changes': {
                            'color': '#dc3545',
                            'font-size': '14px',
                            'margin-top': '4px',
                            'display': 'block'
                        }
                    }
                ]
            },
            js_scenarios=['form_interactions', 'error_handling'],
            use_cases=[
                'Form accessibility compliance',
                'Error message accessibility',
                'Screen reader compatibility',
                'Keyboard navigation in forms'
            ]
        )
        
        # Motion and Animation Templates
        templates['reduced_motion'] = ModificationTemplate(
            template_id='reduced_motion',
            name='Reduced Motion Implementation',
            description='Respect user preferences for reduced motion',
            category='motion',
            css_modifications={
                'global_modifications': {
                    'css_rules': '''
                        @media (prefers-reduced-motion: reduce) {
                            *, *::before, *::after {
                                animation-duration: 0.01ms !important;
                                animation-iteration-count: 1 !important;
                                transition-duration: 0.01ms !important;
                                scroll-behavior: auto !important;
                            }
                        }
                        
                        .animation-safe {
                            animation: var(--safe-animation, none);
                            transition: var(--safe-transition, none);
                        }
                    '''
                }
            },
            use_cases=[
                'Vestibular disorder accommodation',
                'Motion sensitivity',
                'WCAG AAA compliance',
                'User preference respect'
            ]
        )
        
        # Layout and Responsive Templates
        templates['responsive_accessibility'] = ModificationTemplate(
            template_id='responsive_accessibility',
            name='Responsive Accessibility',
            description='Ensure accessibility across all device sizes',
            category='responsive',
            css_modifications={
                'responsive_modifications': {
                    'viewports': [
                        {'width': 320, 'height': 568, 'name': 'mobile'},
                        {'width': 768, 'height': 1024, 'name': 'tablet'},
                        {'width': 1440, 'height': 900, 'name': 'desktop'}
                    ],
                    'css_changes': {
                        'font-size': 'clamp(16px, 4vw, 20px)',
                        'line-height': 'clamp(1.4, 1.6, 1.8)',
                        'padding': 'clamp(8px, 2vw, 24px)',
                        'margin': 'clamp(4px, 1vw, 16px)',
                        'min-width': '320px',
                        'max-width': '100%'
                    }
                }
            },
            js_scenarios=['keyboard_navigation'],
            use_cases=[
                'Mobile accessibility',
                'Content reflow compliance',
                'Cross-device consistency',
                'Responsive design accessibility'
            ]
        )
        
        return templates
    
    def get_template(self, template_id: str) -> Optional[ModificationTemplate]:
        """Get a specific modification template"""
        return self.templates.get(template_id)
    
    def get_templates_by_category(self, category: str) -> List[ModificationTemplate]:
        """Get templates by category"""
        return [template for template in self.templates.values() if template.category == category]
    
    def get_all_templates(self) -> List[ModificationTemplate]:
        """Get all available templates"""
        return list(self.templates.values())
    
    def create_custom_scenario(self, name: str, description: str, 
                             css_modifications: Dict[str, Any] = None,
                             js_scenarios: List[str] = None) -> Dict[str, Any]:
        """
        Create a custom modification scenario
        
        Args:
            name: Name of the custom scenario
            description: Description of what the scenario tests
            css_modifications: CSS modifications to apply
            js_scenarios: JavaScript test scenarios to run
            
        Returns:
            Custom scenario configuration
        """
        return {
            'scenario_id': f"custom_{name.lower().replace(' ', '_')}",
            'name': name,
            'description': description,
            'category': 'custom',
            'priority': 'medium',
            'css_modifications': css_modifications or {},
            'js_test_scenarios': js_scenarios or [],
            'expected_improvements': ['Custom accessibility improvements'],
            'validation_criteria': {
                'custom_scenario_success': {'min': 80}
            },
            'wcag_compliance': '2.1 AA'
        }
    
    def combine_templates(self, template_ids: List[str]) -> Dict[str, Any]:
        """
        Combine multiple templates into a single scenario
        
        Args:
            template_ids: List of template IDs to combine
            
        Returns:
            Combined scenario configuration
        """
        combined_scenario = {
            'scenario_id': f"combined_{'_'.join(template_ids)}",
            'name': f"Combined: {', '.join(template_ids)}",
            'description': 'Combined accessibility improvements from multiple templates',
            'category': 'combined',
            'priority': 'high',
            'css_modifications': {
                'element_modifications': [],
                'global_modifications': {'css_rules': ''}
            },
            'js_test_scenarios': [],
            'expected_improvements': [],
            'use_cases': []
        }
        
        # Combine modifications from all templates
        for template_id in template_ids:
            template = self.get_template(template_id)
            if template:
                # Combine CSS modifications
                if template.css_modifications:
                    if 'element_modifications' in template.css_modifications:
                        combined_scenario['css_modifications']['element_modifications'].extend(
                            template.css_modifications['element_modifications']
                        )
                    
                    if 'global_modifications' in template.css_modifications:
                        combined_scenario['css_modifications']['global_modifications']['css_rules'] += \
                            template.css_modifications['global_modifications'].get('css_rules', '')
                
                # Combine JS scenarios
                if template.js_scenarios:
                    combined_scenario['js_test_scenarios'].extend(template.js_scenarios)
                
                # Combine use cases
                if template.use_cases:
                    combined_scenario['use_cases'].extend(template.use_cases)
        
        # Remove duplicates
        combined_scenario['js_test_scenarios'] = list(set(combined_scenario['js_test_scenarios']))
        combined_scenario['use_cases'] = list(set(combined_scenario['use_cases']))
        
        return combined_scenario
    
    def get_recommended_templates(self, accessibility_issues: List[str]) -> List[str]:
        """
        Get recommended templates based on detected accessibility issues
        
        Args:
            accessibility_issues: List of accessibility issues detected
            
        Returns:
            List of recommended template IDs
        """
        recommendations = []
        
        issue_mappings = {
            'focus': ['focus_ring_enhancement', 'high_contrast_focus'],
            'contrast': ['wcag_aa_contrast', 'dark_mode_contrast'],
            'touch': ['minimum_touch_targets', 'enhanced_touch_targets'],
            'typography': ['readable_typography', 'dyslexia_friendly'],
            'forms': ['accessible_forms'],
            'motion': ['reduced_motion'],
            'responsive': ['responsive_accessibility']
        }
        
        for issue in accessibility_issues:
            issue_lower = issue.lower()
            for category, templates in issue_mappings.items():
                if category in issue_lower:
                    recommendations.extend(templates)
        
        # Remove duplicates and return
        return list(set(recommendations))
    
    def get_template_metadata(self) -> Dict[str, Any]:
        """Get metadata about all available templates"""
        metadata = {
            'total_templates': len(self.templates),
            'categories': {},
            'template_list': []
        }
        
        # Count templates by category
        for template in self.templates.values():
            category = template.category
            if category not in metadata['categories']:
                metadata['categories'][category] = 0
            metadata['categories'][category] += 1
            
            # Add template info
            metadata['template_list'].append({
                'template_id': template.template_id,
                'name': template.name,
                'description': template.description,
                'category': template.category,
                'use_cases': template.use_cases or []
            })
        
        return metadata