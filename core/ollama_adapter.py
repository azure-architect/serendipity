# adapters/ollama_adapter.py
from typing import Dict, Any, Optional, List
import ollama
import os
from .base_adapter import LLMAdapter

class OllamaAdapter(LLMAdapter):
    """Adapter for direct communication with Ollama API."""
    
    def __init__(self):
        self.model = None
        self.client = None
        self.temperature = 0.7
        self.max_tokens = 1000
        
    def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the Ollama adapter with configuration."""
        self.model = config.get("model", "mistral:7b-instruct-fp16")
        self.temperature = config.get("temperature", 0.7)
        self.max_tokens = config.get("max_tokens", 1000)
        
        # Get base URL from environment variable or use default
        base_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
        
        # Create client with appropriate base URL
        self.client = ollama.Client(host=base_url)
    
    def set_config(self, config: Dict[str, Any]) -> None:
        """Update the adapter configuration."""
        self.model = config.get("model", self.model)
        self.temperature = config.get("temperature", self.temperature)
        self.max_tokens = config.get("max_tokens", self.max_tokens)
        
        # Update base URL if provided
        base_url = config.get("base_url", os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434"))
        if hasattr(self.client, 'host') and base_url != self.client.host:
            self.client = ollama.Client(host=base_url)
        
    def generate(self, 
                prompt: str, 
                system_prompt: Optional[str] = None,
                temperature: Optional[float] = None,
                max_tokens: Optional[int] = None,
                stop_sequences: Optional[List[str]] = None) -> str:
        """Generate a response using Ollama client."""
        # Use provided params or fall back to initialized values
        temp = temperature if temperature is not None else self.temperature
        tokens = max_tokens if max_tokens is not None else self.max_tokens
        
        options = {
            "temperature": temp,
            "num_predict": tokens
        }
        
        if stop_sequences:
            options["stop"] = stop_sequences
            
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
            
            return response.response
        except Exception as e:
            print(f"Error generating response with Ollama: {str(e)}")
            return f"Error generating response: {str(e)}"
    
    def close(self) -> None:
        """Close any open resources."""
        # The Ollama Client doesn't need explicit cleanup
        pass