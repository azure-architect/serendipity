# factories/task_factory.py
from typing import Dict, Any, Type

from core.interfaces import ITask
from core.schema import TaskType
from implementations.tasks.base_task import BaseTask

class TaskFactory:
    """Factory for creating task instances."""
    
    def __init__(self, tool_factory):
        self.tool_factory = tool_factory
        self.tasks = {}
        self._register_default_tasks()
    
    def _register_default_tasks(self) -> None:
        """Register default task implementations."""
        # Import default tasks here to avoid circular imports
        from implementations.tasks.contextualizer_task import ContextualizerTask
        
        self.register_task(TaskType.CONTEXTUALIZER, ContextualizerTask)
        # Register other tasks as they become available
    
    def register_task(self, task_type: TaskType, task_class: Type[ITask]) -> None:
        """Register a new task type."""
        self.tasks[task_type] = task_class
    
    def create_task(self, task_type: TaskType, config: Dict[str, Any]) -> ITask:
        """Create a task instance based on type and configuration."""
        if task_type not in self.tasks:
            raise ValueError(f"Unknown task type: {task_type}")
        
        # Create tool for the task
        tool_name = config.get("tool", "text_processor")
        tool_config = config.get("tool_config", {})
        tool = self.tool_factory.create_tool(tool_name, tool_config)
        
        # Create task instance
        task_class = self.tasks[task_type]
        return task_class(config, tool)