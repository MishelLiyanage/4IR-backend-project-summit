"""
Integration tests for the 4IR Backend Project Summit application.
"""

import subprocess
import sys
import os
import pytest


class TestIntegration:
    """Integration test cases."""
    
    def test_main_script_runs(self):
        """Test that the main script can be executed without errors."""
        # Get the path to the main.py file
        main_path = os.path.join(os.path.dirname(__file__), '..', 'main.py')
        
        # Run the script with a timeout to prevent hanging
        try:
            result = subprocess.run(
                [sys.executable, main_path],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # The script should run without errors
            assert result.returncode == 0
            
            # Check that expected output is present
            assert "Welcome to 4IR Backend Project Summit!" in result.stdout
            assert "This application demonstrates clean architecture patterns." in result.stdout
            
        except subprocess.TimeoutExpired:
            pytest.fail("Main script execution timed out")
    
    def test_import_src_modules(self):
        """Test that all src modules can be imported successfully."""
        # Add src to path
        src_path = os.path.join(os.path.dirname(__file__), '..', 'src')
        sys.path.insert(0, src_path)
        
        try:
            # Import all main modules
            import app
            import utils
            
            # Basic checks
            assert hasattr(app, 'Application')
            assert hasattr(utils, 'load_config')
            assert hasattr(utils, 'save_config')
            assert hasattr(utils, 'get_env_var')
            
        except ImportError as e:
            pytest.fail(f"Failed to import src modules: {e}")
    
    def test_application_instantiation(self):
        """Test that Application class can be instantiated."""
        # Add src to path
        src_path = os.path.join(os.path.dirname(__file__), '..', 'src')
        sys.path.insert(0, src_path)
        
        from app import Application
        
        # Should be able to create an instance without errors
        app = Application()
        
        # Basic attribute checks
        assert app.config.app_name == "4IR Backend Project Summit"
        assert app.config.app_version == "1.0.0"
        assert isinstance(app.config.debug, bool)