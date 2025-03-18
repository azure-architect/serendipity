# tests/test_full_pipeline.py
import sys
import os
import asyncio
import logging
from pathlib import Path
from uuid import uuid4

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

async def test_full_document_pipeline():
    """Test the complete document processing pipeline with all agents."""
    logger.info("=== Starting full pipeline test with all agents ===")
    
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
    
    # Create pipeline configuration with all agents
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
                            "model": "mistral:7b-instruct-fp16",
                            "temperature": 0.7
                        }
                    }
                }
            },
            {
                "type": "clarifier",
                "task_type": TaskType.CLARIFIER,
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
            {
                "type": "categorizer",
                "task_type": TaskType.CATEGORIZER,
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
            {
                "type": "crystallizer",
                "task_type": TaskType.CRYSTALLIZER,
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
            {
                "type": "connector",
                "task_type": TaskType.CONNECTOR,
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
        ]
    }
    
    # Create pipeline
    pipeline = Pipeline(agent_factory, pipeline_config)
    logger.info(f"Pipeline created with {len(pipeline_config['pipeline'])} agents")
    
    # Process document
    try:
        logger.info("Processing document through pipeline")
        processed_document = await pipeline.process_document(document)
        
        # Log results
        if processed_document.status == DocumentStatus.COMPLETED:
            logger.info(f"✅ Document processed: status={processed_document.status.value}")
        else:
            logger.error(f"❌ Document processing failed: {processed_document.status}")
            return None
            
        # Check results from each stage
        check_contextualization_results(processed_document)
        check_clarification_results(processed_document)
        check_categorization_results(processed_document)
        check_crystallization_results(processed_document)
        check_connection_results(processed_document)
            
        # Save processed document to file for inspection
        output_path = Path(__file__).parent / "test_output"
        output_path.mkdir(exist_ok=True)
        
        output_file = output_path / f"full_pipeline_document_{document_id}.json"
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
            
        logger.info(f"✅ Saved processed document to {output_file}")
        
        return processed_document

    except Exception as e:
        logger.error(f"❌ Error processing document: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def check_contextualization_results(document):
    """Check the results of the contextualizer agent."""
    if hasattr(document, 'contextualize') and document.contextualize:
        logger.info("✅ CONTEXTUALIZATION RESULTS:")
        
        if isinstance(document.contextualize, dict):
            # Handle dictionary access
            logger.info(f"✅ Document type: {document.contextualize.get('document_type')}")
            logger.info(f"✅ Topics: {document.contextualize.get('topics', [])}")
            logger.info(f"✅ Entities: {document.contextualize.get('entities', [])}")
            logger.info(f"✅ Related domains: {document.contextualize.get('related_domains', [])}")
        else:
            # Handle object attribute access
            logger.info(f"✅ Document type: {document.contextualize.document_type}")
            logger.info(f"✅ Topics: {document.contextualize.topics}")
            logger.info(f"✅ Entities: {document.contextualize.entities}")
            logger.info(f"✅ Related domains: {document.contextualize.related_domains}")
    else:
        logger.warning("❌ No contextualization data available")

def check_clarification_results(document):
    """Check the results of the clarifier agent."""
    if hasattr(document, 'clarification') and document.clarification:
        logger.info("✅ CLARIFICATION RESULTS:")
        
        if isinstance(document.clarification, dict):
            # Handle dictionary access
            logger.info(f"✅ Complex terms: {document.clarification.get('complex_terms', {})}")
            logger.info(f"✅ Ambiguous concepts: {document.clarification.get('ambiguous_concepts', [])}")
            logger.info(f"✅ Implicit assumptions: {document.clarification.get('implicit_assumptions', [])}")
        else:
            # Handle object attribute access
            logger.info(f"✅ Complex terms: {document.clarification.complex_terms}")
            logger.info(f"✅ Ambiguous concepts: {document.clarification.ambiguous_concepts}")
            logger.info(f"✅ Implicit assumptions: {document.clarification.implicit_assumptions}")
    else:
        logger.warning("❌ No clarification data available")

def check_categorization_results(document):
    """Check the results of the categorizer agent."""
    if hasattr(document, 'categorization') and document.categorization:
        logger.info("✅ CATEGORIZATION RESULTS:")
        
        if isinstance(document.categorization, dict):
            # Handle dictionary access
            logger.info(f"✅ Primary category: {document.categorization.get('primary_category')}")
            logger.info(f"✅ Secondary categories: {document.categorization.get('secondary_categories', [])}")
            logger.info(f"✅ Tags: {document.categorization.get('tags', [])}")
        else:
            # Handle object attribute access
            logger.info(f"✅ Primary category: {document.categorization.primary_category}")
            logger.info(f"✅ Secondary categories: {document.categorization.secondary_categories}")
            logger.info(f"✅ Tags: {document.categorization.tags}")
    else:
        logger.warning("❌ No categorization data available")

def check_crystallization_results(document):
    """Check the results of the crystallizer agent."""
    if hasattr(document, 'crystallization') and document.crystallization:
        logger.info("✅ CRYSTALLIZATION RESULTS:")
        
        if isinstance(document.crystallization, dict):
            # Handle dictionary access
            logger.info(f"✅ Executive summary: {document.crystallization.get('executive_summary')}")
            logger.info(f"✅ Key points: {document.crystallization.get('key_points', [])}")
            logger.info(f"✅ Core concepts: {document.crystallization.get('core_concepts', [])}")
            logger.info(f"✅ Conclusions: {document.crystallization.get('conclusions', [])}")
        else:
            # Handle object attribute access
            logger.info(f"✅ Executive summary: {document.crystallization.executive_summary}")
            logger.info(f"✅ Key points: {document.crystallization.key_points}")
            logger.info(f"✅ Core concepts: {document.crystallization.core_concepts}")
            logger.info(f"✅ Conclusions: {document.crystallization.conclusions}")
    else:
        logger.warning("❌ No crystallization data available")

def check_connection_results(document):
    """Check the results of the connector agent."""
    if hasattr(document, 'connection') and document.connection:
        logger.info("✅ CONNECTION RESULTS:")
        
        if isinstance(document.connection, dict):
            # Handle dictionary access
            logger.info(f"✅ Related concepts: {document.connection.get('related_concepts', [])}")
            logger.info(f"✅ Potential references: {document.connection.get('potential_references', [])}")
            logger.info(f"✅ Document connections: {document.connection.get('document_connections', [])}")
        else:
            # Handle object attribute access
            logger.info(f"✅ Related concepts: {document.connection.related_concepts}")
            logger.info(f"✅ Potential references: {document.connection.potential_references}")
            logger.info(f"✅ Document connections: {document.connection.document_connections}")
    else:
        logger.warning("❌ No connection data available")

async def test_contextualizer_only():
    """Test only the contextualizer agent to verify basic functionality."""
    logger.info("=== Starting test with only the contextualizer agent ===")
    
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
    
    # Create factory chain
    llm_factory = LLMFactory()
    tool_factory = ToolFactory(llm_factory)
    task_factory = TaskFactory(tool_factory)
    agent_factory = AgentFactory(task_factory)
    
    # Create pipeline configuration with only contextualizer
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
                            "model": "mistral:7b-instruct-fp16",
                            "temperature": 0.7
                        }
                    }
                }
            }
        ]
    }
    
    # Create pipeline
    pipeline = Pipeline(agent_factory, pipeline_config)
    
    # Process document
    try:
        processed_document = await pipeline.process_document(document)
        
        # Log results
        if processed_document.status == DocumentStatus.COMPLETED:
            logger.info(f"✅ Document processed with contextualizer only: status={processed_document.status.value}")
            check_contextualization_results(processed_document)
            return True
        else:
            logger.error(f"❌ Contextualizer test failed: {processed_document.status}")
            return False
    
    except Exception as e:
        logger.error(f"❌ Error in contextualizer test: {str(e)}")
        return False

