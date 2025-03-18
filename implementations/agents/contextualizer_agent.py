# implementations/agents/contextualizer_agent.py
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from core.interfaces import IAgent, ITask
from core.schema import ProcessedDocument, ProcessingStage, ProcessStage

logger = logging.getLogger(__name__)

class ContextualizerAgent(IAgent):
    """
    Agent responsible for the contextualization stage of document processing.
    Implements the IAgent interface.
    """
    
    def __init__(self, config: Dict[str, Any], task: ITask):
        self._name = "Contextualizer"
        self._description = "Analyzes documents and extracts contextual information"
        self.config = config
        self.task = task
        logger.info(f"Initialized {self._name} agent")
    
    @property
    def name(self) -> str:
        """Get the agent's name."""
        return self._name
    
    @property
    def description(self) -> str:
        """Get the agent's description."""
        return self._description
    
    async def process(self, document: ProcessedDocument) -> ProcessedDocument:
        """
        Process a document to extract contextual information.
        
        Args:
            document: The document to process
            
        Returns:
            The processed document with contextual information added
        """
        logger.info(f"Agent {self._name} processing document {document.id}")
        
        # Record the current stage in history
        document.processing_history.append(
            ProcessStage(
                stage=document.processing_stage,
                timestamp=datetime.now().isoformat()
            )
        )
        
        # Update the current processing stage
        document.processing_stage = ProcessingStage.CONTEXTUALIZING.value
        
        try:
            # Use the task to process the document
            task_result = await self.task.process(document)
            
            if task_result.success:
                # Update document with contextualization data
                document.contextualize = task_result.result_data
                document.contextualize_results = task_result.raw_response
                document.processing_stage = ProcessingStage.CONTEXTUALIZED.value
                logger.info(f"Successfully contextualized document {document.id}")
            else:
                # Record error
                document.processing_stage = ProcessingStage.ERROR.value
                logger.error(f"Failed to contextualize document {document.id}: {task_result.error_message}")
            
            return document
            
        except Exception as e:
            # Handle exceptions
            document.processing_stage = ProcessingStage.ERROR.value
            logger.error(f"Error in {self._name} agent: {str(e)}")
            return document
    
    def get_task(self) -> ITask:
        """Get the task associated with this agent."""
        return self.task