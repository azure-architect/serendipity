# implementations/tools/base_tool.py
from typing import Dict, Any, Optional
from core.interfaces import ITool, ILLM

class BaseTool(ITool):
    """Base class for all tools."""
    
    def __init__(self, config: Dict[str, Any], llm: Optional[ILLM] = None):
        self._config = config
        self._llm = llm
        self._name = "base_tool"
        self._description = "Base tool implementation"
    
    @property
    def name(self) -> str:
        """Get the tool's name."""
        return self._name
    
    @property
    def description(self) -> str:
        """Get the tool's description."""
        return self._description
    
    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the tool (to be implemented by subclasses)."""
        raise NotImplementedError("Subclasses must implement this method")
    
    def get_llm(self) -> ILLM:
        """Get the LLM used by this tool."""
        return self._llm