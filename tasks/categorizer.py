# tasks/categorizer.py
import logging
from typing import Dict, Any, Optional
import json

from core.schema import (
    ProcessedDocument, TaskResult, TaskType, 
    CategorizationData, ProcessingStage
)
from .base import Task

logger = logging.getLogger(__name__)

class Categorizer(Task):
    """
    Task for categorizing documents into relevant taxonomies and classifications.
    Assigns tags, categories, and relevance scores to the document.
    """
    
    @property
    def task_type(self) -> TaskType:
        return TaskType.CATEGORIZER
    
    def _build_prompt(self, document: ProcessedDocument) -> str:
        """Build categorizer-specific prompt."""
        # Include contextual information if available
        context_info = ""
        if hasattr(document, 'contextualize') and document.contextualize:
            topics = document.contextualize.topics or []
            entities = document.contextualize.entities or []
            domains = document.contextualize.related_domains or []
            
            context_info = (
                "Based on previous analysis, the document has these characteristics:\n"
                f"- Topics: {', '.join(topics)}\n"
                f"- Entities: {', '.join(entities)}\n"
                f"- Related domains: {', '.join(domains)}\n\n"
            )
        
        prompt = (
            "You are a document categorizer. Your task is to assign meaningful categories, tags, "
            "and classifications to the following document.\n\n"
            f"Document content:\n{document.content}\n\n"
            f"{context_info}"
            "Please provide the following information in JSON format:\n"
            "1. primary_category: The main category this document belongs to\n"
            "2. secondary_categories: A list of secondary categories\n"
            "3. tags: A list of relevant tags for the document\n"
            "4. relevance_scores: A dictionary mapping key domains to relevance scores (0-10)\n"
            "5. classification_notes: Any additional notes about the categorization\n\n"
            "Format your response as valid JSON with these fields."
        )
        return prompt
    
    async def process(self, document: ProcessedDocument) -> TaskResult:
        """Process the document to categorize it."""
        logger.info(f"Categorizing document {document.id}")
        
        # Call LLM to categorize the document
        system_prompt = (
            "You are an expert document classifier. Your task is to analyze document content "
            "and assign the most appropriate categories, tags, and relevance scores to help "
            "with organization and retrieval."
        )
        
        llm_response = await self._call_llm(
            self._build_prompt(document),
            system_prompt
        )
        
        try:
            # Parse JSON response from LLM
            categorization_data = json.loads(llm_response)
            
            # Create categorization data
            categorization = CategorizationData(
                primary_category=categorization_data.get("primary_category"),
                secondary_categories=categorization_data.get("secondary_categories", []),
                tags=categorization_data.get("tags", []),
                relevance_scores=categorization_data.get("relevance_scores", {}),
                classification_notes=categorization_data.get("classification_notes", "")
            )
            
            # Update document with categorization data
            document.categorization = categorization
            document.categorization_results = llm_response
            document.processing_stage = ProcessingStage.CATEGORIZED.value
            
            # Create result
            result = TaskResult(
                task_type=self.task_type,
                success=True,
                document_id=str(document.id),
                result_data=categorization.model_dump(),
                processing_time=0  # Will be set by execute method
            )
            
            logger.info(f"Successfully categorized document {document.id}")
            return result
            
        except Exception as e:
            logger.error(f"Error parsing categorization results: {str(e)}")
            raise