# adapters/base_adapter.py
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List

class LLMAdapter(ABC):
    """Base adapter interface for LLM communication."""
    
    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the adapter with configuration."""
        pass
    
    @abstractmethod
    def set_config(self, config: Dict[str, Any]) -> None:
        """Update the adapter configuration."""
        pass
    
    @abstractmethod
    def generate(self, 
                prompt: str, 
                system_prompt: Optional[str] = None,
                temperature: float = 0.7,
                max_tokens: int = 1000,
                stop_sequences: Optional[List[str]] = None) -> str:
        """Generate a response from the LLM."""
        pass
    
    @abstractmethod
    def close(self) -> None:
        """Close any open resources or connections."""
        pass