# implementations/agents/crystallizer_agent.py
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from core.interfaces import IAgent, ITask
from core.schema import ProcessedDocument, ProcessingStage, ProcessStage, CrystallizationData

logger = logging.getLogger(__name__)

class CrystallizerAgent(IAgent):
    """
    Agent responsible for the crystallization stage of document processing.
    Implements the IAgent interface.
    """
    
    def __init__(self, config: Dict[str, Any], task: ITask):
        self._name = "Crystallizer"
        self._description = "Distills documents into their most valuable and actionable form"
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
    
# implementations/agents/crystallizer_agent.py
    async def process(self, document: ProcessedDocument) -> ProcessedDocument:
        logger.info(f"Agent {self._name} processing document {document.id}")
        
        # Record the current stage in history
        document.processing_history.append(
            ProcessStage(
                stage=document.processing_stage,
                timestamp=datetime.now().isoformat()
            )
        )
        
        # Update the current processing stage to CRYSTALLIZING (in progress)
        document.processing_stage = ProcessingStage.CRYSTALLIZING.value
        
        try:
            # Use the task to process the document
            logger.info(f"Calling task.process for document {document.id}")
            task_result = await self.task.process(document)
            
            if task_result.success:
                # Handle executive_summary - convert from list to string if needed
                executive_summary = task_result.result_data.get("executive_summary", "")
                if isinstance(executive_summary, list):
                    executive_summary = " ".join(executive_summary)
                
                # Handle potential list-to-string conversions for any string fields
                key_points = task_result.result_data.get("key_points", [])
                core_concepts = task_result.result_data.get("core_concepts", [])
                conclusions = task_result.result_data.get("conclusions", [])
                questions_raised = task_result.result_data.get("questions_raised", [])
                
                # Ensure all list items are strings
                key_points = [str(item) for item in key_points]
                core_concepts = [str(item) for item in core_concepts]
                conclusions = [str(item) for item in conclusions]
                questions_raised = [str(item) for item in questions_raised]
                
                # Create a proper CrystallizationData object from the result data
                crystallization_data = CrystallizationData(
                    executive_summary=executive_summary,
                    key_points=key_points,
                    core_concepts=core_concepts,
                    conclusions=conclusions,
                    questions_raised=questions_raised
                )
                
                # Update document with crystallization data
                document.crystallization = crystallization_data
                document.crystallization_results = task_result.raw_response
                # Set to CRYSTALLIZED (completed)
                document.processing_stage = ProcessingStage.CRYSTALLIZED.value
                logger.info(f"Successfully crystallized document {document.id}")
            else:
                # Record error
                document.processing_stage = ProcessingStage.ERROR.value
                logger.error(f"Failed to crystallize document {document.id}: {task_result.error_message}")
            
            return document
            
        except Exception as e:
            # Handle exceptions
            document.processing_stage = ProcessingStage.ERROR.value
            logger.error(f"Error in {self._name} agent: {str(e)}", exc_info=True)
            return document
    
    def get_task(self) -> ITask:
        """Get the task associated with this agent."""
        return self.task