# llm/base.py
from abc import ABC, abstractmethod
import logging
from typing import Dict, Any, Optional

from core.schema import LLMResponse

logger = logging.getLogger(__name__)

class LLM(ABC):
    """
    Base class for LLM integrations.
    """
    
    def __init__(self, model_name: str, parameters: Dict[str, Any] = None):
        self.model_name = model_name
        self.parameters = parameters or {}
        logger.debug(f"Initialized {self.__class__.__name__} with model: {model_name}")
    
    @abstractmethod
    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> LLMResponse:
        """
        Generate a response from the LLM.
        """
        pass