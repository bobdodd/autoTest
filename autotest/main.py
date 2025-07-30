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
AutoTest - Automated Accessibility Testing Tool
Main application entry point
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from autotest.utils.config import Config
from autotest.utils.logger import setup_logger


def main():
    """Main application entry point"""
    # Setup configuration
    config = Config()
    
    # Setup logging
    logger = setup_logger(config.get('logging.level', 'INFO'))
    
    logger.info("Starting AutoTest application...")
    
    try:
        # Import and start web application
        from autotest.web.app import create_app
        
        app = create_app(config)
        
        # Get host and port from config
        host = config.get('server.host', '127.0.0.1')
        port = config.get('server.port', 5000)
        debug = config.get('server.debug', True)
        
        logger.info(f"Starting web server on {host}:{port}")
        app.run(host=host, port=port, debug=debug)
        
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
    except Exception as e:
        logger.error(f"Application error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()