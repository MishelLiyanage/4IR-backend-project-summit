#!/usr/bin/env python3
"""
Main entry point for the 4IR Backend Project Summit application.
"""

import os
import sys
from dotenv import load_dotenv

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.app import Application


def main():
    """Main function to run the application."""
    # Load environment variables
    load_dotenv()
    
    # Create and run the application
    app = Application()
    app.run()


if __name__ == "__main__":
    main()