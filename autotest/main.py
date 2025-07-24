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