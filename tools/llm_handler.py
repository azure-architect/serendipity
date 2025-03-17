# tools/llm_handler.py
import os
import json
import yaml
import logging
from datetime import datetime
from core import create_adapter 

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Global variables
llm_adapter = None
LLM_CONFIGS = {}

def initialize_llm_configs(config_path, adapter_type="ollama"):
    """Initialize the global LLM configurations and adapter."""
    global LLM_CONFIGS, llm_adapter
    
    logger.info(f"Initializing LLM configs from: {config_path}")
    
    try:
        # Load config file
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)
            logger.info(f"Successfully loaded config from {config_path}")
        
        # Extract LLM configurations
        LLM_CONFIGS = config.get('llm_configs', {})
        if not LLM_CONFIGS:
            logger.warning(f"No LLM configurations found in {config_path}")
        else:
            logger.info(f"Loaded {len(LLM_CONFIGS)} LLM configurations: {list(LLM_CONFIGS.keys())}")
        
        # Create and initialize the adapter
        from core import create_adapter
        llm_adapter = create_adapter(adapter_type)
        logger.info(f"Created {adapter_type} adapter")
        
        # Initialize with first config or default
        default_config = LLM_CONFIGS.get('default', list(LLM_CONFIGS.values())[0] if LLM_CONFIGS else {})
        llm_adapter.initialize(default_config)
        logger.info(f"Initialized adapter with config: {default_config}")
        
    except Exception as e:
        logger.error(f"Error initializing LLM configurations: {e}")
        import traceback
        logger.error(traceback.format_exc())
        
        # Set up a fallback configuration
        LLM_CONFIGS = {'default': {
            'adapter': 'ollama',
            'model': 'llama3',
            'temperature': 0.7
        }}
        
        # Create a fallback adapter
        from core import create_adapter
        llm_adapter = create_adapter("ollama")
        llm_adapter.initialize(LLM_CONFIGS['default'])
        logger.info("Using fallback configuration")


def communicate_with_llm(prompt, config_name='default'):
    """Communicate with the LLM and get a response using the specified configuration."""
    global llm_adapter, LLM_CONFIGS
    
    print("========= COMMUNICATE WITH LLM FUNCTION CALLED =========")
    
    # Check if adapter is initialized
    if llm_adapter is None:
        logger.error("LLM adapter not initialized")
        return "ERROR: LLM adapter not initialized"
    
    # Get the configuration for the specified model
    config = LLM_CONFIGS.get(config_name, LLM_CONFIGS.get('default'))
    if not config:
        logger.error(f"No configuration found for '{config_name}' and no default available")
        return f"ERROR: No configuration found for '{config_name}'"
    
    logger.info(f"Using LLM config: {config_name} - Model: {config.get('model', 'unknown')}")
    
    try:
        # Set the adapter configuration for this request
        llm_adapter.set_config(config)
        
        # Use the adapter to get a response
        response = llm_adapter.generate(prompt)
        print(f"Received response from LLM, length: {len(response)}")
        return response
    except Exception as e:
        logger.error(f"Error communicating with LLM: {e}")
        return f"ERROR: Failed to communicate with LLM: {str(e)}"