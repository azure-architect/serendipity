# factories/agent_factory.py
from typing import Dict, Any, List, Type

from core.interfaces import IAgent
from implementations.agents.contextualizer_agent import ContextualizerAgent

class AgentFactory:
    """Factory for creating agent instances."""
    
    def __init__(self, task_factory):
        self.task_factory = task_factory
        self.agents = {
            "contextualizer": ContextualizerAgent,
            # Add other agent types as needed
        }
    
    def register_agent(self, agent_type: str, agent_class: Type[IAgent]) -> None:
        """Register a new agent type."""
        self.agents[agent_type] = agent_class
    
    def create_agent(self, agent_type: str, config: Dict[str, Any]) -> IAgent:
        """Create an agent instance based on type and configuration."""
        if agent_type not in self.agents:
            raise ValueError(f"Unknown agent type: {agent_type}")
        
        # Create task for the agent
        task_type = config.get("task_type", "contextualizer")
        task_config = config.get("task_config", {})
        task = self.task_factory.create_task(task_type, task_config)
        
        # Create agent instance
        agent_class = self.agents[agent_type]
        return agent_class(config, task)
    
    def create_agent_pipeline(self, pipeline_config: List[Dict[str, Any]]) -> List[IAgent]:
        """Create a pipeline of agents based on configuration."""
        agents = []
        for agent_config in pipeline_config:
            agent_type = agent_config.get("type")
            if not agent_type:
                raise ValueError("Agent configuration missing 'type' field")
            
            agent = self.create_agent(agent_type, agent_config)
            agents.append(agent)
        
        return agents