"""
Reporting Service for AutoTest
Generates comprehensive accessibility reports in multiple formats.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import io
import base64

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
    from reportlab.platypus.tableofcontents import TableOfContents
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    logging.warning("ReportLab not available - PDF reports will be disabled")

from ..core.database import DatabaseConnection


@dataclass
class ReportSection:
    """
    Report section definition
    """
    section_id: str
    title: str
    content: str
    section_type: str = "text"  # text, table, chart, image
    data: Optional[Dict[str, Any]] = None
    order: int = 0


@dataclass
class ReportTemplate:
    """
    Report template definition
    """
    template_id: str
    name: str
    description: str
    sections: List[str]
    format_options: Dict[str, Any]
    target_audience: str = "technical"  # technical, executive, compliance


class ReportingService:
    """
    Comprehensive accessibility reporting service
    """
    
    def __init__(self, config, db_connection: DatabaseConnection):
        """
        Initialize reporting service
        
        Args:
            config: Application configuration
            db_connection: Database connection instance
        """
        self.config = config
        self.db_connection = db_connection
        self.logger = logging.getLogger(__name__)
        
        # Initialize report templates
        self.templates = self._initialize_report_templates()
        
        # Initialize database
        self._init_database()
    
    def _init_database(self):
        """Initialize database collections for reports"""
        try:
            # Create indexes for efficient querying
            self.db_connection.db.generated_reports.create_index("report_id", unique=True)
            self.db_connection.db.generated_reports.create_index("created_date")
            self.db_connection.db.generated_reports.create_index("project_id")
            self.db_connection.db.generated_reports.create_index("report_type")
            
            self.logger.info("Reporting service database collections initialized")
            
        except Exception as e:
            self.logger.error(f"Error initializing reporting database: {e}")
    
    def _initialize_report_templates(self) -> Dict[str, ReportTemplate]:
        """Initialize predefined report templates"""
        templates = {}
        
        # Executive Summary Report
        templates['executive_summary'] = ReportTemplate(
            template_id='executive_summary',
            name='Executive Summary Report',
            description='High-level accessibility overview for executives and stakeholders',
            sections=[
                'executive_summary',
                'key_metrics',
                'compliance_status',
                'risk_assessment',
                'recommendations',
                'action_plan'
            ],
            format_options={
                'include_charts': True,
                'include_technical_details': False,
                'page_limit': 10,
                'focus_areas': ['compliance', 'risk', 'business_impact']
            },
            target_audience='executive'
        )
        
        # Technical Detailed Report
        templates['technical_detailed'] = ReportTemplate(
            template_id='technical_detailed',
            name='Technical Detailed Report',
            description='Comprehensive technical report for developers and QA teams',
            sections=[
                'technical_summary',
                'detailed_violations',
                'code_examples',
                'remediation_guide',
                'testing_methodology',
                'appendices'
            ],
            format_options={
                'include_charts': True,
                'include_technical_details': True,
                'include_code_snippets': True,
                'detailed_violations': True,
                'page_limit': None
            },
            target_audience='technical'
        )
        
        # Compliance Audit Report
        templates['compliance_audit'] = ReportTemplate(
            template_id='compliance_audit',
            name='Compliance Audit Report',
            description='WCAG compliance audit report for legal and compliance teams',
            sections=[
                'compliance_overview',
                'wcag_checklist',
                'violation_breakdown',
                'compliance_gaps',
                'remediation_timeline',
                'certification_readiness'
            ],
            format_options={
                'include_charts': True,
                'include_technical_details': False,
                'focus_wcag_compliance': True,
                'include_legal_implications': True,
                'page_limit': 25
            },
            target_audience='compliance'
        )
        
        # Progress Tracking Report
        templates['progress_tracking'] = ReportTemplate(
            template_id='progress_tracking',
            name='Progress Tracking Report',
            description='Historical progress and trending analysis report',
            sections=[
                'progress_overview',
                'trending_analysis',
                'milestone_tracking',
                'comparative_analysis',
                'future_projections',
                'next_steps'
            ],
            format_options={
                'include_charts': True,
                'include_historical_data': True,
                'time_range': '90d',
                'include_projections': True,
                'page_limit': 15
            },
            target_audience='technical'
        )
        
        return templates
    
    def generate_report(self, report_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate comprehensive accessibility report
        
        Args:
            report_config: Report configuration including template, data sources, format
            
        Returns:
            Generated report data and metadata
        """
        try:
            import uuid
            report_id = str(uuid.uuid4())
            
            # Validate configuration
            template_id = report_config.get('template_id', 'technical_detailed')
            template = self.templates.get(template_id)
            
            if not template:
                raise Exception(f"Unknown report template: {template_id}")
            
            # Initialize report
            report = {
                'report_id': report_id,
                'template_id': template_id,
                'template_name': template.name,
                'created_date': datetime.now(),
                'project_id': report_config.get('project_id'),
                'website_id': report_config.get('website_id'),
                'time_range': report_config.get('time_range', '30d'),
                'format': report_config.get('format', 'html'),
                'sections': [],
                'metadata': {
                    'generated_by': report_config.get('generated_by', 'system'),
                    'generation_time': datetime.now(),
                    'data_sources': report_config.get('data_sources', []),
                    'filters_applied': report_config.get('filters', {})
                }
            }
            
            # Gather data for report
            report_data = self._gather_report_data(report_config)
            
            # Generate each section
            for section_id in template.sections:
                section = self._generate_report_section(
                    section_id, report_data, template.format_options
                )
                if section:
                    report['sections'].append(asdict(section))
            
            # Generate formatted output
            formatted_output = self._format_report(report, report_config.get('format', 'html'))
            report['formatted_output'] = formatted_output
            
            # Store report
            self._store_report(report)
            
            self.logger.info(f"Generated report: {report_id} using template {template_id}")
            return report
            
        except Exception as e:
            self.logger.error(f"Error generating report: {e}")
            raise Exception(f"Failed to generate report: {str(e)}")
    
    def _gather_report_data(self, report_config: Dict[str, Any]) -> Dict[str, Any]:
        """Gather all necessary data for report generation"""
        try:
            project_id = report_config.get('project_id')
            website_id = report_config.get('website_id')
            time_range = report_config.get('time_range', '30d')
            
            data = {
                'project_info': {},
                'test_results': {},
                'violations': [],
                'metrics': {},
                'historical_data': [],
                'compliance_status': {}
            }
            
            # Get project information
            if project_id:
                from ..core.project_manager import ProjectManager
                project_manager = ProjectManager(self.db_connection)
                data['project_info'] = project_manager.get_project(project_id) or {}
            
            # Get test results
            data['test_results'] = self._get_test_results_data(project_id, website_id, time_range)
            
            # Get violations
            data['violations'] = self._get_violations_data(project_id, website_id, time_range)
            
            # Calculate metrics
            data['metrics'] = self._calculate_report_metrics(data['violations'])
            
            # Get historical data if needed
            if 'historical_data' in report_config.get('data_sources', []):
                data['historical_data'] = self._get_historical_data(project_id, time_range)
            
            # Calculate compliance status
            data['compliance_status'] = self._calculate_compliance_status(data['violations'])
            
            return data
            
        except Exception as e:
            self.logger.error(f"Error gathering report data: {e}")
            return {}
    
    def _get_test_results_data(self, project_id: str, website_id: str, time_range: str) -> Dict[str, Any]:
        """Get test results data for the report"""
        try:
            # This would integrate with the testing service
            # For now, return mock data structure
            return {
                'total_pages_tested': 0,
                'total_tests_run': 0,
                'test_completion_rate': 0,
                'average_test_duration': 0,
                'last_test_date': None,
                'test_frequency': 'unknown'
            }
            
        except Exception as e:
            self.logger.error(f"Error getting test results data: {e}")
            return {}
    
    def _get_violations_data(self, project_id: str, website_id: str, time_range: str) -> List[Dict[str, Any]]:
        """Get violations data for the report"""
        try:
            # This would query the actual violations from the database
            # For now, return mock data structure
            return []
            
        except Exception as e:
            self.logger.error(f"Error getting violations data: {e}")
            return []
    
    def _calculate_report_metrics(self, violations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate key metrics from violations data"""
        try:
            if not violations:
                return {
                    'total_violations': 0,
                    'critical_violations': 0,
                    'serious_violations': 0,
                    'moderate_violations': 0,
                    'minor_violations': 0,
                    'accessibility_score': 0,
                    'wcag_compliance_rate': 0
                }
            
            # Count violations by severity
            severity_counts = {'critical': 0, 'serious': 0, 'moderate': 0, 'minor': 0}
            
            for violation in violations:
                severity = violation.get('severity', 'minor')
                if severity in severity_counts:
                    severity_counts[severity] += 1
            
            total_violations = sum(severity_counts.values())
            
            # Calculate accessibility score (simplified)
            score_deductions = {
                'critical': 10,
                'serious': 5,
                'moderate': 2,
                'minor': 1
            }
            
            total_deduction = sum(
                count * score_deductions[severity] 
                for severity, count in severity_counts.items()
            )
            
            accessibility_score = max(0, 100 - total_deduction)
            
            # Calculate WCAG compliance rate (simplified)
            wcag_compliance_rate = max(0, 100 - (severity_counts['critical'] * 5) - (severity_counts['serious'] * 2))
            
            return {
                'total_violations': total_violations,
                'critical_violations': severity_counts['critical'],
                'serious_violations': severity_counts['serious'],
                'moderate_violations': severity_counts['moderate'],
                'minor_violations': severity_counts['minor'],
                'accessibility_score': accessibility_score,
                'wcag_compliance_rate': min(100, wcag_compliance_rate)
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating report metrics: {e}")
            return {}
    
    def _get_historical_data(self, project_id: str, time_range: str) -> List[Dict[str, Any]]:
        """Get historical data for trending analysis"""
        try:
            # This would integrate with the history service
            # For now, return mock data structure
            return []
            
        except Exception as e:
            self.logger.error(f"Error getting historical data: {e}")
            return []
    
    def _calculate_compliance_status(self, violations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate WCAG compliance status"""
        try:
            # Count violations by WCAG level
            wcag_violations = {'A': 0, 'AA': 0, 'AAA': 0}
            
            for violation in violations:
                wcag_level = violation.get('wcag_level', 'AA')
                if wcag_level in wcag_violations:
                    wcag_violations[wcag_level] += 1
            
            # Determine compliance levels
            compliance_status = {
                'wcag_a_compliant': wcag_violations['A'] == 0,
                'wcag_aa_compliant': wcag_violations['A'] == 0 and wcag_violations['AA'] == 0,
                'wcag_aaa_compliant': all(count == 0 for count in wcag_violations.values()),
                'violations_by_level': wcag_violations,
                'overall_compliance_level': 'Non-compliant'
            }
            
            if compliance_status['wcag_aaa_compliant']:
                compliance_status['overall_compliance_level'] = 'WCAG AAA'
            elif compliance_status['wcag_aa_compliant']:
                compliance_status['overall_compliance_level'] = 'WCAG AA'
            elif compliance_status['wcag_a_compliant']:
                compliance_status['overall_compliance_level'] = 'WCAG A'
            
            return compliance_status
            
        except Exception as e:
            self.logger.error(f"Error calculating compliance status: {e}")
            return {}
    
    def _generate_report_section(self, section_id: str, report_data: Dict[str, Any],
                                format_options: Dict[str, Any]) -> Optional[ReportSection]:
        """Generate a specific report section"""
        try:
            section_generators = {
                'executive_summary': self._generate_executive_summary,
                'technical_summary': self._generate_technical_summary,
                'key_metrics': self._generate_key_metrics,
                'detailed_violations': self._generate_detailed_violations,
                'compliance_status': self._generate_compliance_status,
                'recommendations': self._generate_recommendations,
                'trending_analysis': self._generate_trending_analysis,
                'remediation_guide': self._generate_remediation_guide
            }
            
            generator = section_generators.get(section_id)
            if not generator:
                self.logger.warning(f"No generator found for section: {section_id}")
                return None
            
            return generator(report_data, format_options)
            
        except Exception as e:
            self.logger.error(f"Error generating section {section_id}: {e}")
            return None
    
    def _generate_executive_summary(self, data: Dict[str, Any], options: Dict[str, Any]) -> ReportSection:
        """Generate executive summary section"""
        metrics = data.get('metrics', {})
        compliance = data.get('compliance_status', {})
        
        content = f"""
        ## Executive Summary
        
        This accessibility audit reveals {metrics.get('total_violations', 0)} accessibility issues 
        across the tested pages, with an overall accessibility score of {metrics.get('accessibility_score', 0)}%.
        
        **Key Findings:**
        - {metrics.get('critical_violations', 0)} critical accessibility barriers require immediate attention
        - Current WCAG compliance level: {compliance.get('overall_compliance_level', 'Unknown')}
        - {metrics.get('wcag_compliance_rate', 0)}% WCAG compliance rate achieved
        
        **Business Impact:**
        Critical accessibility issues may expose the organization to legal risks and prevent access 
        for users with disabilities, representing approximately 15% of the global population.
        
        **Immediate Action Required:**
        Priority should be given to resolving {metrics.get('critical_violations', 0)} critical violations
        to minimize legal exposure and improve user experience.
        """
        
        return ReportSection(
            section_id='executive_summary',
            title='Executive Summary',
            content=content.strip(),
            section_type='text',
            order=1
        )
    
    def _generate_technical_summary(self, data: Dict[str, Any], options: Dict[str, Any]) -> ReportSection:
        """Generate technical summary section"""
        metrics = data.get('metrics', {})
        test_results = data.get('test_results', {})
        
        content = f"""
        ## Technical Summary
        
        **Testing Overview:**
        - Pages tested: {test_results.get('total_pages_tested', 0)}
        - Total tests executed: {test_results.get('total_tests_run', 0)}
        - Test completion rate: {test_results.get('test_completion_rate', 0)}%
        
        **Violation Breakdown:**
        - Critical: {metrics.get('critical_violations', 0)} violations
        - Serious: {metrics.get('serious_violations', 0)} violations  
        - Moderate: {metrics.get('moderate_violations', 0)} violations
        - Minor: {metrics.get('minor_violations', 0)} violations
        
        **Accessibility Metrics:**
        - Overall accessibility score: {metrics.get('accessibility_score', 0)}/100
        - WCAG compliance rate: {metrics.get('wcag_compliance_rate', 0)}%
        
        **Testing Methodology:**
        Automated accessibility testing was conducted using industry-standard tools and techniques,
        including WCAG 2.1 AA guidelines compliance verification.
        """
        
        return ReportSection(
            section_id='technical_summary',
            title='Technical Summary',
            content=content.strip(),
            section_type='text',
            order=2
        )
    
    def _generate_key_metrics(self, data: Dict[str, Any], options: Dict[str, Any]) -> ReportSection:
        """Generate key metrics section with chart data"""
        metrics = data.get('metrics', {})
        
        # Create chart data for metrics visualization
        chart_data = {
            'violations_by_severity': [
                {'label': 'Critical', 'value': metrics.get('critical_violations', 0), 'color': '#dc3545'},
                {'label': 'Serious', 'value': metrics.get('serious_violations', 0), 'color': '#fd7e14'},
                {'label': 'Moderate', 'value': metrics.get('moderate_violations', 0), 'color': '#ffc107'},
                {'label': 'Minor', 'value': metrics.get('minor_violations', 0), 'color': '#28a745'}
            ],
            'accessibility_score': metrics.get('accessibility_score', 0),
            'compliance_rate': metrics.get('wcag_compliance_rate', 0)
        }
        
        content = f"""
        ## Key Accessibility Metrics
        
        **Overall Performance:**
        - Accessibility Score: {metrics.get('accessibility_score', 0)}/100
        - WCAG Compliance Rate: {metrics.get('wcag_compliance_rate', 0)}%
        - Total Issues Found: {metrics.get('total_violations', 0)}
        
        **Issue Distribution:**
        The following chart shows the distribution of accessibility issues by severity level.
        """
        
        return ReportSection(
            section_id='key_metrics',
            title='Key Accessibility Metrics',
            content=content.strip(),
            section_type='chart',
            data=chart_data,
            order=3
        )
    
    def _generate_detailed_violations(self, data: Dict[str, Any], options: Dict[str, Any]) -> ReportSection:
        """Generate detailed violations section"""
        violations = data.get('violations', [])
        
        if not violations:
            content = "No accessibility violations were found during testing."
        else:
            content = "## Detailed Violation Analysis\n\n"
            
            # Group violations by severity
            by_severity = {}
            for violation in violations:
                severity = violation.get('severity', 'minor')
                if severity not in by_severity:
                    by_severity[severity] = []
                by_severity[severity].append(violation)
            
            for severity in ['critical', 'serious', 'moderate', 'minor']:
                if severity in by_severity:
                    content += f"\n### {severity.title()} Violations ({len(by_severity[severity])})\n\n"
                    
                    for i, violation in enumerate(by_severity[severity][:10], 1):  # Limit to top 10
                        content += f"""
                        **{i}. {violation.get('rule_name', 'Unknown Rule')}**
                        - Element: `{violation.get('element', 'Unknown')}`
                        - Description: {violation.get('description', 'No description available')}
                        - WCAG Guideline: {violation.get('wcag_guideline', 'Not specified')}
                        - Recommendation: {violation.get('recommendation', 'See WCAG guidelines')}
                        
                        """
        
        return ReportSection(
            section_id='detailed_violations',
            title='Detailed Violation Analysis',
            content=content.strip(),
            section_type='text',
            order=4
        )
    
    def _generate_compliance_status(self, data: Dict[str, Any], options: Dict[str, Any]) -> ReportSection:
        """Generate compliance status section"""
        compliance = data.get('compliance_status', {})
        
        content = f"""
        ## WCAG Compliance Status
        
        **Current Compliance Level:** {compliance.get('overall_compliance_level', 'Unknown')}
        
        **Compliance Assessment:**
        - WCAG A Compliant: {'✅ Yes' if compliance.get('wcag_a_compliant') else '❌ No'}
        - WCAG AA Compliant: {'✅ Yes' if compliance.get('wcag_aa_compliant') else '❌ No'}
        - WCAG AAA Compliant: {'✅ Yes' if compliance.get('wcag_aaa_compliant') else '❌ No'}
        
        **Violations by WCAG Level:**
        - Level A: {compliance.get('violations_by_level', {}).get('A', 0)} violations
        - Level AA: {compliance.get('violations_by_level', {}).get('AA', 0)} violations
        - Level AAA: {compliance.get('violations_by_level', {}).get('AAA', 0)} violations
        
        **Legal and Business Implications:**
        {self._get_compliance_implications(compliance.get('overall_compliance_level', 'Non-compliant'))}
        """
        
        return ReportSection(
            section_id='compliance_status',
            title='WCAG Compliance Status',
            content=content.strip(),
            section_type='text',
            order=5
        )
    
    def _generate_recommendations(self, data: Dict[str, Any], options: Dict[str, Any]) -> ReportSection:
        """Generate recommendations section"""
        metrics = data.get('metrics', {})
        violations = data.get('violations', [])
        
        recommendations = []
        
        # Generate recommendations based on findings
        if metrics.get('critical_violations', 0) > 0:
            recommendations.append(
                "**Immediate Action Required:** Address all critical accessibility violations "
                "within 30 days to minimize legal risk and improve user experience."
            )
        
        if metrics.get('accessibility_score', 0) < 70:
            recommendations.append(
                "**Accessibility Overhaul:** The current accessibility score indicates significant "
                "barriers exist. Consider a comprehensive accessibility audit and remediation plan."
            )
        
        if metrics.get('wcag_compliance_rate', 0) < 80:
            recommendations.append(
                "**WCAG Compliance Focus:** Prioritize achieving WCAG 2.1 AA compliance to meet "
                "legal requirements and industry standards."
            )
        
        # Add general recommendations
        recommendations.extend([
            "**Staff Training:** Provide accessibility training for development and design teams.",
            "**Process Integration:** Integrate accessibility testing into your development workflow.",
            "**Regular Monitoring:** Implement automated accessibility monitoring for continuous compliance.",
            "**User Testing:** Conduct usability testing with users who have disabilities."
        ])
        
        content = "## Recommendations\n\n" + "\n\n".join(f"{i+1}. {rec}" for i, rec in enumerate(recommendations))
        
        return ReportSection(
            section_id='recommendations',
            title='Recommendations',
            content=content,
            section_type='text',
            order=6
        )
    
    def _generate_trending_analysis(self, data: Dict[str, Any], options: Dict[str, Any]) -> ReportSection:
        """Generate trending analysis section"""
        historical_data = data.get('historical_data', [])
        
        if not historical_data:
            content = """
            ## Trending Analysis
            
            Historical data is not available for trending analysis. 
            Continue regular testing to build a trend analysis baseline.
            """
        else:
            content = """
            ## Trending Analysis
            
            **Historical Performance:**
            Based on historical testing data, accessibility metrics trends are analyzed below.
            
            **Key Trends:**
            - Accessibility score progression over time
            - Violation count trends by severity
            - WCAG compliance rate improvements
            
            **Insights:**
            Trend analysis will be available after collecting sufficient historical data points.
            """
        
        return ReportSection(
            section_id='trending_analysis',
            title='Trending Analysis',
            content=content.strip(),
            section_type='text',
            order=7
        )
    
    def _generate_remediation_guide(self, data: Dict[str, Any], options: Dict[str, Any]) -> ReportSection:
        """Generate remediation guide section"""
        violations = data.get('violations', [])
        
        content = """
        ## Remediation Guide
        
        **Priority Framework:**
        1. **Critical Issues (Immediate - 0-30 days):** Legal risk, complete barriers to access
        2. **Serious Issues (High - 30-90 days):** Significant usability barriers
        3. **Moderate Issues (Medium - 90-180 days):** Usability improvements
        4. **Minor Issues (Low - 180+ days):** Enhancement opportunities
        
        **Implementation Strategy:**
        1. **Assessment Phase:** Complete comprehensive accessibility audit
        2. **Planning Phase:** Develop remediation timeline and resource allocation
        3. **Implementation Phase:** Execute fixes in priority order
        4. **Testing Phase:** Validate fixes and conduct user testing
        5. **Monitoring Phase:** Implement ongoing accessibility monitoring
        
        **Resources:**
        - WCAG 2.1 Guidelines: https://www.w3.org/WAI/WCAG21/quickref/
        - WebAIM Resources: https://webaim.org/
        - Accessibility Testing Tools: Various automated and manual testing tools
        """
        
        return ReportSection(
            section_id='remediation_guide',
            title='Remediation Guide',
            content=content.strip(),
            section_type='text',
            order=8
        )
    
    def _get_compliance_implications(self, compliance_level: str) -> str:
        """Get legal and business implications text based on compliance level"""
        implications = {
            'WCAG AAA': 'Excellent compliance exceeding legal requirements. Minimal legal risk.',
            'WCAG AA': 'Good compliance meeting most legal requirements. Low legal risk.',
            'WCAG A': 'Basic compliance with significant gaps. Moderate legal risk.',
            'Non-compliant': 'High legal risk. Immediate remediation recommended to avoid potential lawsuits.'
        }
        
        return implications.get(compliance_level, 'Compliance status unclear. Legal review recommended.')
    
    def _format_report(self, report: Dict[str, Any], format_type: str) -> str:
        """Format report for specified output format"""
        try:
            if format_type.lower() == 'html':
                return self._format_html_report(report)
            elif format_type.lower() == 'pdf' and REPORTLAB_AVAILABLE:
                return self._format_pdf_report(report)
            elif format_type.lower() == 'json':
                return json.dumps(report, indent=2, default=str)
            else:
                return self._format_markdown_report(report)
                
        except Exception as e:
            self.logger.error(f"Error formatting report as {format_type}: {e}")
            return f"Error formatting report: {str(e)}"
    
    def _format_html_report(self, report: Dict[str, Any]) -> str:
        """Format report as HTML"""
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{report.get('template_name', 'Accessibility Report')}</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; margin: 40px; }}
                .header {{ border-bottom: 2px solid #333; padding-bottom: 20px; margin-bottom: 30px; }}
                .section {{ margin-bottom: 40px; }}
                .metrics {{ display: flex; gap: 20px; margin: 20px 0; }}
                .metric {{ background: #f4f4f4; padding: 15px; border-radius: 5px; text-align: center; }}
                pre {{ background: #f8f8f8; padding: 15px; border-radius: 5px; overflow-x: auto; }}
                .violation {{ border-left: 4px solid #dc3545; padding-left: 15px; margin: 10px 0; }}
                .critical {{ border-left-color: #dc3545; }}
                .serious {{ border-left-color: #fd7e14; }}
                .moderate {{ border-left-color: #ffc107; }}
                .minor {{ border-left-color: #28a745; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>{report.get('template_name', 'Accessibility Report')}</h1>
                <p>Generated on {report.get('created_date', datetime.now()).strftime('%B %d, %Y')}</p>
                <p>Project: {report.get('project_id', 'Unknown')}</p>
            </div>
        """
        
        # Add sections
        for section in sorted(report.get('sections', []), key=lambda x: x.get('order', 0)):
            html_content += f'<div class="section">'
            html_content += f'<h2>{section.get("title", "Untitled Section")}</h2>'
            
            # Convert markdown-style content to HTML
            content = section.get('content', '').replace('**', '<strong>').replace('**', '</strong>')
            content = content.replace('## ', '<h3>').replace('\n', '</h3>\n')
            content = content.replace('- ', '<li>').replace('\n<li>', '</li>\n<li>')
            
            html_content += f'<div>{content}</div>'
            html_content += '</div>'
        
        html_content += """
        </body>
        </html>
        """
        
        return html_content
    
    def _format_pdf_report(self, report: Dict[str, Any]) -> str:
        """Format report as PDF (returns base64 encoded PDF)"""
        if not REPORTLAB_AVAILABLE:
            return "PDF generation not available - ReportLab not installed"
        
        try:
            # Create PDF buffer
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            
            # Get styles
            styles = getSampleStyleSheet()
            story = []
            
            # Title
            title = Paragraph(report.get('template_name', 'Accessibility Report'), styles['Title'])
            story.append(title)
            story.append(Spacer(1, 12))
            
            # Metadata
            meta_text = f"Generated on {report.get('created_date', datetime.now()).strftime('%B %d, %Y')}<br/>"
            meta_text += f"Project: {report.get('project_id', 'Unknown')}"
            meta = Paragraph(meta_text, styles['Normal'])
            story.append(meta)
            story.append(Spacer(1, 24))
            
            # Add sections
            for section in sorted(report.get('sections', []), key=lambda x: x.get('order', 0)):
                # Section title
                section_title = Paragraph(section.get('title', 'Untitled Section'), styles['Heading1'])
                story.append(section_title)
                story.append(Spacer(1, 12))
                
                # Section content
                content = section.get('content', '').replace('**', '<b>').replace('**', '</b>')
                section_content = Paragraph(content, styles['Normal'])
                story.append(section_content)
                story.append(Spacer(1, 24))
            
            # Build PDF
            doc.build(story)
            
            # Get PDF data and encode as base64
            pdf_data = buffer.getvalue()
            buffer.close()
            
            return base64.b64encode(pdf_data).decode('utf-8')
            
        except Exception as e:
            self.logger.error(f"Error generating PDF report: {e}")
            return f"Error generating PDF: {str(e)}"
    
    def _format_markdown_report(self, report: Dict[str, Any]) -> str:
        """Format report as Markdown"""
        markdown_content = f"# {report.get('template_name', 'Accessibility Report')}\n\n"
        markdown_content += f"**Generated:** {report.get('created_date', datetime.now()).strftime('%B %d, %Y')}\n"
        markdown_content += f"**Project:** {report.get('project_id', 'Unknown')}\n\n"
        markdown_content += "---\n\n"
        
        # Add sections
        for section in sorted(report.get('sections', []), key=lambda x: x.get('order', 0)):
            markdown_content += f"# {section.get('title', 'Untitled Section')}\n\n"
            markdown_content += f"{section.get('content', '')}\n\n"
            markdown_content += "---\n\n"
        
        return markdown_content
    
    def _store_report(self, report: Dict[str, Any]):
        """Store generated report in database"""
        try:
            # Remove large formatted output for database storage
            report_copy = report.copy()
            if len(report_copy.get('formatted_output', '')) > 100000:  # 100KB limit
                report_copy['formatted_output'] = '[Large content - stored separately]'
            
            self.db_connection.db.generated_reports.insert_one(report_copy)
            self.logger.info(f"Stored report: {report['report_id']}")
            
        except Exception as e:
            self.logger.error(f"Error storing report: {e}")
    
    def get_report(self, report_id: str) -> Optional[Dict[str, Any]]:
        """Get a stored report by ID"""
        try:
            report = self.db_connection.db.generated_reports.find_one(
                {'report_id': report_id}
            )
            
            if report:
                report.pop('_id', None)
                return report
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting report {report_id}: {e}")
            return None
    
    def list_reports(self, project_id: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        """List generated reports with optional filtering"""
        try:
            query = {}
            if project_id:
                query['project_id'] = project_id
            
            reports = list(
                self.db_connection.db.generated_reports
                .find(query, {'formatted_output': 0})  # Exclude large content
                .sort('created_date', -1)
                .limit(limit)
            )
            
            # Remove MongoDB _id fields
            for report in reports:
                report.pop('_id', None)
            
            return reports
            
        except Exception as e:
            self.logger.error(f"Error listing reports: {e}")
            return []
    
    def delete_report(self, report_id: str) -> bool:
        """Delete a report"""
        try:
            result = self.db_connection.db.generated_reports.delete_one(
                {'report_id': report_id}
            )
            
            return result.deleted_count > 0
            
        except Exception as e:
            self.logger.error(f"Error deleting report {report_id}: {e}")
            return False
    
    def get_available_templates(self) -> List[Dict[str, Any]]:
        """Get list of available report templates"""
        return [
            {
                'template_id': template.template_id,
                'name': template.name,
                'description': template.description,
                'target_audience': template.target_audience,
                'sections': template.sections,
                'format_options': template.format_options
            }
            for template in self.templates.values()
        ]