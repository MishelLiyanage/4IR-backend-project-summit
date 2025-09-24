"""
Utility functions for the 4IR Backend Project Summit.
"""

import json
import os
from typing import Any, Dict, Optional


def load_config(config_path: str) -> Dict[str, Any]:
    """
    Load configuration from a JSON file.
    
    Args:
        config_path: Path to the configuration file
        
    Returns:
        Dictionary containing configuration data
        
    Raises:
        FileNotFoundError: If the config file doesn't exist
        json.JSONDecodeError: If the config file is not valid JSON
    """
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_config(config: Dict[str, Any], config_path: str) -> None:
    """
    Save configuration to a JSON file.
    
    Args:
        config: Configuration dictionary to save
        config_path: Path where to save the configuration file
    """
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def get_env_var(name: str, default: Optional[str] = None) -> Optional[str]:
    """
    Get environment variable with optional default value.
    
    Args:
        name: Environment variable name
        default: Default value if environment variable is not set
        
    Returns:
        Environment variable value or default
    """
    return os.getenv(name, default)