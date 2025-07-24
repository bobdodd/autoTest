"""
Configuration management for AutoTest application
"""

import os
import json
from pathlib import Path
from typing import Any, Dict, Optional


class Config:
    """Configuration manager with support for environment variables and config files"""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize configuration
        
        Args:
            config_file: Path to configuration file (optional)
        """
        self._config = self._load_default_config()
        
        # Load from config file if provided
        if config_file:
            self._load_config_file(config_file)
        else:
            # Try to load from default locations
            self._load_default_config_file()
        
        # Override with environment variables
        self._load_env_variables()
    
    def _load_default_config(self) -> Dict[str, Any]:
        """Load default configuration values"""
        return {
            'database': {
                'mongodb_uri': 'mongodb://localhost:27017/',
                'database_name': 'autotest',
                'connection_timeout': 5000
            },
            'server': {
                'host': '127.0.0.1',
                'port': 5000,
                'debug': True
            },
            'logging': {
                'level': 'INFO',
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                'file': None
            },
            'scraping': {
                'default_max_pages': 100,
                'default_depth_limit': 3,
                'request_delay': 1.0,
                'user_agent': 'AutoTest Accessibility Scanner/1.0'
            },
            'testing': {
                'timeout': 30,
                'screenshot_on_error': True,
                'custom_rules_enabled': True
            }
        }
    
    def _load_config_file(self, config_file: str) -> None:
        """Load configuration from JSON file"""
        config_path = Path(config_file)
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    file_config = json.load(f)
                self._merge_config(self._config, file_config)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not load config file {config_file}: {e}")
    
    def _load_default_config_file(self) -> None:
        """Try to load configuration from default locations"""
        possible_locations = [
            Path('config.json'),
            Path('autotest/config.json'),
            Path.home() / '.autotest' / 'config.json'
        ]
        
        for config_path in possible_locations:
            if config_path.exists():
                self._load_config_file(str(config_path))
                break
    
    def _load_env_variables(self) -> None:
        """Load configuration from environment variables"""
        env_mappings = {
            'AUTOTEST_MONGODB_URI': 'database.mongodb_uri',
            'AUTOTEST_DATABASE_NAME': 'database.database_name',
            'AUTOTEST_HOST': 'server.host',
            'AUTOTEST_PORT': 'server.port',
            'AUTOTEST_DEBUG': 'server.debug',
            'AUTOTEST_LOG_LEVEL': 'logging.level',
            'AUTOTEST_LOG_FILE': 'logging.file'
        }
        
        for env_var, config_key in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                # Convert string values to appropriate types
                if config_key.endswith('.port'):
                    value = int(value)
                elif config_key.endswith('.debug'):
                    value = value.lower() in ('true', '1', 'yes', 'on')
                
                self._set_nested_value(self._config, config_key, value)
    
    def _merge_config(self, base: Dict[str, Any], override: Dict[str, Any]) -> None:
        """Recursively merge configuration dictionaries"""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value
    
    def _set_nested_value(self, config: Dict[str, Any], key_path: str, value: Any) -> None:
        """Set a nested configuration value using dot notation"""
        keys = key_path.split('.')
        current = config
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = value
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation
        
        Args:
            key_path: Configuration key path (e.g., 'database.mongodb_uri')
            default: Default value if key not found
        
        Returns:
            Configuration value or default
        """
        keys = key_path.split('.')
        current = self._config
        
        try:
            for key in keys:
                current = current[key]
            return current
        except (KeyError, TypeError):
            return default
    
    def set(self, key_path: str, value: Any) -> None:
        """
        Set configuration value using dot notation
        
        Args:
            key_path: Configuration key path
            value: Value to set
        """
        self._set_nested_value(self._config, key_path, value)
    
    def get_all(self) -> Dict[str, Any]:
        """Get all configuration values"""
        return self._config.copy()