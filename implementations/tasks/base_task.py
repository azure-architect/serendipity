# implementations/tasks/base_task.py
from typing import Dict, Any, Optional
from core.interfaces import ITask, ITool
from core.schema import ProcessedDocument, TaskResult, TaskType

class BaseTask(ITask):
    """Base class for all tasks."""
    
    def __init__(self, config: Dict[str, Any], tool: ITool):
        self.config = config
        self.tool = tool
        self._task_type = None  # Subclasses should override this
    
    @property
    def task_type(self) -> TaskType:
        """Get the type of this task."""
        if self._task_type is None:
            raise NotImplementedError("Subclasses must set _task_type")
        return self._task_type
    
    async def process(self, document: ProcessedDocument) -> TaskResult:
        """Process a document (to be implemented by subclasses)."""
        raise NotImplementedError("Subclasses must implement this method")
    
    def get_tool(self) -> ITool:
        """Get the tool used by this task."""
        return self.tool
    
    def build_prompt(self, document: ProcessedDocument) -> str:
        """Build a prompt for the document (to be implemented by subclasses)."""
        raise NotImplementedError("Subclasses must implement this method")