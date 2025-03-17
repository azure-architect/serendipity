# llm/factory.py
import logging
from typing import Dict, Optional

from core.schema import LLMType, LLMConfig
from .base import LLM
from .ollama import OllamaLLM

logger = logging.getLogger(__name__)

class LLMFactory:
    """
    Factory for creating LLM instances.
    """
    
    def __init__(self):
        self.llm_registry = {
            LLMType.OLLAMA: OllamaLLM,
            # Add other LLM types as needed
        }
        logger.info(f"LLMFactory initialized with {len(self.llm_registry)} LLM types")
    
    def create_llm(self, config: LLMConfig) -> LLM:
        """
        Create an LLM instance based on the provided configuration.
        """
        if config.llm_type not in self.llm_registry:
            raise ValueError(f"Unsupported LLM type: {config.llm_type}")
        
        llm_class = self.llm_registry[config.llm_type]
        llm = llm_class(config.model_name, config.parameters)
        
        logger.debug(f"Created {config.llm_type} LLM instance with model: {config.model_name}")
        return llm
    
    def register_llm(self, llm_type: LLMType, llm_class):
        """
        Register a new LLM type.
        """
        self.llm_registry[llm_type] = llm_class
        logger.info(f"Registered new LLM type: {llm_type}")