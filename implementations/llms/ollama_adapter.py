# implementations/llms/ollama_adapter.py
from typing import Dict, Any, Optional, List
import ollama
import os
import json
import logging
from core.interfaces import ILLM

logger = logging.getLogger(__name__)

class OllamaAdapter(ILLM):
    """Adapter for Ollama LLM models using the Ollama Python library."""
    
    def __init__(self):
        self.model = None
        self.client = None
        self.temperature = 0.7
        self.max_tokens = 1000
        self.base_url = None
        logger.debug("OllamaAdapter instance created")
        
    def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the Ollama adapter with configuration."""
        logger.info(f"Initializing OllamaAdapter with config: {config}")
        
        self.model = config.get("model", "llama3")
        self.temperature = config.get("temperature", 0.7)
        self.max_tokens = config.get("max_tokens", 1000)
        
        # Get base URL from config or environment variable
        self.base_url = config.get("base_url", 
                            os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434"))
        
        # Create client with appropriate base URL
        try:
            self.client = ollama.Client(host=self.base_url)
            logger.info(f"Connected to Ollama at {self.base_url} with model {self.model}")
        except Exception as e:
            logger.error(f"Failed to initialize Ollama client: {str(e)}")
            raise
    
    def set_config(self, config: Dict[str, Any]) -> None:
        """Update the adapter configuration."""
        logger.debug(f"Updating OllamaAdapter config: {config}")
        
        # Update configuration values
        self.model = config.get("model", self.model)
        self.temperature = config.get("temperature", self.temperature)
        self.max_tokens = config.get("max_tokens", self.max_tokens)
        
        # Update base URL if provided and different from current
        new_base_url = config.get("base_url", self.base_url)
        if new_base_url != self.base_url:
            self.base_url = new_base_url
            try:
                self.client = ollama.Client(host=self.base_url)
                logger.info(f"Reconnected to Ollama at {self.base_url}")
            except Exception as e:
                logger.error(f"Failed to update Ollama client: {str(e)}")
                raise
        
    async def generate(self, 
                prompt: str, 
                system_prompt: Optional[str] = None,
                temperature: Optional[float] = None,
                max_tokens: Optional[int] = None,
                stop_sequences: Optional[List[str]] = None) -> str:
        """Generate a response using Ollama client."""
        if not self.client:
            error_msg = "Ollama client not initialized"
            logger.error(error_msg)
            return f"Error: {error_msg}"
            
        # Use provided parameters or fall back to instance values
        temp = temperature if temperature is not None else self.temperature
        tokens = max_tokens if max_tokens is not None else self.max_tokens
        
        # Prepare options for the request
        options = {
            "temperature": temp,
            "num_predict": tokens
        }
        
        if stop_sequences:
            options["stop"] = stop_sequences
            
        logger.debug(f"Generating with model={self.model}, temp={temp}, tokens={tokens}")
        
        try:
            # Use appropriate generation method based on parameters
            if system_prompt:
                logger.debug(f"Using system prompt: {system_prompt[:50]}...")
                response = self.client.generate(
                    model=self.model,
                    prompt=prompt,
                    system=system_prompt,
                    options=options
                )
            else:
                response = self.client.generate(
                    model=self.model,
                    prompt=prompt,
                    options=options
                )
            
            logger.debug(f"Received response from Ollama")
            return response.response
            
        except Exception as e:
            error_msg = f"Error generating response with Ollama: {str(e)}"
            logger.error(error_msg)
            return f"Error: {error_msg}"