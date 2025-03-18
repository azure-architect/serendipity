# tests/test_agent_factory.py
import asyncio
import sys 
from pathlib import Path
import logging
from typing import Dict, Any
from unittest.mock import MagicMock
sys.path.insert(0, str(Path(__file__).parent.parent))
from factories.llm_factory import LLMFactory
from factories.tool_factory import ToolFactory
from factories.task_factory import TaskFactory
from factories.agent_factory import AgentFactory
from core.schema import TaskType
from implementations.agents.contextualizer_agent import ContextualizerAgent
from implementations.agents.clarifier_agent import ClarifierAgent
from implementations.agents.categorizer_agent import CategorizerAgent
from implementations.agents.crystallizer_agent import CrystallizerAgent
from implementations.agents.connector_agent import ConnectorAgent

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("agent_factory_test")

async def test_agent_factory_registration():
    """Test that the AgentFactory correctly registers and creates all agent types."""
    logger.info("Testing agent factory registration")
    
    # Create mock task factory
    task_factory = MagicMock()
    
    # Create agent factory
    agent_factory = AgentFactory(task_factory)
    
    # Verify default registrations
    expected_agents = {
        "contextualizer": ContextualizerAgent,
        "clarifier": ClarifierAgent,
        "categorizer": CategorizerAgent,
        "crystallizer": CrystallizerAgent,
        "connector": ConnectorAgent
    }
    
    # Check if all expected agents are registered
    for agent_type, agent_class in expected_agents.items():
        if agent_type in agent_factory.agents:
            logger.info(f"✅ Agent '{agent_type}' is registered")
        else:
            logger.error(f"❌ Agent '{agent_type}' is NOT registered")
    
    # Test adding a custom agent
    class CustomAgent:
        def __init__(self, config, task):
            self.config = config
            self.task = task
    
    # Register custom agent
    agent_factory.register_agent("custom", CustomAgent)
    
    # Verify custom agent registration
    if "custom" in agent_factory.agents:
        logger.info(f"✅ Custom agent successfully registered")
    else:
        logger.error(f"❌ Custom agent registration failed")
    
    return "custom" in agent_factory.agents and all(agent_type in agent_factory.agents for agent_type in expected_agents)

async def test_agent_creation():
    """Test that the AgentFactory can create instances of all agent types."""
    logger.info("Testing agent instance creation")
    
    # Create real factories
    llm_factory = LLMFactory()
    tool_factory = ToolFactory(llm_factory)
    task_factory = TaskFactory(tool_factory)
    agent_factory = AgentFactory(task_factory)
    
    # Test configuration
    test_config: Dict[str, Any] = {
        "task_type": TaskType.CONTEXTUALIZER,
        "task_config": {
            "tool": "text_processor",
            "tool_config": {
                "llm_config": {
                    "adapter": "ollama",
                    "model": "mistral:7b-instruct-fp16",
                    "temperature": 0.7
                }
            }
        }
    }
    
    # Try to create instances of each agent type
    agent_types = ["contextualizer", "clarifier", "categorizer", "crystallizer", "connector"]
    success = True
    
    for agent_type in agent_types:
        try:
            agent = agent_factory.create_agent(agent_type, test_config)
            
            # Verify the agent has the expected name property
            if agent_type.capitalize() in agent.name:
                logger.info(f"✅ Successfully created agent of type '{agent_type}': {agent.name}")
            else:
                logger.warning(f"⚠️ Created agent of type '{agent_type}' but name doesn't match: {agent.name}")
            
        except Exception as e:
            logger.error(f"❌ Failed to create agent of type '{agent_type}': {str(e)}")
            success = False
    
    return success

if __name__ == "__main__":
    logger.info("Starting agent factory tests")
    
    # Run tests
    registration_result = asyncio.run(test_agent_factory_registration())
    creation_result = asyncio.run(test_agent_creation())
    
    if registration_result and creation_result:
        logger.info("✅ All agent factory tests passed successfully")
    else:
        logger.error("❌ Some agent factory tests failed")