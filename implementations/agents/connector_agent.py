# implementations/agents/connector_agent.py
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from core.interfaces import IAgent, ITask
from core.schema import ProcessedDocument, ProcessingStage, ProcessStage, ConnectionData, DocumentConnection

logger = logging.getLogger(__name__)

class ConnectorAgent(IAgent):
    """
    Agent responsible for the connection stage of document processing.
    Implements the IAgent interface.
    """
    
    def __init__(self, config: Dict[str, Any], task: ITask):
        self._name = "Connector"
        self._description = "Creates connections between documents and identifies relationships"
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
        Process a document to create connections.
        
        Args:
            document: The document to process
            
        Returns:
            The processed document with connection information added
        """
        logger.info(f"Agent {self._name} processing document {document.id}")
        
        # Record the current stage in history
        document.processing_history.append(
            ProcessStage(
                stage=document.processing_stage,
                timestamp=datetime.now().isoformat()
            )
        )
        
        # Update the current processing stage to CONNECTING (in progress)
        document.processing_stage = ProcessingStage.CONNECTING.value
        
        try:
            # Use the task to process the document
            logger.info(f"Calling task.process for document {document.id}")
            task_result = await self.task.process(document)
            
            if task_result.success:
                # Process document connections
                document_connections = []
                for conn in task_result.result_data.get("document_connections", []):
                    doc_connection = DocumentConnection(
                        document_id=conn.get("document_id", ""),
                        connection_type=conn.get("connection_type", "related"),
                        strength=conn.get("strength", 5)
                    )
                    document_connections.append(doc_connection)
                
                # Create a proper ConnectionData object from the result data
                connection_data = ConnectionData(
                    related_concepts=task_result.result_data.get("related_concepts", []),
                    potential_references=task_result.result_data.get("potential_references", []),
                    document_connections=document_connections,
                    dependency_chain=task_result.result_data.get("dependency_chain", []),
                    connection_notes=task_result.result_data.get("connection_notes", "")
                )
                
                # Update document with connection data
                document.connection = connection_data
                document.connection_results = task_result.raw_response
                # Set to CONNECTED (completed)
                document.processing_stage = ProcessingStage.CONNECTED.value
                logger.info(f"Successfully connected document {document.id}")
            else:
                # Record error
                document.processing_stage = ProcessingStage.ERROR.value
                logger.error(f"Failed to connect document {document.id}: {task_result.error_message}")
            
            return document
            
        except Exception as e:
            # Handle exceptions
            document.processing_stage = ProcessingStage.ERROR.value
            logger.error(f"Error in {self._name} agent: {str(e)}", exc_info=True)
            return document
    
    def get_task(self) -> ITask:
        """Get the task associated with this agent."""
        return self.task