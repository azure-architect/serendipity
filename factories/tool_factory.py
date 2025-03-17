# factories/tool_factory.py
from typing import Dict, Any, Type

from core.interfaces import ITool
from implementations.tools.base_tool import BaseTool

class ToolFactory:
    """Factory for creating tool instances."""
    
    def __init__(self, llm_factory):
        self.llm_factory = llm_factory
        self.tools = {}
        self._register_default_tools()
    
    def _register_default_tools(self) -> None:
        """Register default tool implementations."""
        # Import default tools here to avoid circular imports
        from implementations.tools.text_processor import TextProcessor
        from implementations.tools.embeddings_tool import EmbeddingsTool
        
        self.register_tool("text_processor", TextProcessor)
        self.register_tool("embeddings", EmbeddingsTool)
    
    def register_tool(self, name: str, tool_class: Type[ITool]) -> None:
        """Register a new tool type."""
        self.tools[name] = tool_class
    
    def create_tool(self, name: str, config: Dict[str, Any]) -> ITool:
        """Create a tool instance based on name and configuration."""
        if name not in self.tools:
            raise ValueError(f"Unknown tool: {name}")
        
        # Create LLM for the tool if specified
        llm = None
        if "llm_config" in config:
            llm_config = config["llm_config"]
            llm = self.llm_factory.create_llm(llm_config)
        
        # Create tool instance
        tool_class = self.tools[name]
        return tool_class(config, llm)