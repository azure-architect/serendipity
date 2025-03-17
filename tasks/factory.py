# tasks/factory.py
class TaskFactory:
    """Factory for creating processing tasks."""
    
    def __init__(self, llm_factory=None):
        self.llm_factory = llm_factory
        self.tasks = {}
        
    def get_task(self, task_name):
        """Get a task instance by name."""
        # Return cached task if it exists
        if task_name in self.tasks:
            return self.tasks[task_name]
            
        # Create new task instance based on name
        if task_name == "contextualize":
            from .contextualizer import ContextualizerTask
            task = ContextualizerTask(self.llm_factory)
        elif task_name == "clarify":
            from .clarifier import ClarifierTask
            task = ClarifierTask(self.llm_factory)
        elif task_name == "categorize":
            from .categorizer import CategorizerTask
            task = CategorizerTask(self.llm_factory)
        elif task_name == "crystallize":
            from .crystallizer import CrystallizerTask
            task = CrystallizerTask(self.llm_factory)
        elif task_name == "connect":
            from .connector import ConnectorTask
            task = ConnectorTask(self.llm_factory)
        else:
            return None
            
        # Cache and return task
        self.tasks[task_name] = task
        return task
        
    def register_task(self, task_name, task_class):
        """Register a custom task implementation."""
        task = task_class(self.llm_factory)
        self.tasks[task_name] = task
        return task