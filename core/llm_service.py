# core/llm_service.py
import logging
from typing import Dict, Any, Optional

from core.interfaces import ILLM
from factories.llm_factory import LLMFactory
from core.config_provider import get_config_provider

logger = logging.getLogger(__name__)

class LLMService:
    """Centralized service for LLM operations."""
    
    def __init__(self):
        self.llm_factory = LLMFactory()
        self.config_provider = get_config_provider()
        self.llm_instances = {}
        self.default_llm_name = "default"
        self._initialize_llms()
    
    def _initialize_llms(self) -> None:
        """Initialize LLM instances from configuration."""
        llm_configs = self.config_provider.get_config("llms")
        
        # Set default LLM name if configured
        if "default" in llm_configs:
            self.default_llm_name = llm_configs.get("default")
            
        # Create LLM instances for each configuration
        for name, config in llm_configs.items():
            if name != "default" and isinstance(config, dict):
                try:
                    self.llm_instances[name] = self.llm_factory.create_llm(config)
                    logger.info(f"Initialized LLM: {name}")
                except Exception as e:
                    logger.error(f"Error initializing LLM {name}: {e}")
    
    def get_llm(self, name: Optional[str] = None) -> ILLM:
        """Get an LLM instance by name."""
        llm_name = name or self.default_llm_name
        
        # If requested LLM doesn't exist, try the default
        if llm_name not in self.llm_instances:
            if llm_name != self.default_llm_name and self.default_llm_name in self.llm_instances:
                logger.warning(f"LLM {llm_name} not found, using default")
                return self.llm_instances[self.default_llm_name]
            else:
                # If no default exists, create a fallback LLM
                logger.warning(f"Creating fallback LLM instance")
                fallback_config = {"adapter": "ollama", "model": "llama3"}
                return self.llm_factory.create_llm(fallback_config)
        
        return self.llm_instances[llm_name]
    
    async def generate(self, 
                      prompt: str, 
                      llm_name: Optional[str] = None,
                      system_prompt: Optional[str] = None,
                      temperature: Optional[float] = None,
                      max_tokens: Optional[int] = None) -> str:
        """Generate text using the specified LLM."""
        llm = self.get_llm(llm_name)
        
        try:
            return await llm.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens
            )
        except Exception as e:
            logger.error(f"Error generating text with LLM {llm_name}: {e}")
            return f"Error: {str(e)}"

# Singleton instance
_llm_service = None

def get_llm_service() -> LLMService:
    """Get the singleton instance of the LLM service."""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service

async def generate_text(prompt: str, 
                        llm_name: Optional[str] = None,
                        system_prompt: Optional[str] = None,
                        temperature: Optional[float] = None,
                        max_tokens: Optional[int] = None) -> str:
    """
    Convenience function for generating text with an LLM.
    This provides a simple function-based interface for basic use cases.
    """
    service = get_llm_service()
    return await service.generate(
        prompt=prompt,
        llm_name=llm_name,
        system_prompt=system_prompt,
        temperature=temperature,
        max_tokens=max_tokens
    )