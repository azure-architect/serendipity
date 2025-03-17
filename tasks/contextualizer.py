# tasks/contextualizer.py
import logging
from typing import Dict, Any, Optional
import json

from core.schema import (
    ProcessedDocument, TaskResult, TaskType, 
    ContextualizationData, ProcessingStage
)
from .base import Task

logger = logging.getLogger(__name__)

class Contextualizer(Task):
    """
    Task for contextualizing document content.
    Extracts document type, topics, entities, and related domains.
    """
    
    @property
    def task_type(self) -> TaskType:
        return TaskType.CONTEXTUALIZER
    
    def _build_prompt(self, document: ProcessedDocument) -> str:
        """Build contextualizer-specific prompt."""
        prompt = (
            "You are a document contextualizer. Your task is to analyze the following document "
            "and extract key contextual information.\n\n"
            f"Document content:\n{document.content}\n\n"
            "Please provide the following information in JSON format:\n"
            "1. document_type: The type of document (e.g., article, research paper, email, etc.)\n"
            "2. topics: A list of main topics covered in the document\n"
            "3. entities: A list of key entities mentioned (people, organizations, products, etc.)\n"
            "4. related_domains: A list of knowledge domains related to this document\n"
            "5. context_notes: Any additional contextual information that might be relevant\n\n"
            "Format your response as valid JSON with these fields."
        )
        return prompt
    
    async def process(self, document: ProcessedDocument) -> TaskResult:
        """Process the document to extract contextual information."""
        logger.info(f"Contextualizing document {document.id}")
        
        # Call LLM to contextualize the document
        system_prompt = (
            "You are an expert document analyst. Your task is to extract key contextual "
            "information from documents to help categorize and connect them with related content."
        )
        
        llm_response = await self._call_llm(
            self._build_prompt(document),
            system_prompt
        )
        
        try:
            # Parse JSON response from LLM
            context_data = json.loads(llm_response)
            
            # Create contextualization data
            contextualization = ContextualizationData(
                document_type=context_data.get("document_type"),
                topics=context_data.get("topics", []),
                entities=context_data.get("entities", []),
                related_domains=context_data.get("related_domains", []),
                context_notes=context_data.get("context_notes")
            )
            
            # Update document with contextualization data
            document.contextualize = contextualization
            document.contextualize_results = llm_response
            document.processing_stage = ProcessingStage.CONTEXTUALIZED.value
            
            # Create result
            result = TaskResult(
                task_type=self.task_type,
                success=True,
                document_id=str(document.id),
                result_data=contextualization.model_dump(),
                processing_time=0  # Will be set by execute method
            )
            
            logger.info(f"Successfully contextualized document {document.id}")
            return result
            
        except Exception as e:
            logger.error(f"Error parsing contextualization results: {str(e)}")
            raise