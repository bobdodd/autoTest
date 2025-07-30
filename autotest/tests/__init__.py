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