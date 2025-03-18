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
        
    def generate(self, 
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
            
            logger.debug(f"Received response from Ollama, length: {len(response.response)}")
            return response.response
            
        except Exception as e:
            error_msg = f"Error generating response with Ollama: {str(e)}"
            logger.error(error_msg)
            return f"Error: {error_msg}"
    
    def generate_structured(self, 
                          prompt: str,
                          response_format: Dict[str, Any],
                          system_prompt: Optional[str] = None,
                          temperature: Optional[float] = None,
                          max_tokens: Optional[int] = None) -> Dict[str, Any]:
        """
        Generate a structured response (JSON) using Ollama.
        Note: This is an extension method not in the base interface.
        
        Args:
            prompt: The prompt to send to the model
            response_format: Format specification (JSON schema)
            system_prompt: Optional system prompt
            temperature: Optional temperature override
            max_tokens: Optional max tokens override
            
        Returns:
            Parsed JSON response or error dict
        """
        # For models that support format directly like llama3
        format_supports_json = self.model in ["llama3", "mistral", "gemma"]
        
        if format_supports_json:
            # Use native format support if available
            options = {
                "temperature": temperature if temperature is not None else self.temperature,
                "num_predict": max_tokens if max_tokens is not None else self.max_tokens,
                "format": "json"
            }
            
            try:
                if system_prompt:
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
                
                # Parse JSON response
                return json.loads(response.response)
                
            except json.JSONDecodeError:
                logger.warning("Failed to parse JSON from response with format=json")
                # Fall through to the method below
        
        # For models without native format support,
        # or if the native support failed
        enhanced_prompt = (
            f"{prompt}\n\n"
            "Please provide your response in the following JSON format:\n"
            f"{json.dumps(response_format, indent=2)}\n\n"
            "Your response must be valid JSON."
        )
        
        enhanced_system = system_prompt
        if enhanced_system:
            enhanced_system += "\nYou must provide your response in valid JSON format."
        else:
            enhanced_system = "You must provide your response in valid JSON format."
        
        # Generate response
        raw_response = self.generate(
            prompt=enhanced_prompt,
            system_prompt=enhanced_system,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        # Try to parse JSON from the response
        try:
            # First try to find JSON in the response with open/close braces
            json_start = raw_response.find('{')
            json_end = raw_response.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = raw_response[json_start:json_end]
                return json.loads(json_str)
            else:
                # If no JSON structure found, try the whole response
                return json.loads(raw_response)
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from response: {e}")
            return {
                "error": "Failed to parse JSON from response",
                "raw_response": raw_response
            }