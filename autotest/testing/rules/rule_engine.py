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
Rule engine and configuration system for AutoTest accessibility testing
"""

import json
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from pathlib import Path
import importlib.util

from selenium import webdriver

from autotest.utils.logger import LoggerMixin
from autotest.utils.config import Config


@dataclass
class RuleDefinition:
    """Definition of an accessibility test rule"""
    rule_id: str
    name: str
    description: str
    help_text: str
    help_url: str
    impact: str  # "minor", "moderate", "serious", "critical"
    category: str  # "wcag21", "semantic", "custom"
    enabled: bool = True
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []


@dataclass
class RuleConfiguration:
    """Configuration for a specific rule"""
    rule_id: str
    enabled: bool = True
    custom_impact: Optional[str] = None
    custom_parameters: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.custom_parameters is None:
            self.custom_parameters = {}


class RuleEngine(LoggerMixin):
    """Accessibility testing rule engine with configuration support"""
    
    def __init__(self, config: Config):
        """
        Initialize rule engine
        
        Args:
            config: Application configuration
        """
        self.config = config
        self.rules: Dict[str, RuleDefinition] = {}
        self.rule_functions: Dict[str, Callable] = {}
        self.rule_configurations: Dict[str, RuleConfiguration] = {}
        self.custom_rules_enabled = config.get('testing.custom_rules_enabled', True)
        
        # Initialize built-in rules
        self._initialize_builtin_rules()
        
        # Load custom rules if enabled
        if self.custom_rules_enabled:
            self._load_custom_rules()
        
        # Load rule configurations
        self._load_rule_configurations()
    
    def _initialize_builtin_rules(self) -> None:
        """Initialize built-in accessibility rules"""
        
        # Basic accessibility rules
        basic_rules = [
            RuleDefinition(
                rule_id="page-has-title",
                name="Page has title",
                description="Ensures every HTML document has a non-empty <title> element",
                help_text="All pages must have a title to help users understand the page content",
                help_url="https://www.w3.org/WAI/WCAG21/Understanding/page-titled.html",
                impact="serious",
                category="wcag21",
                tags=["title", "navigation", "wcag21-2.4.2"]
            ),
            RuleDefinition(
                rule_id="page-has-heading",
                name="Page has heading",
                description="Ensures the page has at least one heading (h1-h6)",
                help_text="Pages should have proper heading structure for screen readers",
                help_url="https://www.w3.org/WAI/WCAG21/Understanding/info-and-relationships.html",
                impact="serious",
                category="wcag21",
                tags=["headings", "structure", "wcag21-1.3.1"]
            ),
            RuleDefinition(
                rule_id="images-have-alt",
                name="Images have alt text",
                description="Ensures all images have alternative text",
                help_text="Images must have alt attributes for screen readers",
                help_url="https://www.w3.org/WAI/WCAG21/Understanding/non-text-content.html",
                impact="critical",
                category="wcag21",
                tags=["images", "alt-text", "wcag21-1.1.1"]
            ),
            RuleDefinition(
                rule_id="links-have-names",
                name="Links have accessible names",
                description="Ensures links have discernible text",
                help_text="Links must have text content or accessible names",
                help_url="https://www.w3.org/WAI/WCAG21/Understanding/link-purpose-in-context.html",
                impact="serious",
                category="wcag21",
                tags=["links", "navigation", "wcag21-2.4.4"]
            ),
            RuleDefinition(
                rule_id="form-labels",
                name="Form inputs have labels",
                description="Ensures every form input has an associated label",
                help_text="Form controls must be properly labeled for accessibility",
                help_url="https://www.w3.org/WAI/WCAG21/Understanding/labels-or-instructions.html",
                impact="critical",
                category="wcag21",
                tags=["forms", "labels", "wcag21-3.3.2"]
            )
        ]
        
        # WCAG 2.1 advanced rules
        wcag_rules = [
            RuleDefinition(
                rule_id="color-contrast",
                name="Color contrast",
                description="Ensures text has sufficient color contrast",
                help_text="Text must have adequate contrast ratio for readability",
                help_url="https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum.html",
                impact="serious",
                category="wcag21",
                tags=["color", "contrast", "wcag21-1.4.3"]
            ),
            RuleDefinition(
                rule_id="keyboard-navigation",
                name="Keyboard navigation",
                description="Ensures all interactive elements are keyboard accessible",
                help_text="All functionality must be available via keyboard",
                help_url="https://www.w3.org/WAI/WCAG21/Understanding/keyboard.html",
                impact="critical",
                category="wcag21",
                tags=["keyboard", "navigation", "wcag21-2.1.1"]
            ),
            RuleDefinition(
                rule_id="focus-visible",
                name="Focus indicators",
                description="Ensures focusable elements have visible focus indicators",
                help_text="Interactive elements must have visible focus indicators",
                help_url="https://www.w3.org/WAI/WCAG21/Understanding/focus-visible.html",
                impact="serious",
                category="wcag21",
                tags=["focus", "keyboard", "wcag21-2.4.7"]
            ),
            RuleDefinition(
                rule_id="aria-labels",
                name="ARIA labels and roles",
                description="Ensures proper use of ARIA labels and roles",
                help_text="ARIA attributes must be used correctly for accessibility",
                help_url="https://www.w3.org/WAI/WCAG21/Understanding/name-role-value.html",
                impact="serious",
                category="wcag21",
                tags=["aria", "labels", "wcag21-4.1.2"]
            ),
            RuleDefinition(
                rule_id="landmark-regions",
                name="Landmark regions",
                description="Ensures proper landmark regions for navigation",
                help_text="Pages should have proper landmark structure",
                help_url="https://www.w3.org/WAI/WCAG21/Understanding/bypass-blocks.html",
                impact="moderate",
                category="wcag21",
                tags=["landmarks", "navigation", "wcag21-2.4.1"]
            )
        ]
        
        # HTML semantic rules
        semantic_rules = [
            RuleDefinition(
                rule_id="html-structure",
                name="HTML structure",
                description="Validates basic HTML document structure",
                help_text="HTML documents must have proper structure",
                help_url="https://html.spec.whatwg.org/multipage/semantics.html",
                impact="serious",
                category="semantic",
                tags=["html", "structure", "validation"]
            ),
            RuleDefinition(
                rule_id="semantic-elements",
                name="Semantic HTML elements",
                description="Validates proper use of HTML5 semantic elements",
                help_text="Use semantic HTML elements for better accessibility",
                help_url="https://html.spec.whatwg.org/multipage/sections.html",
                impact="moderate",
                category="semantic",
                tags=["html5", "semantic", "structure"]
            ),
            RuleDefinition(
                rule_id="heading-hierarchy",
                name="Heading hierarchy",
                description="Ensures headings are in proper hierarchical order",
                help_text="Headings should follow proper nesting order (h1, h2, h3, etc.)",
                help_url="https://www.w3.org/WAI/WCAG21/Understanding/info-and-relationships.html",
                impact="moderate",
                category="semantic",
                tags=["headings", "structure", "hierarchy"]
            ),
            RuleDefinition(
                rule_id="list-structure",
                name="List structure",
                description="Validates proper list markup and structure",
                help_text="Lists should use proper HTML list elements",
                help_url="https://html.spec.whatwg.org/multipage/semantics.html#the-ul-element",
                impact="minor",
                category="semantic",
                tags=["lists", "structure", "html"]
            ),
            RuleDefinition(
                rule_id="form-structure",
                name="Form structure",
                description="Validates proper form markup and structure",
                help_text="Forms should use proper HTML form elements and structure",
                help_url="https://html.spec.whatwg.org/multipage/forms.html",
                impact="moderate",
                category="semantic",
                tags=["forms", "structure", "html"]
            )
        ]
        
        # Add all rules to the registry
        all_rules = basic_rules + wcag_rules + semantic_rules
        for rule in all_rules:
            self.rules[rule.rule_id] = rule
    
    def _load_custom_rules(self) -> None:
        """Load custom rules from configuration directory"""
        try:
            custom_rules_dir = Path('autotest/testing/rules/custom')
            if not custom_rules_dir.exists():
                return
            
            for rule_file in custom_rules_dir.glob('*.json'):
                try:
                    with open(rule_file, 'r') as f:
                        rule_data = json.load(f)
                    
                    rule = RuleDefinition(
                        rule_id=rule_data['rule_id'],
                        name=rule_data['name'],
                        description=rule_data['description'],
                        help_text=rule_data['help_text'],
                        help_url=rule_data.get('help_url', ''),
                        impact=rule_data['impact'],
                        category='custom',
                        enabled=rule_data.get('enabled', True),
                        tags=rule_data.get('tags', [])
                    )
                    
                    self.rules[rule.rule_id] = rule
                    self.logger.info(f"Loaded custom rule: {rule.rule_id}")
                    
                except Exception as e:
                    self.logger.warning(f"Failed to load custom rule from {rule_file}: {e}")
        
        except Exception as e:
            self.logger.warning(f"Error loading custom rules: {e}")
    
    def _load_rule_configurations(self) -> None:
        """Load rule configurations from file"""
        try:
            config_file = Path('autotest/testing/rules/rule_config.json')
            if config_file.exists():
                with open(config_file, 'r') as f:
                    config_data = json.load(f)
                
                for rule_id, config in config_data.items():
                    self.rule_configurations[rule_id] = RuleConfiguration(
                        rule_id=rule_id,
                        enabled=config.get('enabled', True),
                        custom_impact=config.get('custom_impact'),
                        custom_parameters=config.get('custom_parameters', {})
                    )
                    
                self.logger.info(f"Loaded configurations for {len(self.rule_configurations)} rules")
        
        except Exception as e:
            self.logger.warning(f"Error loading rule configurations: {e}")
    
    def save_rule_configurations(self) -> bool:
        """Save current rule configurations to file"""
        try:
            config_file = Path('autotest/testing/rules/rule_config.json')
            config_file.parent.mkdir(parents=True, exist_ok=True)
            
            config_data = {}
            for rule_id, config in self.rule_configurations.items():
                config_data[rule_id] = asdict(config)
            
            with open(config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
            
            self.logger.info("Rule configurations saved successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving rule configurations: {e}")
            return False
    
    def get_enabled_rules(self, category: Optional[str] = None, 
                         tags: Optional[List[str]] = None) -> List[RuleDefinition]:
        """
        Get list of enabled rules, optionally filtered by category or tags
        
        Args:
            category: Filter by rule category
            tags: Filter by rule tags
        
        Returns:
            List of enabled rule definitions
        """
        enabled_rules = []
        
        for rule_id, rule in self.rules.items():
            # Check if rule is enabled globally
            config = self.rule_configurations.get(rule_id)
            if config and not config.enabled:
                continue
            
            if not rule.enabled:
                continue
            
            # Apply category filter
            if category and rule.category != category:
                continue
            
            # Apply tags filter
            if tags and not any(tag in rule.tags for tag in tags):
                continue
            
            enabled_rules.append(rule)
        
        return enabled_rules
    
    def get_rule_by_id(self, rule_id: str) -> Optional[RuleDefinition]:
        """
        Get rule definition by ID
        
        Args:
            rule_id: Rule identifier
        
        Returns:
            Rule definition or None if not found
        """
        return self.rules.get(rule_id)
    
    def configure_rule(self, rule_id: str, enabled: Optional[bool] = None,
                      custom_impact: Optional[str] = None,
                      custom_parameters: Optional[Dict[str, Any]] = None) -> bool:
        """
        Configure a specific rule
        
        Args:
            rule_id: Rule identifier
            enabled: Enable/disable rule
            custom_impact: Override rule impact level
            custom_parameters: Custom parameters for rule
        
        Returns:
            True if configuration successful, False otherwise
        """
        try:
            if rule_id not in self.rules:
                self.logger.error(f"Rule not found: {rule_id}")
                return False
            
            config = self.rule_configurations.get(rule_id, RuleConfiguration(rule_id))
            
            if enabled is not None:
                config.enabled = enabled
            
            if custom_impact is not None:
                valid_impacts = ["minor", "moderate", "serious", "critical"]
                if custom_impact in valid_impacts:
                    config.custom_impact = custom_impact
                else:
                    self.logger.error(f"Invalid impact level: {custom_impact}")
                    return False
            
            if custom_parameters is not None:
                config.custom_parameters.update(custom_parameters)
            
            self.rule_configurations[rule_id] = config
            return True
            
        except Exception as e:
            self.logger.error(f"Error configuring rule {rule_id}: {e}")
            return False
    
    def get_rule_impact(self, rule_id: str) -> str:
        """
        Get the effective impact level for a rule (considering overrides)
        
        Args:
            rule_id: Rule identifier
        
        Returns:
            Impact level string
        """
        rule = self.rules.get(rule_id)
        if not rule:
            return "moderate"
        
        config = self.rule_configurations.get(rule_id)
        if config and config.custom_impact:
            return config.custom_impact
        
        return rule.impact
    
    def get_rule_parameters(self, rule_id: str) -> Dict[str, Any]:
        """
        Get custom parameters for a rule
        
        Args:
            rule_id: Rule identifier
        
        Returns:
            Dictionary of custom parameters
        """
        config = self.rule_configurations.get(rule_id)
        if config:
            return config.custom_parameters
        return {}
    
    def create_custom_rule(self, rule_definition: Dict[str, Any]) -> bool:
        """
        Create a new custom rule
        
        Args:
            rule_definition: Dictionary containing rule definition
        
        Returns:
            True if rule created successfully, False otherwise
        """
        try:
            required_fields = ['rule_id', 'name', 'description', 'help_text', 'impact']
            for field in required_fields:
                if field not in rule_definition:
                    self.logger.error(f"Missing required field: {field}")
                    return False
            
            rule_id = rule_definition['rule_id']
            if rule_id in self.rules:
                self.logger.error(f"Rule already exists: {rule_id}")
                return False
            
            rule = RuleDefinition(
                rule_id=rule_id,
                name=rule_definition['name'],
                description=rule_definition['description'],
                help_text=rule_definition['help_text'],
                help_url=rule_definition.get('help_url', ''),
                impact=rule_definition['impact'],
                category='custom',
                enabled=rule_definition.get('enabled', True),
                tags=rule_definition.get('tags', [])
            )
            
            self.rules[rule_id] = rule
            
            # Save to custom rules directory
            custom_rules_dir = Path('autotest/testing/rules/custom')
            custom_rules_dir.mkdir(parents=True, exist_ok=True)
            
            rule_file = custom_rules_dir / f"{rule_id}.json"
            with open(rule_file, 'w') as f:
                json.dump(asdict(rule), f, indent=2)
            
            self.logger.info(f"Created custom rule: {rule_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error creating custom rule: {e}")
            return False
    
    def delete_custom_rule(self, rule_id: str) -> bool:
        """
        Delete a custom rule
        
        Args:
            rule_id: Rule identifier
        
        Returns:
            True if rule deleted successfully, False otherwise
        """
        try:
            rule = self.rules.get(rule_id)
            if not rule or rule.category != 'custom':
                self.logger.error(f"Custom rule not found: {rule_id}")
                return False
            
            # Remove from memory
            del self.rules[rule_id]
            
            # Remove configuration if exists
            if rule_id in self.rule_configurations:
                del self.rule_configurations[rule_id]
            
            # Remove file
            rule_file = Path(f'autotest/testing/rules/custom/{rule_id}.json')
            if rule_file.exists():
                rule_file.unlink()
            
            self.logger.info(f"Deleted custom rule: {rule_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error deleting custom rule: {e}")
            return False
    
    def get_rules_by_impact(self, impact: str) -> List[RuleDefinition]:
        """
        Get rules filtered by impact level
        
        Args:
            impact: Impact level to filter by
        
        Returns:
            List of rules with specified impact level
        """
        return [rule for rule in self.rules.values() 
                if self.get_rule_impact(rule.rule_id) == impact]
    
    def get_rules_summary(self) -> Dict[str, Any]:
        """
        Get summary of all rules
        
        Returns:
            Dictionary with rules summary
        """
        enabled_rules = self.get_enabled_rules()
        
        summary = {
            'total_rules': len(self.rules),
            'enabled_rules': len(enabled_rules),
            'disabled_rules': len(self.rules) - len(enabled_rules),
            'by_category': {},
            'by_impact': {}
        }
        
        # Count by category
        for rule in self.rules.values():
            category = rule.category
            if category not in summary['by_category']:
                summary['by_category'][category] = {'total': 0, 'enabled': 0}
            summary['by_category'][category]['total'] += 1
            
            if rule in enabled_rules:
                summary['by_category'][category]['enabled'] += 1
        
        # Count by impact
        for rule in enabled_rules:
            impact = self.get_rule_impact(rule.rule_id)
            summary['by_impact'][impact] = summary['by_impact'].get(impact, 0) + 1
        
        return summary