"""
Test configuration and fixtures for the 4IR Backend Project Summit.
"""

import pytest
import os
import sys

# Add src directory to Python path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


@pytest.fixture
def sample_config():
    """Fixture providing sample configuration data."""
    return {
        "app_name": "4IR Backend Project Summit",
        "version": "1.0.0",
        "debug": False,
        "database": {
            "host": "localhost",
            "port": 5432,
            "name": "test_db"
        }
    }


@pytest.fixture
def temp_env_vars(monkeypatch):
    """Fixture for setting temporary environment variables."""
    test_vars = {
        "DEBUG": "True",
        "APP_NAME": "Test App",
        "LOG_LEVEL": "DEBUG"
    }
    
    for key, value in test_vars.items():
        monkeypatch.setenv(key, value)
    
    return test_vars