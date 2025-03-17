# core/pipeline.py
import logging
import asyncio
from typing import List, Dict, Any, Optional

from core.schema import ProcessedDocument, DocumentStatus
from core.interfaces import IAgent
from factories.agent_factory import AgentFactory

logger = logging.getLogger(__name__)

class Pipeline:
    """Document processing pipeline using the factory pattern."""
    
    def __init__(self, agent_factory: AgentFactory, config: Optional[Dict[str, Any]] = None):
        self.agent_factory = agent_factory
        self.config = config or {}
        self.agents = []
        self._initialize_pipeline()
        
        logger.info("Document processing pipeline initialized")
    
    def _initialize_pipeline(self) -> None:
        """Initialize the pipeline with agents from configuration."""
        pipeline_config = self.config.get("pipeline", [])
        self.agents = self.agent_factory.create_agent_pipeline(pipeline_config)
        
        logger.info(f"Initialized pipeline with {len(self.agents)} agents")
    
    async def process_document(self, document: ProcessedDocument) -> ProcessedDocument:
        """Process a document through the pipeline of agents."""
        logger.info(f"Processing document {document.id} through pipeline")
        
        document.status = DocumentStatus.PROCESSING
        
        try:
            # Process document through each agent in sequence
            for agent in self.agents:
                logger.info(f"Processing document with agent: {agent.name}")
                document = await agent.process(document)
                
            # Mark document as completed
            document.status = DocumentStatus.COMPLETED
            logger.info(f"Successfully processed document {document.id} through pipeline")
            
        except Exception as e:
            logger.error(f"Error processing document {document.id}: {str(e)}")
            document.status = DocumentStatus.ERROR
            
        return document
    
    async def batch_process_documents(self, documents: List[ProcessedDocument]) -> List[ProcessedDocument]:
        """Process multiple documents through the pipeline."""
        logger.info(f"Batch processing {len(documents)} documents")
        
        tasks = []
        for document in documents:
            tasks.append(self.process_document(document))
        
        return await asyncio.gather(*tasks)