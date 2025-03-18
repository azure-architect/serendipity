# Example script to run the ingestion service (you can save as run_ingestion.py)
import asyncio
import logging
from factories.llm_factory import LLMFactory
from factories.tool_factory import ToolFactory
from factories.task_factory import TaskFactory
from factories.agent_factory import AgentFactory
from core.pipeline import Pipeline
from services.ingestion_service import IngestionService

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("ingestion_runner")

async def main():
    # Create factory chain
    logger.info("Creating component factories")
    llm_factory = LLMFactory()
    tool_factory = ToolFactory(llm_factory)
    task_factory = TaskFactory(tool_factory)
    agent_factory = AgentFactory(task_factory)
    
    # Configure pipeline
    pipeline_config = {
        "pipeline": [
            {
                "type": "contextualizer",
                "task_type": "CONTEXTUALIZER",
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
            },
            # Additional agent configurations
            # ...
        ]
    }
    
    # Create pipeline
    logger.info("Creating processing pipeline")
    pipeline = Pipeline(agent_factory, pipeline_config)
    
    # Create and start ingestion service
    logger.info("Starting ingestion service")
    ingestion_service = IngestionService(pipeline)
    await ingestion_service.start()
    
    try:
        # Keep the service running
        logger.info("Ingestion service running. Press Ctrl+C to stop.")
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        # Graceful shutdown
        logger.info("Shutting down...")
        await ingestion_service.stop()
        logger.info("Shutdown complete")

if __name__ == "__main__":
    asyncio.run(main())