"""
History Service for AutoTest
Manages test result history, trending analysis, and historical comparisons.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict
import statistics

from ..core.database import DatabaseConnection


@dataclass
class HistorySnapshot:
    """
    Historical snapshot of accessibility test results
    """
    snapshot_id: str
    project_id: Optional[str] = None
    website_id: Optional[str] = None
    page_id: Optional[str] = None
    snapshot_date: Optional[datetime] = None
    accessibility_score: Optional[float] = None
    total_violations: Optional[int] = None
    critical_violations: Optional[int] = None
    serious_violations: Optional[int] = None
    moderate_violations: Optional[int] = None
    minor_violations: Optional[int] = None
    pages_tested: Optional[int] = None
    wcag_compliance_rate: Optional[float] = None
    test_type: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class TrendingMetric:
    """
    Trending metric with historical data points
    """
    metric_name: str
    current_value: float
    previous_value: Optional[float] = None
    trend_direction: str = "stable"  # up, down, stable
    percentage_change: Optional[float] = None
    data_points: Optional[List[Dict[str, Any]]] = None
    confidence_level: Optional[str] = None  # high, medium, low


class HistoryService:
    """
    Comprehensive test result history and trending service
    """
    
    def __init__(self, config, db_connection: DatabaseConnection):
        """
        Initialize history service
        
        Args:
            config: Application configuration
            db_connection: Database connection instance
        """
        self.config = config
        self.db_connection = db_connection
        self.logger = logging.getLogger(__name__)
        
        # Initialize database
        self._init_database()
    
    def _init_database(self):
        """Initialize database collections for history tracking"""
        try:
            # Create indexes for efficient querying
            self.db_connection.db.history_snapshots.create_index("snapshot_id", unique=True)
            self.db_connection.db.history_snapshots.create_index("snapshot_date")
            self.db_connection.db.history_snapshots.create_index("project_id")
            self.db_connection.db.history_snapshots.create_index("website_id")
            self.db_connection.db.history_snapshots.create_index("page_id")
            
            # Trending metrics
            self.db_connection.db.trending_metrics.create_index("metric_name")
            self.db_connection.db.trending_metrics.create_index("project_id")
            self.db_connection.db.trending_metrics.create_index("calculated_date")
            
            self.logger.info("History service database collections initialized")
            
        except Exception as e:
            self.logger.error(f"Error initializing history database: {e}")
    
    def create_snapshot(self, snapshot_data: Dict[str, Any]) -> str:
        """
        Create a historical snapshot of test results
        
        Args:
            snapshot_data: Snapshot data including test results
            
        Returns:
            Snapshot ID
        """
        try:
            import uuid
            snapshot_id = str(uuid.uuid4())
            
            snapshot = HistorySnapshot(
                snapshot_id=snapshot_id,
                project_id=snapshot_data.get('project_id'),
                website_id=snapshot_data.get('website_id'),
                page_id=snapshot_data.get('page_id'),
                snapshot_date=datetime.now(),
                accessibility_score=snapshot_data.get('accessibility_score'),
                total_violations=snapshot_data.get('total_violations'),
                critical_violations=snapshot_data.get('critical_violations'),
                serious_violations=snapshot_data.get('serious_violations'),
                moderate_violations=snapshot_data.get('moderate_violations'),
                minor_violations=snapshot_data.get('minor_violations'),
                pages_tested=snapshot_data.get('pages_tested'),
                wcag_compliance_rate=snapshot_data.get('wcag_compliance_rate'),
                test_type=snapshot_data.get('test_type', 'accessibility'),
                metadata=snapshot_data.get('metadata', {})
            )
            
            # Store in database
            self.db_connection.db.history_snapshots.insert_one(asdict(snapshot))
            
            self.logger.info(f"Created history snapshot: {snapshot_id}")
            return snapshot_id
            
        except Exception as e:
            self.logger.error(f"Error creating snapshot: {e}")
            raise Exception(f"Failed to create snapshot: {str(e)}")
    
    def get_historical_snapshots(self, project_id: str = None, website_id: str = None,
                                page_id: str = None, time_range: str = "30d",
                                limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get historical snapshots with filtering
        
        Args:
            project_id: Filter by project ID
            website_id: Filter by website ID
            page_id: Filter by page ID
            time_range: Time range (e.g., "7d", "30d", "90d", "1y")
            limit: Maximum number of snapshots
            
        Returns:
            List of historical snapshots
        """
        try:
            # Build query
            query = {}
            
            if project_id:
                query['project_id'] = project_id
            if website_id:
                query['website_id'] = website_id
            if page_id:
                query['page_id'] = page_id
            
            # Parse time range
            days = self._parse_time_range(time_range)
            start_date = datetime.now() - timedelta(days=days)
            query['snapshot_date'] = {'$gte': start_date}
            
            # Execute query
            snapshots = list(
                self.db_connection.db.history_snapshots
                .find(query)
                .sort('snapshot_date', -1)
                .limit(limit)
            )
            
            # Remove MongoDB _id fields
            for snapshot in snapshots:
                snapshot.pop('_id', None)
            
            return snapshots
            
        except Exception as e:
            self.logger.error(f"Error getting historical snapshots: {e}")
            return []
    
    def generate_trending_analysis(self, project_id: str = None, website_id: str = None,
                                 time_range: str = "30d") -> Dict[str, Any]:
        """
        Generate comprehensive trending analysis
        
        Args:
            project_id: Project to analyze
            website_id: Website to analyze
            time_range: Time range for analysis
            
        Returns:
            Trending analysis results
        """
        try:
            # Get historical data
            snapshots = self.get_historical_snapshots(
                project_id=project_id,
                website_id=website_id,
                time_range=time_range,
                limit=1000
            )
            
            if len(snapshots) < 2:
                return {
                    'error': 'Insufficient historical data for trending analysis',
                    'snapshots_found': len(snapshots)
                }
            
            # Calculate trending metrics
            trending_metrics = self._calculate_trending_metrics(snapshots)
            
            # Generate insights
            insights = self._generate_trending_insights(trending_metrics, snapshots)
            
            # Calculate confidence levels
            for metric in trending_metrics:
                metric.confidence_level = self._calculate_confidence_level(
                    metric, len(snapshots)
                )
            
            analysis = {
                'analysis_date': datetime.now().isoformat(),
                'time_range': time_range,
                'snapshots_analyzed': len(snapshots),
                'project_id': project_id,
                'website_id': website_id,
                'trending_metrics': [asdict(metric) for metric in trending_metrics],
                'insights': insights,
                'summary': self._generate_trend_summary(trending_metrics)
            }
            
            # Store trending analysis
            self._store_trending_analysis(analysis)
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error generating trending analysis: {e}")
            return {'error': str(e)}
    
    def _calculate_trending_metrics(self, snapshots: List[Dict[str, Any]]) -> List[TrendingMetric]:
        """Calculate trending metrics from historical snapshots"""
        try:
            if len(snapshots) < 2:
                return []
            
            # Sort snapshots by date
            snapshots.sort(key=lambda x: x.get('snapshot_date', datetime.min))
            
            metrics = []
            
            # Accessibility Score Trend
            scores = [s.get('accessibility_score') for s in snapshots if s.get('accessibility_score') is not None]
            if len(scores) >= 2:
                current = scores[-1]
                previous = scores[-2]
                metric = self._create_trending_metric(
                    'accessibility_score',
                    current,
                    previous,
                    [{'date': s.get('snapshot_date'), 'value': s.get('accessibility_score')} 
                     for s in snapshots if s.get('accessibility_score') is not None]
                )
                metrics.append(metric)
            
            # Total Violations Trend
            violations = [s.get('total_violations') for s in snapshots if s.get('total_violations') is not None]
            if len(violations) >= 2:
                current = violations[-1]
                previous = violations[-2]
                metric = self._create_trending_metric(
                    'total_violations',
                    current,
                    previous,
                    [{'date': s.get('snapshot_date'), 'value': s.get('total_violations')} 
                     for s in snapshots if s.get('total_violations') is not None]
                )
                metrics.append(metric)
            
            # Critical Violations Trend
            critical = [s.get('critical_violations') for s in snapshots if s.get('critical_violations') is not None]
            if len(critical) >= 2:
                current = critical[-1]
                previous = critical[-2]
                metric = self._create_trending_metric(
                    'critical_violations',
                    current,
                    previous,
                    [{'date': s.get('snapshot_date'), 'value': s.get('critical_violations')} 
                     for s in snapshots if s.get('critical_violations') is not None]
                )
                metrics.append(metric)
            
            # WCAG Compliance Rate Trend
            compliance = [s.get('wcag_compliance_rate') for s in snapshots if s.get('wcag_compliance_rate') is not None]
            if len(compliance) >= 2:
                current = compliance[-1]
                previous = compliance[-2]
                metric = self._create_trending_metric(
                    'wcag_compliance_rate',
                    current,
                    previous,
                    [{'date': s.get('snapshot_date'), 'value': s.get('wcag_compliance_rate')} 
                     for s in snapshots if s.get('wcag_compliance_rate') is not None]
                )
                metrics.append(metric)
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error calculating trending metrics: {e}")
            return []
    
    def _create_trending_metric(self, name: str, current: float, previous: float,
                              data_points: List[Dict[str, Any]]) -> TrendingMetric:
        """Create a trending metric with trend analysis"""
        try:
            # Calculate percentage change
            if previous != 0:
                percentage_change = ((current - previous) / previous) * 100
            else:
                percentage_change = 0 if current == 0 else float('inf')
            
            # Determine trend direction
            if abs(percentage_change) < 1:  # Less than 1% change
                trend_direction = "stable"
            elif percentage_change > 0:
                # For violations, increase is bad; for scores, increase is good
                if name in ['total_violations', 'critical_violations', 'serious_violations']:
                    trend_direction = "down"  # More violations = trending down
                else:
                    trend_direction = "up"    # Higher scores = trending up
            else:
                if name in ['total_violations', 'critical_violations', 'serious_violations']:
                    trend_direction = "up"    # Fewer violations = trending up
                else:
                    trend_direction = "down"  # Lower scores = trending down
            
            return TrendingMetric(
                metric_name=name,
                current_value=current,
                previous_value=previous,
                trend_direction=trend_direction,
                percentage_change=percentage_change,
                data_points=data_points
            )
            
        except Exception as e:
            self.logger.error(f"Error creating trending metric {name}: {e}")
            return TrendingMetric(metric_name=name, current_value=current)
    
    def _generate_trending_insights(self, metrics: List[TrendingMetric],
                                  snapshots: List[Dict[str, Any]]) -> List[str]:
        """Generate insights from trending analysis"""
        insights = []
        
        try:
            # Overall accessibility trend
            accessibility_metric = next(
                (m for m in metrics if m.metric_name == 'accessibility_score'), None
            )
            if accessibility_metric:
                if accessibility_metric.trend_direction == "up":
                    insights.append(f"Accessibility score is improving (+{accessibility_metric.percentage_change:.1f}%)")
                elif accessibility_metric.trend_direction == "down":
                    insights.append(f"Accessibility score is declining ({accessibility_metric.percentage_change:.1f}%)")
                else:
                    insights.append("Accessibility score remains stable")
            
            # Violations trend
            violations_metric = next(
                (m for m in metrics if m.metric_name == 'total_violations'), None
            )
            if violations_metric:
                if violations_metric.trend_direction == "up":
                    insights.append("Total violations are decreasing - good progress!")
                elif violations_metric.trend_direction == "down":
                    insights.append("Total violations are increasing - attention needed")
                else:
                    insights.append("Violations count remains stable")
            
            # Critical violations focus
            critical_metric = next(
                (m for m in metrics if m.metric_name == 'critical_violations'), None
            )
            if critical_metric and critical_metric.current_value > 0:
                if critical_metric.trend_direction == "up":
                    insights.append("Critical violations are being resolved")
                elif critical_metric.trend_direction == "down":
                    insights.append("Critical violations are increasing - immediate action required")
                else:
                    insights.append(f"Critical violations remain at {critical_metric.current_value}")
            
            # WCAG compliance progress
            compliance_metric = next(
                (m for m in metrics if m.metric_name == 'wcag_compliance_rate'), None
            )
            if compliance_metric:
                if compliance_metric.current_value >= 95:
                    insights.append("Excellent WCAG compliance rate maintained")
                elif compliance_metric.trend_direction == "up":
                    insights.append("WCAG compliance is improving")
                elif compliance_metric.current_value < 80:
                    insights.append("WCAG compliance needs significant improvement")
            
            # Testing frequency insights
            if len(snapshots) >= 5:
                recent_snapshots = snapshots[-5:]
                dates = [s.get('snapshot_date') for s in recent_snapshots if s.get('snapshot_date')]
                if len(dates) >= 2:
                    date_diffs = [(dates[i] - dates[i-1]).days for i in range(1, len(dates))]
                    avg_interval = sum(date_diffs) / len(date_diffs)
                    
                    if avg_interval <= 3:
                        insights.append("Regular testing frequency maintained")
                    elif avg_interval > 14:
                        insights.append("Consider more frequent testing for better trend analysis")
            
            return insights
            
        except Exception as e:
            self.logger.error(f"Error generating insights: {e}")
            return ["Unable to generate insights due to data analysis error"]
    
    def _generate_trend_summary(self, metrics: List[TrendingMetric]) -> Dict[str, Any]:
        """Generate overall trend summary"""
        try:
            summary = {
                'overall_trend': 'stable',
                'positive_trends': 0,
                'negative_trends': 0,
                'stable_trends': 0,
                'key_improvements': [],
                'areas_of_concern': []
            }
            
            for metric in metrics:
                if metric.trend_direction == "up":
                    summary['positive_trends'] += 1
                    if metric.metric_name in ['accessibility_score', 'wcag_compliance_rate']:
                        summary['key_improvements'].append(f"{metric.metric_name.replace('_', ' ').title()}")
                elif metric.trend_direction == "down":
                    summary['negative_trends'] += 1
                    if metric.metric_name in ['accessibility_score', 'wcag_compliance_rate']:
                        summary['areas_of_concern'].append(f"{metric.metric_name.replace('_', ' ').title()}")
                else:
                    summary['stable_trends'] += 1
            
            # Determine overall trend
            if summary['positive_trends'] > summary['negative_trends']:
                summary['overall_trend'] = 'improving'
            elif summary['negative_trends'] > summary['positive_trends']:
                summary['overall_trend'] = 'declining'
            else:
                summary['overall_trend'] = 'stable'
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Error generating trend summary: {e}")
            return {'overall_trend': 'unknown', 'error': str(e)}
    
    def _calculate_confidence_level(self, metric: TrendingMetric, 
                                  snapshot_count: int) -> str:
        """Calculate confidence level for trending metric"""
        try:
            # Base confidence on data points and change magnitude
            if snapshot_count < 5:
                return "low"
            elif snapshot_count < 15:
                base_confidence = "medium"
            else:
                base_confidence = "high"
            
            # Adjust based on change magnitude
            if metric.percentage_change and abs(metric.percentage_change) < 2:
                # Very small changes have lower confidence
                if base_confidence == "high":
                    return "medium"
                elif base_confidence == "medium":
                    return "low"
            
            return base_confidence
            
        except Exception as e:
            self.logger.error(f"Error calculating confidence level: {e}")
            return "low"
    
    def _store_trending_analysis(self, analysis: Dict[str, Any]):
        """Store trending analysis results"""
        try:
            analysis['_id'] = f"trend_{analysis.get('project_id', 'global')}_{datetime.now().isoformat()}"
            analysis['calculated_date'] = datetime.now()
            
            self.db_connection.db.trending_metrics.insert_one(analysis)
            self.logger.info("Stored trending analysis")
            
        except Exception as e:
            self.logger.error(f"Error storing trending analysis: {e}")
    
    def _parse_time_range(self, time_range: str) -> int:
        """Parse time range string to number of days"""
        try:
            if time_range.endswith('d'):
                return int(time_range[:-1])
            elif time_range.endswith('w'):
                return int(time_range[:-1]) * 7
            elif time_range.endswith('m'):
                return int(time_range[:-1]) * 30
            elif time_range.endswith('y'):
                return int(time_range[:-1]) * 365
            else:
                return 30  # Default to 30 days
                
        except ValueError:
            return 30  # Default fallback
    
    def get_comparison_report(self, project_id: str, comparison_dates: List[str]) -> Dict[str, Any]:
        """
        Generate comparison report between specific dates
        
        Args:
            project_id: Project to compare
            comparison_dates: List of date strings to compare
            
        Returns:
            Comparison report
        """
        try:
            comparison_snapshots = []
            
            for date_str in comparison_dates:
                # Parse date and find nearest snapshot
                target_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                
                # Find snapshot closest to target date
                snapshot = self.db_connection.db.history_snapshots.find_one({
                    'project_id': project_id,
                    'snapshot_date': {
                        '$gte': target_date - timedelta(days=1),
                        '$lte': target_date + timedelta(days=1)
                    }
                }, sort=[('snapshot_date', 1)])
                
                if snapshot:
                    snapshot.pop('_id', None)
                    comparison_snapshots.append(snapshot)
            
            if len(comparison_snapshots) < 2:
                return {'error': 'Insufficient snapshots found for comparison dates'}
            
            # Generate comparison metrics
            comparison_metrics = self._calculate_comparison_metrics(comparison_snapshots)
            
            return {
                'comparison_date': datetime.now().isoformat(),
                'project_id': project_id,
                'snapshots_compared': len(comparison_snapshots),
                'comparison_snapshots': comparison_snapshots,
                'comparison_metrics': comparison_metrics,
                'summary': self._generate_comparison_summary(comparison_metrics)
            }
            
        except Exception as e:
            self.logger.error(f"Error generating comparison report: {e}")
            return {'error': str(e)}
    
    def _calculate_comparison_metrics(self, snapshots: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate metrics for snapshot comparison"""
        try:
            metrics = {}
            
            # Compare each metric across snapshots
            metric_fields = [
                'accessibility_score', 'total_violations', 'critical_violations',
                'serious_violations', 'moderate_violations', 'minor_violations',
                'wcag_compliance_rate'
            ]
            
            for field in metric_fields:
                values = [s.get(field) for s in snapshots if s.get(field) is not None]
                
                if len(values) >= 2:
                    metrics[field] = {
                        'values': values,
                        'min_value': min(values),
                        'max_value': max(values),
                        'change': values[-1] - values[0] if len(values) >= 2 else 0,
                        'percentage_change': ((values[-1] - values[0]) / values[0] * 100) if values[0] != 0 else 0
                    }
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error calculating comparison metrics: {e}")
            return {}
    
    def _generate_comparison_summary(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary for comparison report"""
        try:
            summary = {
                'improvements': [],
                'regressions': [],
                'overall_assessment': 'mixed'
            }
            
            # Analyze each metric
            for metric_name, metric_data in metrics.items():
                change = metric_data.get('change', 0)
                percentage_change = metric_data.get('percentage_change', 0)
                
                if abs(percentage_change) > 5:  # Significant changes > 5%
                    if metric_name in ['accessibility_score', 'wcag_compliance_rate']:
                        if change > 0:
                            summary['improvements'].append(f"{metric_name.replace('_', ' ').title()}: +{percentage_change:.1f}%")
                        else:
                            summary['regressions'].append(f"{metric_name.replace('_', ' ').title()}: {percentage_change:.1f}%")
                    else:  # Violations - fewer is better
                        if change < 0:
                            summary['improvements'].append(f"{metric_name.replace('_', ' ').title()}: {percentage_change:.1f}%")
                        else:
                            summary['regressions'].append(f"{metric_name.replace('_', ' ').title()}: +{percentage_change:.1f}%")
            
            # Overall assessment
            if len(summary['improvements']) > len(summary['regressions']):
                summary['overall_assessment'] = 'improving'
            elif len(summary['regressions']) > len(summary['improvements']):
                summary['overall_assessment'] = 'declining'
            else:
                summary['overall_assessment'] = 'stable'
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Error generating comparison summary: {e}")
            return {'overall_assessment': 'unknown', 'error': str(e)}
    
    def get_history_statistics(self, project_id: str = None) -> Dict[str, Any]:
        """Get history and trending statistics"""
        try:
            query = {}
            if project_id:
                query['project_id'] = project_id
            
            total_snapshots = self.db_connection.db.history_snapshots.count_documents(query)
            
            # Recent snapshots (last 30 days)
            recent_date = datetime.now() - timedelta(days=30)
            recent_snapshots = self.db_connection.db.history_snapshots.count_documents({
                **query,
                'snapshot_date': {'$gte': recent_date}
            })
            
            # Get latest snapshot for current metrics
            latest_snapshot = self.db_connection.db.history_snapshots.find_one(
                query,
                sort=[('snapshot_date', -1)]
            )
            
            stats = {
                'total_snapshots': total_snapshots,
                'recent_snapshots_30d': recent_snapshots,
                'oldest_snapshot_date': None,
                'latest_snapshot_date': None,
                'current_accessibility_score': None,
                'current_violations': None
            }
            
            if latest_snapshot:
                stats['latest_snapshot_date'] = latest_snapshot.get('snapshot_date')
                stats['current_accessibility_score'] = latest_snapshot.get('accessibility_score')
                stats['current_violations'] = latest_snapshot.get('total_violations')
            
            # Get oldest snapshot
            oldest_snapshot = self.db_connection.db.history_snapshots.find_one(
                query,
                sort=[('snapshot_date', 1)]
            )
            
            if oldest_snapshot:
                stats['oldest_snapshot_date'] = oldest_snapshot.get('snapshot_date')
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error getting history statistics: {e}")
            return {}