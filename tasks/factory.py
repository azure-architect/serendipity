# tasks/factory.py
import logging
from typing import Dict, Any, Optional, Type

from core.schema import TaskType
from .base import Task
from .contextualizer import Contextualizer
from .clarifier import Clarifier
from .categorizer import Categorizer
from .crystallizer import Crystallizer
from .connection_mapper import ConnectionMapper

logger = logging.getLogger(__name__)

class TaskFactory:
    """
    Factory for creating task instances based on task type.
    """
    
    def __init__(self, llm_factory):
        self.llm_factory = llm_factory
        self.task_registry = {
            TaskType.CONTEXTUALIZER: Contextualizer,
            TaskType.CLARIFIER: Clarifier,
            TaskType.CATEGORIZER: Categorizer,
            TaskType.CRYSTALLIZER: Crystallizer,
            TaskType.CONNECTION_MAPPER: ConnectionMapper
        }
        logger.info(f"TaskFactory initialized with {len(self.task_registry)} task types")
        
    def create_task(self, task_type: TaskType, config: Optional[Dict[str, Any]] = None) -> Task:
        """
        Create a task instance of the specified type.
        """
        if task_type not in self.task_registry:
            raise ValueError(f"Unknown task type: {task_type}")
            
        task_class = self.task_registry[task_type]
        task_instance = task_class(self.llm_factory, config)
        
        logger.debug(f"Created {task_type} task instance")
        return task_instance
    
    def register_task(self, task_type: TaskType, task_class: Type[Task]):
        """
        Register a new task type.
        """
        self.task_registry[task_type] = task_class
        logger.info(f"Registered new task type: {task_type}")