#!/usr/bin/env python3
"""
Debug script to analyze project statistics calculation discrepancy
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'autotest'))

from autotest.core.database import DatabaseConnection
from autotest.core.project_manager import ProjectManager
from autotest.models.project import ProjectRepository
from autotest.models.page import PageRepository
from autotest.models.test_result import TestResultRepository
from autotest.utils.config import Config

def debug_project_statistics(project_id: str):
    """Debug project statistics calculation"""
    
    # Initialize components
    config = Config()
    db_connection = DatabaseConnection(config)
    db_connection.connect()
    
    project_manager = ProjectManager(db_connection)
    project_repo = ProjectRepository(db_connection)
    page_repo = PageRepository(db_connection)
    test_result_repo = TestResultRepository(db_connection)
    
    print(f"=== Debugging Project Statistics for {project_id} ===\n")
    
    # 1. Get project basic info
    project = project_repo.get_project(project_id)
    if not project:
        print("Project not found!")
        return
    
    print(f"Project: {project.name}")
    print(f"Websites: {len(project.websites)}")
    
    # 2. Get page counts
    total_pages = page_repo.count({'project_id': project_id})
    print(f"Total pages: {total_pages}")
    
    # 3. Direct test results query
    all_results = test_result_repo.get_results_by_project(project_id)
    print(f"Total test results found: {len(all_results)}")
    
    # 4. Analyze test results
    total_violations_direct = 0
    total_passes_direct = 0
    for result in all_results:
        if result.summary:
            total_violations_direct += result.summary.violations  
            total_passes_direct += result.summary.passes
            
    print(f"Direct count - Total violations: {total_violations_direct}")
    print(f"Direct count - Total passes: {total_passes_direct}")
    
    # 5. Use violation summary method
    violation_summary = test_result_repo.get_violation_summary_by_project(project_id)
    print(f"\nViolation summary method:")
    print(f"Total violations: {violation_summary['total_violations']}")
    print(f"Total passes: {violation_summary['total_passes']}")
    print(f"Total tests: {violation_summary['total_tests']}")
    
    # 6. Use project manager statistics method
    stats_result = project_manager.get_project_statistics(project_id)
    if stats_result['success']:
        stats = stats_result['statistics']
        print(f"\nProject manager statistics:")
        print(f"Total violations: {stats['total_violations']}")
        print(f"Total passes: {stats['total_passes']}")
        print(f"Total tests: {stats['total_tests']}")
    else:
        print(f"Project manager error: {stats_result['error']}")
    
    # 7. List projects method (used by dashboard)
    projects_result = project_manager.list_projects()
    if projects_result['success']:
        for proj in projects_result['projects']:
            if proj['project_id'] == project_id:
                print(f"\nList projects method (dashboard):")
                print(f"Total violations: {proj['total_violations']}")
                print(f"Total tests: {proj['total_tests']}")
                break
    
    # 8. Analyze individual results
    print(f"\n=== Individual Test Results Analysis ===")
    unique_pages = set()
    for i, result in enumerate(all_results):
        unique_pages.add(result.page_id)
        violations = result.summary.violations if result.summary else 0
        passes = result.summary.passes if result.summary else 0
        print(f"Result {i+1}: Page {result.page_id}, Violations: {violations}, Passes: {passes}, Date: {result.test_date}")
    
    print(f"\nUnique pages with results: {len(unique_pages)}")
    
    # 9. Check for duplicate results per page
    page_result_counts = {}
    for result in all_results:
        if result.page_id not in page_result_counts:
            page_result_counts[result.page_id] = 0
        page_result_counts[result.page_id] += 1
    
    print(f"\nPage result counts:")
    for page_id, count in page_result_counts.items():
        print(f"  Page {page_id}: {count} results")
        if count > 1:
            print(f"    ⚠️  Multiple results for same page!")
    
    db_connection.disconnect()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python debug_statistics.py <project_id>")
        print("Use the project ID from your project page URL")
        sys.exit(1)
    
    project_id = sys.argv[1]
    debug_project_statistics(project_id)