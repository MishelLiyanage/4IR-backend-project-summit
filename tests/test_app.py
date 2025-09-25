"""
Tests for the main application module.
"""

import pytest
from unittest.mock import patch, MagicMock
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from app import Application


class TestApplication:
    """Test cases for the Application class."""
    
    def test_application_init(self):
        """Test application initialization."""
        app = Application()
        
        assert app.config.app_name == "4IR Backend Project Summit"
        assert app.config.app_version == "1.0.0"
        assert isinstance(app.config.debug, bool)
    
    def test_application_init_with_debug_env(self, temp_env_vars):
        """Test application initialization with debug environment variable."""
        app = Application()
        
        # Should be True due to temp_env_vars fixture setting DEBUG=True
        assert app.config.debug is True
    
    @patch('src.app.logger')
    def test_setup_method(self, mock_logger):
        """Test the _setup method."""
        app = Application()
        app._setup()
        
        mock_logger.info.assert_called_with("Setting up application resources...")
    
    @patch('src.app.logger')
    def test_cleanup_method(self, mock_logger):
        """Test the _cleanup method."""
        app = Application()
        app._cleanup()
        
        mock_logger.info.assert_called_with("Cleaning up application resources...")
    
    @patch('src.app.Application._cleanup')
    @patch('src.app.Application._main_loop')
    @patch('src.app.Application._setup') 
    @patch('src.app.logger')
    def test_run_method_success(self, mock_logger, mock_setup, mock_main_loop, mock_cleanup):
        """Test successful run method execution."""
        app = Application()
        app.run()
        
        mock_setup.assert_called_once()
        mock_main_loop.assert_called_once()
        mock_cleanup.assert_called_once()
        mock_logger.info.assert_called_with("Starting application...")
    
    @patch('src.app.Application._cleanup')
    @patch('src.app.Application._main_loop')
    @patch('src.app.Application._setup')
    @patch('src.app.logger')
    def test_run_method_keyboard_interrupt(self, mock_logger, mock_setup, mock_main_loop, mock_cleanup):
        """Test run method with keyboard interrupt."""
        mock_main_loop.side_effect = KeyboardInterrupt()
        
        app = Application()
        app.run()
        
        mock_setup.assert_called_once()
        mock_main_loop.assert_called_once()
        mock_cleanup.assert_called_once()
        mock_logger.info.assert_any_call("Application interrupted by user")
    
    @patch('src.app.Application._cleanup')
    @patch('src.app.Application._main_loop')
    @patch('src.app.Application._setup')
    @patch('src.app.logger')
    def test_run_method_exception_debug_mode(self, mock_logger, mock_setup, mock_main_loop, mock_cleanup):
        """Test run method with exception in debug mode."""
        mock_main_loop.side_effect = ValueError("Test error")
        
        app = Application()
        app.config.debug = True
        
        with pytest.raises(ValueError):
            app.run()
        
        mock_setup.assert_called_once()
        mock_main_loop.assert_called_once()
        mock_cleanup.assert_called_once()
        mock_logger.error.assert_called_with("Application error: Test error")