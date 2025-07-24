"""
Test result model for AutoTest application
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import datetime

from autotest.core.database import BaseRepository, DatabaseConnection


@dataclass
class AccessibilityViolation:
    """Accessibility violation data model"""
    violation_id: str
    impact: str  # "minor", "moderate", "serious", "critical"
    description: str
    help: str
    help_url: str = ""
    nodes: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage"""
        return {
            'id': self.violation_id,
            'impact': self.impact,
            'description': self.description,
            'help': self.help,
            'helpUrl': self.help_url,
            'nodes': self.nodes
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AccessibilityViolation':
        """Create AccessibilityViolation instance from dictionary"""
        return cls(
            violation_id=data['id'],
            impact=data['impact'],
            description=data['description'],
            help=data['help'],
            help_url=data.get('helpUrl', ''),
            nodes=data.get('nodes', [])
        )


@dataclass
class AccessibilityPass:
    """Accessibility test pass data model"""
    rule_id: str
    description: str
    help: str
    help_url: str = ""
    nodes: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage"""
        return {
            'id': self.rule_id,
            'description': self.description,
            'help': self.help,
            'helpUrl': self.help_url,
            'nodes': self.nodes
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AccessibilityPass':
        """Create AccessibilityPass instance from dictionary"""
        return cls(
            rule_id=data['id'],
            description=data['description'],
            help=data['help'],
            help_url=data.get('helpUrl', ''),
            nodes=data.get('nodes', [])
        )


@dataclass
class TestSummary:
    """Test result summary data model"""
    violations: int = 0
    passes: int = 0
    incomplete: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage"""
        return {
            'violations': self.violations,
            'passes': self.passes,
            'incomplete': self.incomplete
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TestSummary':
        """Create TestSummary instance from dictionary"""
        return cls(
            violations=data.get('violations', 0),
            passes=data.get('passes', 0),
            incomplete=data.get('incomplete', 0)
        )


@dataclass
class TestResult:
    """Test result data model"""
    result_id: Optional[str]
    page_id: str
    test_date: Optional[datetime.datetime] = None
    test_engine: str = "autotest-custom"
    violations: List[AccessibilityViolation] = field(default_factory=list)
    passes: List[AccessibilityPass] = field(default_factory=list)
    incomplete: List[Dict[str, Any]] = field(default_factory=list)
    summary: Optional[TestSummary] = None
    
    def __post_init__(self):
        """Calculate summary after initialization"""
        if self.summary is None:
            self.summary = TestSummary(
                violations=len(self.violations),
                passes=len(self.passes),
                incomplete=len(self.incomplete)
            )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage"""
        return {
            'page_id': self.page_id,
            'test_date': self.test_date,
            'test_engine': self.test_engine,
            'violations': [v.to_dict() for v in self.violations],
            'passes': [p.to_dict() for p in self.passes],
            'incomplete': self.incomplete,
            'summary': self.summary.to_dict() if self.summary else TestSummary().to_dict()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TestResult':
        """Create TestResult instance from dictionary"""
        violations = [
            AccessibilityViolation.from_dict(v_data) 
            for v_data in data.get('violations', [])
        ]
        
        passes = [
            AccessibilityPass.from_dict(p_data) 
            for p_data in data.get('passes', [])
        ]
        
        summary = TestSummary.from_dict(data.get('summary', {}))
        
        return cls(
            result_id=data.get('_id'),
            page_id=data['page_id'],
            test_date=data.get('test_date'),
            test_engine=data.get('test_engine', 'autotest-custom'),
            violations=violations,
            passes=passes,
            incomplete=data.get('incomplete', []),
            summary=summary
        )


class TestResultRepository(BaseRepository):
    """Repository for TestResult model operations"""
    
    def __init__(self, db_connection: DatabaseConnection):
        super().__init__(db_connection, 'test_results')
    
    def create_test_result(self, page_id: str, violations: List[AccessibilityViolation],
                          passes: List[AccessibilityPass], incomplete: List[Dict[str, Any]],
                          test_engine: str = "autotest-custom") -> str:
        """
        Create a new test result
        
        Args:
            page_id: Page ID that was tested
            violations: List of accessibility violations
            passes: List of accessibility passes
            incomplete: List of incomplete test results
            test_engine: Testing engine used
        
        Returns:
            Created test result ID
        """
        test_result = TestResult(
            result_id=None,
            page_id=page_id,
            test_date=datetime.datetime.utcnow(),
            test_engine=test_engine,
            violations=violations,
            passes=passes,
            incomplete=incomplete
        )
        
        return self.create(test_result.to_dict())
    
    def get_test_result(self, result_id: str) -> Optional[TestResult]:
        """
        Get test result by ID
        
        Args:
            result_id: Test result ID
        
        Returns:
            TestResult instance or None if not found
        """
        data = self.get_by_id(result_id)
        if data:
            return TestResult.from_dict(data)
        return None
    
    def get_latest_result_for_page(self, page_id: str) -> Optional[TestResult]:
        """
        Get the latest test result for a page
        
        Args:
            page_id: Page ID
        
        Returns:
            Latest TestResult instance or None if not found
        """
        results_data = self.find_all(
            filter_dict={'page_id': page_id},
            sort=[('test_date', -1)],
            limit=1
        )
        
        if results_data:
            return TestResult.from_dict(results_data[0])
        return None
    
    def get_results_for_page(self, page_id: str, limit: Optional[int] = None) -> List[TestResult]:
        """
        Get all test results for a page
        
        Args:
            page_id: Page ID
            limit: Maximum number of results to return
        
        Returns:
            List of TestResult instances
        """
        results_data = self.find_all(
            filter_dict={'page_id': page_id},
            sort=[('test_date', -1)],
            limit=limit
        )
        return [TestResult.from_dict(data) for data in results_data]
    
    def get_results_by_project(self, project_id: str, limit: Optional[int] = None) -> List[TestResult]:
        """
        Get test results for all pages in a project
        
        Args:
            project_id: Project ID
            limit: Maximum number of results to return
        
        Returns:
            List of TestResult instances
        """
        # First get all pages for the project
        from autotest.models.page import PageRepository
        page_repo = PageRepository(self.db_connection)
        pages = page_repo.get_pages_by_project(project_id)
        
        if not pages:
            return []
        
        page_ids = [page.page_id for page in pages if page.page_id]
        
        results_data = self.find_all(
            filter_dict={'page_id': {'$in': page_ids}},
            sort=[('test_date', -1)],
            limit=limit
        )
        return [TestResult.from_dict(data) for data in results_data]
    
    def get_violation_summary_by_project(self, project_id: str) -> Dict[str, Any]:
        """
        Get violation summary statistics for a project
        
        Args:
            project_id: Project ID
        
        Returns:
            Dictionary with violation statistics
        """
        results = self.get_results_by_project(project_id)
        
        total_violations = 0
        total_passes = 0
        total_incomplete = 0
        violation_by_impact = {'critical': 0, 'serious': 0, 'moderate': 0, 'minor': 0}
        
        for result in results:
            if result.summary:
                total_violations += result.summary.violations
                total_passes += result.summary.passes
                total_incomplete += result.summary.incomplete
            
            for violation in result.violations:
                if violation.impact in violation_by_impact:
                    violation_by_impact[violation.impact] += 1
        
        return {
            'total_violations': total_violations,
            'total_passes': total_passes,
            'total_incomplete': total_incomplete,
            'violations_by_impact': violation_by_impact,
            'total_tests': len(results)
        }
    
    def delete_results_by_page(self, page_id: str) -> int:
        """
        Delete all test results for a page
        
        Args:
            page_id: Page ID
        
        Returns:
            Number of results deleted
        """
        try:
            result = self.collection.delete_many({'page_id': page_id})
            
            self.logger.info(f"Deleted {result.deleted_count} test results for page {page_id}")
            return result.deleted_count
            
        except Exception as e:
            self.logger.error(f"Error deleting test results for page {page_id}: {e}")
            return 0
    
    def delete_old_results(self, days_old: int = 90) -> int:
        """
        Delete test results older than specified days
        
        Args:
            days_old: Number of days after which results should be deleted
        
        Returns:
            Number of results deleted
        """
        try:
            cutoff_date = datetime.datetime.utcnow() - datetime.timedelta(days=days_old)
            
            result = self.collection.delete_many({
                'test_date': {'$lt': cutoff_date}
            })
            
            self.logger.info(f"Deleted {result.deleted_count} old test results")
            return result.deleted_count
            
        except Exception as e:
            self.logger.error(f"Error deleting old test results: {e}")
            return 0
    
    def get_test_history_for_page(self, page_id: str, days: int = 30) -> List[Dict[str, Any]]:
        """
        Get test history for a page over specified days
        
        Args:
            page_id: Page ID
            days: Number of days of history to retrieve
        
        Returns:
            List of dictionaries with date and violation counts
        """
        cutoff_date = datetime.datetime.utcnow() - datetime.timedelta(days=days)
        
        results = self.find_all(
            filter_dict={
                'page_id': page_id,
                'test_date': {'$gte': cutoff_date}
            },
            sort=[('test_date', 1)]
        )
        
        history = []
        for result_data in results:
            result = TestResult.from_dict(result_data)
            history.append({
                'date': result.test_date,
                'violations': result.summary.violations if result.summary else 0,
                'passes': result.summary.passes if result.summary else 0,
                'incomplete': result.summary.incomplete if result.summary else 0
            })
        
        return history