async def test_clarifier_only():
    """Test only the clarifier agent to verify it works independently."""
    logger.info("=== Starting test with only the clarifier agent ===")
    
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
    
    # Create factory chain
    llm_factory = LLMFactory()
    tool_factory = ToolFactory(llm_factory)
    task_factory = TaskFactory(tool_factory)
    agent_factory = AgentFactory(task_factory)
    
    # Create pipeline configuration with only clarifier
    pipeline_config = {
        "pipeline": [
            {
                "type": "clarifier",
                "task_type": TaskType.CLARIFIER,
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
        ]
    }
    
    # Create pipeline
    pipeline = Pipeline(agent_factory, pipeline_config)
    
    # Process document
    try:
        processed_document = await pipeline.process_document(document)
        
        # Log results
        if processed_document.status == DocumentStatus.COMPLETED:
            logger.info(f"✅ Document processed with clarifier only: status={processed_document.status.value}")
            check_clarification_results(processed_document)
            return True
        else:
            logger.error(f"❌ Clarifier test failed: {processed_document.status}")
            return False
    
    except Exception as e:
        logger.error(f"❌ Error in clarifier test: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("Starting META Stack pipeline tests")
    
    # Run tests
    asyncio.run(test_contextualizer_only())
    asyncio.run(test_clarifier_only())
    asyncio.run(test_full_document_pipeline())
    
    logger.info("All tests completed")