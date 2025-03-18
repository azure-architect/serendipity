# implementations/agents/categorizer_agent.py
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from core.interfaces import IAgent, ITask
from core.schema import ProcessedDocument, ProcessingStage, ProcessStage, CategorizationData

logger = logging.getLogger(__name__)

class CategorizerAgent(IAgent):
    """
    Agent responsible for the categorization stage of document processing.
    Implements the IAgent interface.
    """
    
    def __init__(self, config: Dict[str, Any], task: ITask):
        self._name = "Categorizer"
        self._description = "Categorizes documents into relevant taxonomies and classifications"
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
        Process a document to categorize its content.
        
        Args:
            document: The document to process
            
        Returns:
            The processed document with categorization information added
        """
        logger.info(f"Agent {self._name} processing document {document.id}")
        
        # Record the current stage in history
        document.processing_history.append(
            ProcessStage(
                stage=document.processing_stage,
                timestamp=datetime.now().isoformat()
            )
        )
        
        # Update the current processing stage to CATEGORIZING (in progress)
        document.processing_stage = ProcessingStage.CATEGORIZING.value
        
        try:
            # Use the task to process the document
            logger.info(f"Calling task.process for document {document.id}")
            task_result = await self.task.process(document)
            
            if task_result.success:
                # Create a proper CategorizationData object from the result data
                categorization_data = CategorizationData(
                    primary_category=task_result.result_data.get("primary_category"),
                    secondary_categories=task_result.result_data.get("secondary_categories", []),
                    tags=task_result.result_data.get("tags", []),
                    relevance_scores=task_result.result_data.get("relevance_scores", {}),
                    classification_notes=task_result.result_data.get("classification_notes", "")
                )
                
                # Update document with categorization data
                document.categorization = categorization_data
                document.categorization_results = task_result.raw_response
                # Set to CATEGORIZED (completed)
                document.processing_stage = ProcessingStage.CATEGORIZED.value
                logger.info(f"Successfully categorized document {document.id}")
            else:
                # Record error
                document.processing_stage = ProcessingStage.ERROR.value
                logger.error(f"Failed to categorize document {document.id}: {task_result.error_message}")
            
            return document
            
        except Exception as e:
            # Handle exceptions
            document.processing_stage = ProcessingStage.ERROR.value
            logger.error(f"Error in {self._name} agent: {str(e)}", exc_info=True)
            return document
    
    def get_task(self) -> ITask:
        """Get the task associated with this agent."""
        return self.task