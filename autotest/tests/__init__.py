"""
AutoTest Testing Module
Comprehensive test suite for the AutoTest accessibility testing application
"""

import sys
import os
from pathlib import Path

# Add the autotest package to the Python path
test_dir = Path(__file__).parent
project_root = test_dir.parent.parent
sys.path.insert(0, str(project_root))

# Test configuration
TEST_DATABASE_NAME = "autotest_test"
TEST_MONGODB_URI = "mongodb://localhost:27017/autotest_test"

# Test fixtures directory
FIXTURES_DIR = test_dir / "fixtures"
SAMPLE_DATA_DIR = FIXTURES_DIR / "sample_data"