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
Page Modification Testing Scenarios for AutoTest
Provides comprehensive page modification testing scenarios combining CSS and JavaScript.
"""

from .scenario_manager import ScenarioManager
from .modification_scenarios import ModificationScenarios
from .accessibility_scenarios import AccessibilityScenarios

__all__ = ['ScenarioManager', 'ModificationScenarios', 'AccessibilityScenarios']