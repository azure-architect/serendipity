# tasks/connector.py
import logging
from typing import Dict, Any, Optional, List
import json

from core.schema import (
    ProcessedDocument, TaskResult, TaskType, 
    ConnectionData, ProcessingStage, DocumentConnection
)
from .base import Task

logger = logging.getLogger(__name__)

class Connector(Task):
    """
    Task for connecting the current document with other documents or concepts.
    Identifies relationships, dependencies, and potential connections.
    """
    
    @property
    def task_type(self) -> TaskType:
        return TaskType.CONNECTOR
    
    def _build_prompt(self, document: ProcessedDocument, document_corpus: Optional[List[ProcessedDocument]] = None) -> str:
        """Build connector-specific prompt."""
        # Include processed document information
        doc_info = ""
        if hasattr(document, 'crystallization') and document.crystallization:
            summary = document.crystallization.executive_summary
            key_points = document.crystallization.key_points
            
            doc_info = (
                "Summary of current document:\n"
                f"{summary}\n\n"
                "Key points:\n"
                f"{', '.join(key_points)}\n\n"
            )
        
        # Include corpus information if available
        corpus_info = ""
        if document_corpus:
            corpus_info = "Related documents in the corpus:\n"
            for idx, doc in enumerate(document_corpus[:5]):  # Limit to 5 documents
                summary = ""
                if hasattr(doc, 'crystallization') and doc.crystallization:
                    summary = doc.crystallization.executive_summary
                corpus_info += f"Document {idx+1} (ID: {doc.id}): {summary}\n\n"
        
        prompt = (
            "You are a document connector. Your task is to identify relationships and connections "
            "between the current document and other concepts or documents.\n\n"
            f"Current document ID: {document.id}\n"
            f"{doc_info}"
            f"{corpus_info}"
            "Please provide the following information in JSON format:\n"
            "1. related_concepts: A list of concepts that connect to this document\n"
            "2. potential_references: Potential sources or references mentioned\n"
            "3. document_connections: A list of objects with 'document_id', 'connection_type', and 'strength' (1-10)\n"
            "4. dependency_chain: Any logical or conceptual dependencies this document has\n"
            "5. connection_notes: Additional notes about document connections\n\n"
            "Format your response as valid JSON with these fields."
        )
        return prompt
    
    async def process(self, document: ProcessedDocument, document_corpus: Optional[List[ProcessedDocument]] = None) -> TaskResult:
        """Process the document to create connections."""
        logger.info(f"Connecting document {document.id}")
        
        # Call LLM to create connections
        system_prompt = (
            "You are an expert at identifying relationships and connections between documents "
            "and concepts. Your task is to map out how documents relate to each other and to "
            "broader conceptual frameworks."
        )
        
        llm_response = await self._call_llm(
            self._build_prompt(document, document_corpus),
            system_prompt
        )
        
        try:
            # Parse JSON response from LLM
            connection_data = json.loads(llm_response)
            
            # Process document connections
            document_connections = []
            for conn in connection_data.get("document_connections", []):
                doc_connection = DocumentConnection(
                    document_id=conn.get("document_id", ""),
                    connection_type=conn.get("connection_type", "related"),
                    strength=conn.get("strength", 5)
                )
                document_connections.append(doc_connection)
            
            # Create connection data
            connection = ConnectionData(
                related_concepts=connection_data.get("related_concepts", []),
                potential_references=connection_data.get("potential_references", []),
                document_connections=document_connections,
                dependency_chain=connection_data.get("dependency_chain", []),
                connection_notes=connection_data.get("connection_notes", "")
            )
            
            # Update document with connection data
            document.connection = connection
            document.connection_results = llm_response
            document.processing_stage = ProcessingStage.CONNECTED.value
            
            # Create result
            result = TaskResult(
                task_type=self.task_type,
                success=True,
                document_id=str(document.id),
                result_data=connection.model_dump(),
                processing_time=0  # Will be set by execute method
            )
            
            logger.info(f"Successfully connected document {document.id}")
            return result
            
        except Exception as e:
            logger.error(f"Error parsing connection results: {str(e)}")
            raise