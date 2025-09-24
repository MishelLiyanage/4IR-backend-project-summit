"""
Tests for utility functions.
"""

import json
import os
import tempfile
import pytest
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils import load_config, save_config, get_env_var


class TestConfigFunctions:
    """Test cases for configuration functions."""
    
    def test_save_and_load_config(self, sample_config):
        """Test saving and loading configuration."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_path = f.name
        
        try:
            # Save config
            save_config(sample_config, config_path)
            
            # Verify file exists
            assert os.path.exists(config_path)
            
            # Load config
            loaded_config = load_config(config_path)
            
            # Verify loaded config matches original
            assert loaded_config == sample_config
            
        finally:
            # Cleanup
            if os.path.exists(config_path):
                os.unlink(config_path)
    
    def test_load_config_file_not_found(self):
        """Test loading configuration from non-existent file."""
        with pytest.raises(FileNotFoundError):
            load_config("non_existent_file.json")
    
    def test_load_config_invalid_json(self):
        """Test loading configuration from invalid JSON file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("invalid json content")
            config_path = f.name
        
        try:
            with pytest.raises(json.JSONDecodeError):
                load_config(config_path)
        finally:
            os.unlink(config_path)
    
    def test_save_config_creates_directory(self, sample_config):
        """Test that save_config creates directories if they don't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = os.path.join(temp_dir, "subdir", "config.json")
            
            save_config(sample_config, config_path)
            
            assert os.path.exists(config_path)
            
            # Verify content
            loaded_config = load_config(config_path)
            assert loaded_config == sample_config


class TestEnvironmentVariables:
    """Test cases for environment variable functions."""
    
    def test_get_env_var_existing(self, temp_env_vars):
        """Test getting an existing environment variable."""
        result = get_env_var("DEBUG")
        assert result == "True"
    
    def test_get_env_var_non_existing_no_default(self):
        """Test getting a non-existing environment variable without default."""
        result = get_env_var("NON_EXISTENT_VAR")
        assert result is None
    
    def test_get_env_var_non_existing_with_default(self):
        """Test getting a non-existing environment variable with default."""
        result = get_env_var("NON_EXISTENT_VAR", "default_value")
        assert result == "default_value"
    
    def test_get_env_var_existing_over_default(self, temp_env_vars):
        """Test that existing environment variable takes precedence over default."""
        result = get_env_var("DEBUG", "False")
        assert result == "True"  # Should return the env var value, not the default