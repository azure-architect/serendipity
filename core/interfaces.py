# core/interfaces.py (Complete)
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List

from core.schema import ProcessedDocument, TaskResult, TaskType

class ILLM(ABC):
    """Interface for Language Model providers."""
    
    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the LLM with configuration."""
        pass
    
    @abstractmethod
    async def generate(self, 
                prompt: str, 
                system_prompt: Optional[str] = None,
                temperature: Optional[float] = None,
                max_tokens: Optional[int] = None,
                stop_sequences: Optional[List[str]] = None) -> str:
        """Generate a response from the LLM."""
        pass
    
    @abstractmethod
    def set_config(self, config: Dict[str, Any]) -> None:
        """Update the LLM configuration."""
        pass

class ITool(ABC):
    """Interface for tools used in document processing."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Get the tool's name."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Get the tool's description."""
        pass
    
    @abstractmethod
    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the tool with the provided inputs."""
        pass
    
    @abstractmethod
    def get_llm(self) -> ILLM:
        """Get the LLM used by this tool."""
        pass

class ITask(ABC):
    """Interface for document processing tasks."""
    
    @property
    @abstractmethod
    def task_type(self) -> TaskType:
        """Get the type of this task."""
        pass
    
    @abstractmethod
    async def process(self, document: ProcessedDocument) -> TaskResult:
        """Process a document and return the result."""
        pass
    
    @abstractmethod
    def get_tool(self) -> ITool:
        """Get the tool used by this task."""
        pass
    
    @abstractmethod
    def build_prompt(self, document: ProcessedDocument) -> str:
        """Build a prompt for the document."""
        pass

class IAgent(ABC):
    """Interface for processing agents."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Get the agent's name."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Get the agent's description."""
        pass
    
    @abstractmethod
    async def process(self, document: ProcessedDocument) -> ProcessedDocument:
        """Process a document and return the updated document."""
        pass
    
    @abstractmethod
    def get_task(self) -> ITask:
        """Get the task associated with this agent."""
        pass