"""
Severity level management and reporting for AutoTest accessibility testing
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import datetime

from autotest.models.test_result import AccessibilityViolation, TestResult
from autotest.utils.logger import LoggerMixin


class SeverityLevel(Enum):
    """Enumeration of accessibility violation severity levels"""
    MINOR = "minor"
    MODERATE = "moderate" 
    SERIOUS = "serious"
    CRITICAL = "critical"
    
    @classmethod
    def get_priority_order(cls) -> List[str]:
        """Get severity levels in priority order (highest to lowest)"""
        return [cls.CRITICAL.value, cls.SERIOUS.value, cls.MODERATE.value, cls.MINOR.value]
    
    @classmethod
    def get_numeric_value(cls, severity: str) -> int:
        """Get numeric value for severity level (higher = more severe)"""
        severity_values = {
            cls.CRITICAL.value: 4,
            cls.SERIOUS.value: 3,
            cls.MODERATE.value: 2,
            cls.MINOR.value: 1
        }
        return severity_values.get(severity, 1)


@dataclass
class SeverityStats:
    """Statistics for a specific severity level"""
    level: str
    count: int
    percentage: float
    examples: List[Dict[str, Any]]


@dataclass 
class SeverityReport:
    """Comprehensive severity report"""
    total_violations: int
    severity_stats: List[SeverityStats]
    severity_score: float
    priority_violations: List[AccessibilityViolation]
    recommendations: List[str]
    trend_data: Optional[Dict[str, Any]] = None


class SeverityManager(LoggerMixin):
    """Manager for handling accessibility violation severity levels"""
    
    def __init__(self):
        """Initialize severity manager"""
        self.severity_thresholds = {
            'critical': {'max_allowed': 0, 'weight': 10.0},
            'serious': {'max_allowed': 2, 'weight': 5.0},
            'moderate': {'max_allowed': 10, 'weight': 2.0},
            'minor': {'max_allowed': 25, 'weight': 1.0}
        }
        
        self.wcag_mappings = {
            'critical': [
                'Images without alt text prevent screen reader access',
                'Form inputs without labels are unusable',
                'Keyboard inaccessible content blocks users'
            ],
            'serious': [
                'Insufficient color contrast affects readability',
                'Missing page titles confuse navigation',
                'Improper heading structure disrupts flow'
            ],
            'moderate': [
                'Missing landmarks make navigation harder',
                'Semantic HTML issues affect assistive technology',
                'Focus indicators help keyboard users'
            ],
            'minor': [
                'HTML validation improves compatibility',
                'Better semantic structure aids understanding',
                'Consistent markup patterns help maintainability'
            ]
        }
    
    def analyze_violations(self, violations: List[AccessibilityViolation]) -> SeverityReport:
        """
        Analyze violations and create comprehensive severity report
        
        Args:
            violations: List of accessibility violations
        
        Returns:
            Detailed severity report
        """
        try:
            if not violations:
                return SeverityReport(
                    total_violations=0,
                    severity_stats=[],
                    severity_score=0.0,
                    priority_violations=[],
                    recommendations=["No accessibility violations found! Great job!"]
                )
            
            # Count violations by severity
            severity_counts = {}
            for violation in violations:
                severity = violation.impact
                severity_counts[severity] = severity_counts.get(severity, 0) + 1
            
            # Create severity statistics
            severity_stats = []
            total_violations = len(violations)
            
            for severity_level in SeverityLevel.get_priority_order():
                count = severity_counts.get(severity_level, 0)
                percentage = (count / total_violations) * 100 if total_violations > 0 else 0.0
                
                # Get examples of this severity level
                examples = []
                severity_violations = [v for v in violations if v.impact == severity_level]
                for violation in severity_violations[:3]:  # Max 3 examples
                    examples.append({
                        'rule_id': violation.violation_id,
                        'description': violation.description,
                        'help': violation.help,
                        'node_count': len(violation.nodes)
                    })
                
                severity_stats.append(SeverityStats(
                    level=severity_level,
                    count=count,
                    percentage=round(percentage, 1),
                    examples=examples
                ))
            
            # Calculate severity score
            severity_score = self._calculate_severity_score(violations)
            
            # Get priority violations (critical and serious)
            priority_violations = [
                v for v in violations 
                if v.impact in ['critical', 'serious']
            ]
            
            # Generate recommendations
            recommendations = self._generate_recommendations(severity_counts, severity_score)
            
            return SeverityReport(
                total_violations=total_violations,
                severity_stats=severity_stats,
                severity_score=severity_score,
                priority_violations=priority_violations,
                recommendations=recommendations
            )
            
        except Exception as e:
            self.logger.error(f"Error analyzing violations: {e}")
            return SeverityReport(
                total_violations=len(violations),
                severity_stats=[],
                severity_score=0.0,
                priority_violations=[],
                recommendations=["Error analyzing violations"]
            )
    
    def _calculate_severity_score(self, violations: List[AccessibilityViolation]) -> float:
        """
        Calculate overall severity score (0-100, higher = more severe)
        
        Args:
            violations: List of accessibility violations
        
        Returns:
            Severity score as float
        """
        if not violations:
            return 0.0
        
        total_weighted_score = 0.0
        max_possible_score = 0.0
        
        severity_counts = {}
        for violation in violations:
            severity = violation.impact
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        for severity, count in severity_counts.items():
            weight = self.severity_thresholds.get(severity, {}).get('weight', 1.0)
            max_allowed = self.severity_thresholds.get(severity, {}).get('max_allowed', 0)
            
            # Score increases exponentially for violations above threshold
            excess_violations = max(0, count - max_allowed)
            severity_score = (excess_violations * weight) + (min(count, max_allowed) * weight * 0.5)
            
            total_weighted_score += severity_score
            max_possible_score += weight * 10  # Arbitrary max scale
        
        # Normalize to 0-100 scale
        if max_possible_score > 0:
            score = min(100.0, (total_weighted_score / max_possible_score) * 100)
        else:
            score = 0.0
        
        return round(score, 1)
    
    def _generate_recommendations(self, severity_counts: Dict[str, int], 
                                severity_score: float) -> List[str]:
        """
        Generate prioritized recommendations based on violations
        
        Args:
            severity_counts: Count of violations by severity
            severity_score: Overall severity score
        
        Returns:
            List of prioritized recommendations
        """
        recommendations = []
        
        # Critical violations - immediate action required
        if severity_counts.get('critical', 0) > 0:
            recommendations.append(
                f"🚨 URGENT: Fix {severity_counts['critical']} critical accessibility issues immediately. "
                "These prevent users from accessing content."
            )
        
        # Serious violations - high priority
        if severity_counts.get('serious', 0) > 0:
            count = severity_counts['serious']
            threshold = self.severity_thresholds['serious']['max_allowed']
            if count > threshold:
                recommendations.append(
                    f"⚠️ HIGH PRIORITY: Address {count} serious accessibility issues. "
                    f"Target: Reduce to {threshold} or fewer."
                )
            else:
                recommendations.append(
                    f"⚠️ Address {count} serious accessibility issues for better compliance."
                )
        
        # Moderate violations
        if severity_counts.get('moderate', 0) > 0:
            count = severity_counts['moderate']
            threshold = self.severity_thresholds['moderate']['max_allowed']
            if count > threshold:
                recommendations.append(
                    f"📋 MODERATE: Fix {count} moderate issues. "
                    f"Target: Reduce to {threshold} or fewer for good accessibility."
                )
        
        # Minor violations
        if severity_counts.get('minor', 0) > 0:
            count = severity_counts['minor']
            recommendations.append(
                f"✨ ENHANCEMENT: Address {count} minor issues to improve overall quality."
            )
        
        # Overall score recommendations
        if severity_score >= 80:
            recommendations.append(
                "🔥 CRITICAL SITE: Immediate accessibility review and remediation required."
            )
        elif severity_score >= 50:
            recommendations.append(
                "⚠️ HIGH RISK: Significant accessibility barriers present. Plan remediation sprint."
            )
        elif severity_score >= 25:
            recommendations.append(
                "📈 IMPROVING: Good progress, but continue addressing remaining issues."
            )
        elif severity_score > 0:
            recommendations.append(
                "✅ GOOD: Minor issues remain. Polish for excellent accessibility."
            )
        else:
            recommendations.append(
                "🎉 EXCELLENT: No accessibility violations detected!"
            )
        
        # Add specific guidance based on violation patterns
        if severity_counts.get('critical', 0) > 0 or severity_counts.get('serious', 0) > 0:
            recommendations.append(
                "💡 TIP: Focus on critical and serious issues first - they have the biggest impact on users."
            )
        
        return recommendations
    
    def get_severity_trend(self, test_results: List[TestResult], 
                          days: int = 30) -> Dict[str, Any]:
        """
        Analyze severity trends over time
        
        Args:
            test_results: List of test results over time
            days: Number of days to analyze
        
        Returns:
            Dictionary with trend analysis
        """
        try:
            if not test_results:
                return {'trend': 'no_data', 'message': 'No test results available'}
            
            # Sort results by date
            sorted_results = sorted(test_results, key=lambda x: x.test_date or datetime.datetime.min)
            
            # Calculate severity scores over time
            score_history = []
            severity_history = []
            
            for result in sorted_results[-days:]:  # Last N days
                violations = result.violations
                score = self._calculate_severity_score(violations)
                
                severity_counts = {}
                for violation in violations:
                    severity_counts[violation.impact] = severity_counts.get(violation.impact, 0) + 1
                
                score_history.append({
                    'date': result.test_date,
                    'score': score,
                    'total_violations': len(violations)
                })
                
                severity_history.append({
                    'date': result.test_date,
                    'counts': severity_counts
                })
            
            if len(score_history) < 2:
                return {'trend': 'insufficient_data', 'message': 'Need more test results for trend analysis'}
            
            # Calculate trend
            first_score = score_history[0]['score']
            last_score = score_history[-1]['score']
            score_change = last_score - first_score
            
            if score_change <= -10:
                trend = 'improving_significantly'
                message = f"Excellent progress! Severity score decreased by {abs(score_change):.1f} points."
            elif score_change <= -2:
                trend = 'improving'
                message = f"Good progress! Severity score decreased by {abs(score_change):.1f} points."
            elif score_change <= 2:
                trend = 'stable'
                message = f"Severity score is stable (change: {score_change:+.1f} points)."
            elif score_change <= 10:
                trend = 'degrading'
                message = f"Accessibility is declining. Severity score increased by {score_change:.1f} points."
            else:
                trend = 'degrading_significantly'
                message = f"Significant regression! Severity score increased by {score_change:.1f} points."
            
            return {
                'trend': trend,
                'message': message,
                'score_change': score_change,
                'first_score': first_score,
                'last_score': last_score,
                'history': score_history,
                'severity_history': severity_history
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating severity trend: {e}")
            return {'trend': 'error', 'message': f'Error analyzing trend: {str(e)}'}
    
    def prioritize_violations(self, violations: List[AccessibilityViolation]) -> List[AccessibilityViolation]:
        """
        Sort violations by priority (severity and frequency)
        
        Args:
            violations: List of accessibility violations
        
        Returns:
            List of violations sorted by priority
        """
        try:
            # Group violations by rule ID to count frequency
            violation_groups = {}
            for violation in violations:
                rule_id = violation.violation_id
                if rule_id not in violation_groups:
                    violation_groups[rule_id] = []
                violation_groups[rule_id].append(violation)
            
            # Create priority scores and sort
            prioritized = []
            
            for rule_id, rule_violations in violation_groups.items():
                # Use first violation as representative
                representative = rule_violations[0]
                
                # Calculate priority score
                severity_score = SeverityLevel.get_numeric_value(representative.impact)
                frequency_score = len(rule_violations)
                node_count = sum(len(v.nodes) for v in rule_violations)
                
                priority_score = (severity_score * 10) + (frequency_score * 2) + (node_count * 0.1)
                
                # Add all violations for this rule with their priority score
                for violation in rule_violations:
                    violation._priority_score = priority_score
                    prioritized.append(violation)
            
            # Sort by priority score (highest first)
            prioritized.sort(key=lambda v: v._priority_score, reverse=True)
            
            # Clean up temporary attribute
            for violation in prioritized:
                if hasattr(violation, '_priority_score'):
                    delattr(violation, '_priority_score')
            
            return prioritized
            
        except Exception as e:
            self.logger.error(f"Error prioritizing violations: {e}")
            return violations
    
    def get_severity_distribution(self, violations: List[AccessibilityViolation]) -> Dict[str, Any]:
        """
        Get detailed distribution of violations by severity
        
        Args:
            violations: List of accessibility violations
        
        Returns:
            Dictionary with severity distribution data
        """
        try:
            if not violations:
                return {
                    'total': 0,
                    'distribution': {},
                    'percentages': {},
                    'severity_breakdown': []
                }
            
            # Count by severity
            severity_counts = {}
            for violation in violations:
                severity = violation.impact
                severity_counts[severity] = severity_counts.get(severity, 0) + 1
            
            total = len(violations)
            
            # Calculate percentages
            percentages = {}
            for severity, count in severity_counts.items():
                percentages[severity] = round((count / total) * 100, 1)
            
            # Create detailed breakdown
            breakdown = []
            for severity_level in SeverityLevel.get_priority_order():
                count = severity_counts.get(severity_level, 0)
                percentage = percentages.get(severity_level, 0.0)
                
                breakdown.append({
                    'severity': severity_level,
                    'count': count,
                    'percentage': percentage,
                    'description': self._get_severity_description(severity_level),
                    'examples': self.wcag_mappings.get(severity_level, [])[:2]
                })
            
            return {
                'total': total,
                'distribution': severity_counts,
                'percentages': percentages,
                'severity_breakdown': breakdown
            }
            
        except Exception as e:
            self.logger.error(f"Error getting severity distribution: {e}")
            return {'total': 0, 'distribution': {}, 'percentages': {}, 'severity_breakdown': []}
    
    def _get_severity_description(self, severity: str) -> str:
        """Get human-readable description for severity level"""
        descriptions = {
            'critical': 'Blocks access to content or functionality',
            'serious': 'Makes content difficult or impossible to use',
            'moderate': 'Causes inconvenience or confusion for users', 
            'minor': 'Minor usability or compliance issues'
        }
        return descriptions.get(severity, 'Unknown severity level')
    
    def export_severity_report(self, severity_report: SeverityReport, 
                             format: str = 'json') -> Dict[str, Any]:
        """
        Export severity report in specified format
        
        Args:
            severity_report: Severity report to export
            format: Export format ('json', 'summary')
        
        Returns:
            Formatted report data
        """
        try:
            if format == 'summary':
                return {
                    'summary': {
                        'total_violations': severity_report.total_violations,
                        'severity_score': severity_report.severity_score,
                        'critical_count': next((s.count for s in severity_report.severity_stats if s.level == 'critical'), 0),
                        'serious_count': next((s.count for s in severity_report.severity_stats if s.level == 'serious'), 0),
                        'top_recommendation': severity_report.recommendations[0] if severity_report.recommendations else 'No recommendations'
                    }
                }
            else:  # Default JSON format
                return {
                    'total_violations': severity_report.total_violations,
                    'severity_score': severity_report.severity_score,
                    'severity_stats': [
                        {
                            'level': stat.level,
                            'count': stat.count,
                            'percentage': stat.percentage,
                            'examples': stat.examples
                        }
                        for stat in severity_report.severity_stats
                    ],
                    'priority_violations_count': len(severity_report.priority_violations),
                    'recommendations': severity_report.recommendations,
                    'trend_data': severity_report.trend_data
                }
                
        except Exception as e:
            self.logger.error(f"Error exporting severity report: {e}")
            return {'error': f'Export failed: {str(e)}'}