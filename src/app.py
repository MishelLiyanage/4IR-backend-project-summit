"""
Main application module for the 4IR Backend Project Summit.
"""

import logging
import os
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class Application:
    """Main application class."""
    
    def __init__(self):
        """Initialize the application."""
        self.name = "4IR Backend Project Summit"
        self.version = "1.0.0"
        self.debug = os.getenv('DEBUG', 'False').lower() == 'true'
        
        logger.info(f"Initializing {self.name} v{self.version}")
    
    def run(self):
        """Run the main application logic."""
        logger.info("Starting application...")
        
        try:
            self._setup()
            self._main_loop()
        except KeyboardInterrupt:
            logger.info("Application interrupted by user")
        except Exception as e:
            logger.error(f"Application error: {e}")
            if self.debug:
                raise
        finally:
            self._cleanup()
    
    def _setup(self):
        """Setup application resources."""
        logger.info("Setting up application resources...")
        # Add your setup logic here
        pass
    
    def _main_loop(self):
        """Main application logic."""
        logger.info("Running main application logic...")
        
        # Example: Simple greeting
        print(f"Welcome to {self.name}!")
        print("This is a basic Python project template.")
        print("You can extend this by adding your own modules and functionality.")
        
        # Add your main application logic here
        
    def _cleanup(self):
        """Cleanup application resources."""
        logger.info("Cleaning up application resources...")
        # Add your cleanup logic here
        pass