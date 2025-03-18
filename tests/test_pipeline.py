# tests/test_pipeline.py
import sys
import os
import asyncio
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("pipeline_test")

from factories.llm_factory import LLMFactory
from factories.tool_factory import ToolFactory
from factories.task_factory import TaskFactory
from factories.agent_factory import AgentFactory
from core.pipeline import Pipeline
from core.schema import ProcessedDocument, DocumentStatus, TaskType
from uuid import uuid4

async def test_document_pipeline():
    """Test the complete document processing pipeline."""
    logger.info("Starting document pipeline test")
    
    # Create a test document
    document_id = str(uuid4())
    test_content = """
    I need to design a system that processes information through multiple specialized components.
    Each component should be able to use different AI models based on its specific requirements.
    Some components need larger context windows, while others benefit from faster response times.
    The whole system should be configurable through YAML files.
    """
    
    document = ProcessedDocument(
        id=document_id,
        content=test_content,
        status=DocumentStatus.PENDING
    )
    
    logger.info(f"Created test document with ID: {document_id}")
    
    # Create factory chain
    llm_factory = LLMFactory()
    tool_factory = ToolFactory(llm_factory)
    task_factory = TaskFactory(tool_factory)
    agent_factory = AgentFactory(task_factory)
    
    # Create pipeline configuration
# Create pipeline configuration
    pipeline_config = {
        "pipeline": [
            {
                "type": "contextualizer",
                "task_type": TaskType.CONTEXTUALIZER,
                "task_config": {
                    "tool": "text_processor",
                    "tool_config": {
                        "llm_config": {
                            "adapter": "ollama",
                            "model": "mistral:7b-instruct-fp16",  # Changed from "llama3" to match available model
                            "temperature": 0.7
                        }
                    }
                }
            }
        ]
    }
    
    # Create pipeline
    pipeline = Pipeline(agent_factory, pipeline_config)
    logger.info("Pipeline created with 1 agent")
    
    # Process document
    try:
        logger.info("Processing document through pipeline")
        processed_document = await pipeline.process_document(document)
        
        # Log results
        logger.info(f"Document processed: status={processed_document.status.value}")
        if processed_document.status != DocumentStatus.COMPLETED:
            logger.error(f"Document processing failed: {processed_document.status}")
            return None
            
        # Check contextualization results
        if hasattr(processed_document, 'contextualize') and processed_document.contextualize:
            logger.info(f"Document type: {processed_document.contextualize.document_type}")
            logger.info(f"Topics: {processed_document.contextualize.topics}")
            logger.info(f"Entities: {processed_document.contextualize.entities}")
            logger.info(f"Related domains: {processed_document.contextualize.related_domains}")
        else:
            logger.warning("No contextualization data available")
            
        # Save processed document to file for inspection
        output_path = Path(__file__).parent / "test_output"
        output_path.mkdir(exist_ok=True)
        
        output_file = output_path / f"processed_document_{document_id}.json"
        with open(output_file, "w") as f:
            import json
            from enum import Enum
            
            # Create a modified dump that handles enums
            serializable_data = processed_document.model_dump()
            # Convert any enum values to strings
            for key, value in list(serializable_data.items()):
                if isinstance(value, Enum):
                    serializable_data[key] = value.value
            
            json.dump(serializable_data, f, indent=2)
            
        logger.info(f"Saved processed document to {output_file}")
        
        return processed_document

    except Exception as e:
        logger.error(f"Error processing document: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    result = asyncio.run(test_document_pipeline())
    
    if result:
        logger.info("Pipeline test completed successfully")
    else:
        logger.error("Pipeline test failed")