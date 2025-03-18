# main.py
import os
import sys
import asyncio
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
)
logger = logging.getLogger("main")

# Import necessary components
from factories.llm_factory import LLMFactory
from factories.tool_factory import ToolFactory
from factories.task_factory import TaskFactory
from factories.agent_factory import AgentFactory
from core.pipeline import Pipeline
from services.ingestion_service import IngestionService
from config.defaults import INGESTION_DEFAULTS

# Define default pipeline configuration
PIPELINE_DEFAULTS = [
    {
        "type": "contextualizer",
        "task_type": "CONTEXTUALIZER",
        "task_config": {
            "tool": "text_processor",
            "tool_config": {
                "llm_config": {
                    "adapter": "ollama",
                    "model": "mistral:7b-instruct-fp16"  # Use a model you have installed
                }
            }
        }
    },
    {
        "type": "clarifier",
        "task_type": "CLARIFIER",
        "task_config": {
            "tool": "text_processor",
            "tool_config": {
                "llm_config": {
                    "adapter": "ollama",
                    "model": "mistral:7b-instruct-fp16"  # Use a model you have installed
                }
            }
        }
    }
    # Add more pipeline stages as needed
]

async def setup_ingestion_service():
    """Set up and return the ingestion service."""
    # Create factory chain
    llm_factory = LLMFactory()
    tool_factory = ToolFactory(llm_factory)
    task_factory = TaskFactory(tool_factory)
    agent_factory = AgentFactory(task_factory)
    
    # Create pipeline with default configuration
    pipeline_config = {"pipeline": PIPELINE_DEFAULTS}
    pipeline = Pipeline(agent_factory, pipeline_config)
    logger.info("Created document processing pipeline")
    
    # Create ingestion service with configuration
    service = IngestionService(pipeline, INGESTION_DEFAULTS)
    logger.info("Created ingestion service")
    
    return service

async def main():
    """Main application entry point."""
    logger.info("Starting META Stack application")
    
    # Set up services
    ingestion_service = await setup_ingestion_service()
    
    # Start services
    await ingestion_service.start()
    logger.info("Services started successfully")
    
    try:
        # Keep the application running
        logger.info("Application running. Press Ctrl+C to exit.")
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        # Graceful shutdown
        logger.info("Shutting down...")
        await ingestion_service.stop()
        logger.info("Shutdown complete")

if __name__ == "__main__":
    asyncio.run(main())