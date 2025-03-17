# factories/llm_factory.py
from typing import Dict, Any, Type

from core.interfaces import ILLM
from implementations.llms.ollama_adapter import OllamaAdapter

class LLMFactory:
    """Factory for creating LLM instances."""
    
    def __init__(self):
        self.adapters = {
            "ollama": OllamaAdapter,
            # Add other adapter types as needed
        }
    
    def register_adapter(self, name: str, adapter_class: Type[ILLM]) -> None:
        """Register a new adapter type."""
        self.adapters[name] = adapter_class
    
    def create_llm(self, config: Dict[str, Any]) -> ILLM:
        """Create an LLM instance based on configuration."""
        adapter_type = config.get("adapter", "ollama").lower()
        
        if adapter_type not in self.adapters:
            raise ValueError(f"Unknown adapter type: {adapter_type}")
        
        adapter_class = self.adapters[adapter_type]
        adapter = adapter_class()
        adapter.initialize(config)
        
        return adapter