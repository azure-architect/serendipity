# llm/ollama.py
import logging
import json
import aiohttp
import time
from typing import Dict, Any, Optional

from core.schema import LLMResponse
from .base import LLM

logger = logging.getLogger(__name__)

class OllamaLLM(LLM):
    """
    Integration with Ollama LLM API.
    """
    
    def __init__(self, model_name: str, parameters: Dict[str, Any] = None):
        super().__init__(model_name, parameters)
        self.base_url = parameters.get("base_url", "http://localhost:11434")
        self.api_url = f"{self.base_url}/api/generate"
        
        # Set default parameters if not provided
        self.default_params = {
            "temperature": 0.7,
            "top_p": 0.9,
            "top_k": 40,
            "num_predict": 1024,
            "stream": False
        }
        
        # Merge default parameters with provided parameters
        self.params = {**self.default_params, **self.parameters}
        logger.info(f"Initialized Ollama LLM with model: {model_name}, API URL: {self.api_url}")
    
    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> LLMResponse:
        """
        Generate a response from Ollama.
        """
        logger.debug(f"Generating response with model: {self.model_name}")
        
        request_data = {
            "model": self.model_name,
            "prompt": prompt,
            **self.params
        }
        
        if system_prompt:
            request_data["system"] = system_prompt
        
        start_time = time.time()
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.api_url, json=request_data) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"Ollama API error: {response.status} - {error_text}")
                    
                    response_data = await response.json()
                    
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Extract token usage if available
            token_usage = {
                "total_tokens": response_data.get("total_tokens", 0),
                "prompt_tokens": response_data.get("prompt_tokens", 0),
                "completion_tokens": response_data.get("total_tokens", 0) - response_data.get("prompt_tokens", 0)
            }
            
            return LLMResponse(
                content=response_data.get("response", ""),
                raw_response=response_data,
                processing_time=processing_time,
                token_usage=token_usage
            )
            
        except Exception as e:
            logger.error(f"Error calling Ollama API: {str(e)}")
            raise