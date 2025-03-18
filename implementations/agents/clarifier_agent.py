# implementations/agents/clarifier_agent.py
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from core.interfaces import IAgent, ITask
from core.schema import ProcessedDocument, ProcessingStage, ProcessStage, ClarificationData

logger = logging.getLogger(__name__)

class ClarifierAgent(IAgent):
    """
    Agent responsible for the clarification stage of document processing.
    Implements the IAgent interface.
    """
    
    def __init__(self, config: Dict[str, Any], task: ITask):
        self._name = "Clarifier"
        self._description = "Clarifies and expands ambiguous aspects of documents"
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
        Process a document to clarify its content.
        
        Args:
            document: The document to process
            
        Returns:
            The processed document with clarification information added
        """
        logger.info(f"Agent {self._name} processing document {document.id}")
        
        # Record the current stage in history
        document.processing_history.append(
            ProcessStage(
                stage=document.processing_stage,
                timestamp=datetime.now().isoformat()
            )
        )
        
        # Update the current processing stage to CLARIFYING (in progress)
        document.processing_stage = ProcessingStage.CLARIFYING.value
        
        try:
            # Use the task to process the document
            logger.info(f"Calling task.process for document {document.id}")
            task_result = await self.task.process(document)
            
            if task_result.success:
                # Handle clarification notes - convert from list to string if needed
                clarification_notes = task_result.result_data.get("clarification_notes", "")
                if isinstance(clarification_notes, list):
                    clarification_notes = "\n".join(clarification_notes)
                
                # Create a proper ClarificationData object from the result data
                clarification_data = ClarificationData(
                    complex_terms=task_result.result_data.get("complex_terms", {}),
                    ambiguous_concepts=task_result.result_data.get("ambiguous_concepts", []),
                    implicit_assumptions=task_result.result_data.get("implicit_assumptions", []),
                    clarification_notes=clarification_notes
                )
                
                # Update document with clarification data
                document.clarification = clarification_data
                document.clarification_results = task_result.raw_response
                # Set to CLARIFIED (completed)
                document.processing_stage = ProcessingStage.CLARIFIED.value
                logger.info(f"Successfully clarified document {document.id}")
            else:
                # Record error
                document.processing_stage = ProcessingStage.ERROR.value
                logger.error(f"Failed to clarify document {document.id}: {task_result.error_message}")
            
            return document
            
        except Exception as e:
            # Handle exceptions
            document.processing_stage = ProcessingStage.ERROR.value
            logger.error(f"Error in {self._name} agent: {str(e)}", exc_info=True)
            return document
    
    def get_task(self) -> ITask:
        """Get the task associated with this agent."""
        return self.task