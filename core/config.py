# config.py
import json
import os
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

DEFAULT_CONFIG = {
    "llm": {
        "default_provider": "ollama",
        "ollama": {
            "base_url": "http://localhost:11434",
            "model_name": "llama3",
            "parameters": {
                "temperature": 0.7,
                "top_p": 0.9
            }
        }
    },
    "pipeline": {
        "default_stages": [
            "contextualizer",
            "clarifier",
            "categorizer",
            "crystallizer",
            "connector"
        ]
    },
    "tasks": {
        "contextualizer_config": {
            "llm_type": "ollama",
            "model_name": "llama3"
        },
        "clarifier_config": {
            "llm_type": "ollama",
            "model_name": "llama3"
        },
        "categorizer_config": {
            "llm_type": "ollama",
            "model_name": "llama3"
        },
        "crystallizer_config": {
            "llm_type": "ollama",
            "model_name": "llama3"
        },
        "connector_config": {
            "llm_type": "ollama",
            "model_name": "llama3"
        }
    },
    "logging": {
        "level": "INFO",
        "file": "serendipity.log"
    }
}

class Config:
    """
    Configuration management for the Serendipity project.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "config.json"
        self.config = DEFAULT_CONFIG.copy()
        
        self.load_config()
    
    def load_config(self) -> None:
        """
        Load configuration from file.
        """
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    file_config = json.load(f)
                
                # Merge configurations
                self._deep_update(self.config, file_config)
                logger.info(f"Loaded configuration from {self.config_path}")
        
        except Exception as e:
            logger.error(f"Error loading configuration: {str(e)}")
    
    def save_config(self) -> None:
        """
        Save current configuration to file.
        """
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            
            logger.info(f"Saved configuration to {self.config_path}")
        
        except Exception as e:
            logger.error(f"Error saving configuration: {str(e)}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value by key.
        Supports dot notation for nested keys, e.g., "llm.default_provider"
        """
        keys = key.split('.')
        value = self.config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value by key.
        Supports dot notation for nested keys, e.g., "llm.default_provider"
        """
        keys = key.split('.')
        config = self.config
        
        # Navigate to the appropriate nesting level
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # Set the value
        config[keys[-1]] = value
    
    def _deep_update(self, target: Dict, source: Dict) -> None:
        """
        Deep update a nested dictionary.
        """
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._deep_update(target[key], value)
            else:
                target[key] = value

# Singleton config instance
config = Config()

def get_config() -> Config:
    """
    Get the singleton config instance.
    """
    return config