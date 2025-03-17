# core/config_provider.py
import os
import yaml
import json
from typing import Dict, Any, Optional
from pathlib import Path

class ConfigurationProvider:
    """Centralized configuration provider for the system."""
    
    def __init__(self, base_path: Optional[str] = None):
        self.base_path = base_path or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.config_path = os.path.join(self.base_path, "config")
        self.configs = {}
        self._load_configs()
    
    def _load_configs(self) -> None:
        """Load all configuration files from the config directory."""
        if not os.path.exists(self.config_path):
            os.makedirs(self.config_path)
            
        for config_file in os.listdir(self.config_path):
            if config_file.endswith(('.yaml', '.yml', '.json')):
                config_name = os.path.splitext(config_file)[0]
                file_path = os.path.join(self.config_path, config_file)
                
                try:
                    if config_file.endswith(('.yaml', '.yml')):
                        with open(file_path, 'r') as f:
                            self.configs[config_name] = yaml.safe_load(f)
                    elif config_file.endswith('.json'):
                        with open(file_path, 'r') as f:
                            self.configs[config_name] = json.load(f)
                except Exception as e:
                    print(f"Error loading configuration file {config_file}: {e}")
    
    def get_config(self, name: str) -> Dict[str, Any]:
        """Get a specific configuration by name."""
        return self.configs.get(name, {})
    
    def get_value(self, config_name: str, key_path: str, default: Any = None) -> Any:
        """
        Get a specific configuration value using dot notation path.
        
        Example:
            get_value('llms', 'default.model', 'llama3')
        """
        config = self.configs.get(config_name, {})
        
        # Navigate through nested dictionary using the key path
        keys = key_path.split('.')
        value = config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
                
        return value
    
    def set_value(self, config_name: str, key_path: str, value: Any) -> None:
        """Set a specific configuration value using dot notation path."""
        if config_name not in self.configs:
            self.configs[config_name] = {}
            
        config = self.configs[config_name]
        
        # Navigate through nested dictionary using the key path
        keys = key_path.split('.')
        current = config
        
        # Navigate to the parent of the leaf node
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
            
        # Set the value at the leaf node
        current[keys[-1]] = value
    
    def save_config(self, name: str) -> bool:
        """Save a specific configuration to file."""
        if name not in self.configs:
            return False
            
        config_path = os.path.join(self.config_path, f"{name}.yaml")
        
        try:
            with open(config_path, 'w') as f:
                yaml.safe_dump(self.configs[name], f, default_flow_style=False)
            return True
        except Exception as e:
            print(f"Error saving configuration {name}: {e}")
            return False

# Singleton instance
_config_provider = None

def get_config_provider() -> ConfigurationProvider:
    """Get the singleton instance of the configuration provider."""
    global _config_provider
    if _config_provider is None:
        _config_provider = ConfigurationProvider()
    return _config_provider