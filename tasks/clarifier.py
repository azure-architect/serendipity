# tasks/clarifier.py
import logging
from typing import Dict, Any, Optional
import json

from core.schema import (
    ProcessedDocument, TaskResult, TaskType, 
    ClarificationData, ProcessingStage
)
from .base import Task

logger = logging.getLogger(__name__)

class Clarifier(Task):
    """
    Task for clarifying ambiguous or complex concepts within a document.
    Identifies and explains unclear terms, jargon, and complex ideas.
    """
    
    @property
    def task_type(self) -> TaskType:
        return TaskType.CLARIFIER
    
    def _build_prompt(self, document: ProcessedDocument) -> str:
        """Build clarifier-specific prompt."""
        prompt = (
            "You are a document clarifier. Your task is to identify and explain ambiguous or complex "
            "concepts in the following document.\n\n"
            f"Document content:\n{document.content}\n\n"
            "Please provide the following information in JSON format:\n"
            "1. complex_terms: A dictionary of complex terms or jargon and their explanations\n"
            "2. ambiguous_concepts: A list of concepts that may be unclear and explanations for them\n"
            "3. implicit_assumptions: Any assumptions made in the document that aren't explicitly stated\n"
            "4. clarification_notes: Any additional clarifications that would help understanding\n\n"
            "Format your response as valid JSON with these fields."
        )
        return prompt
    
    async def process(self, document: ProcessedDocument) -> TaskResult:
        """Process the document to clarify complex concepts."""
        logger.info(f"Clarifying document {document.id}")
        
        # Call LLM to clarify the document
        system_prompt = (
            "You are an expert at making complex content more accessible. Your task is to identify "
            "and explain difficult concepts, jargon, and ambiguous terms to improve document understanding."
        )
        
        llm_response = await self._call_llm(
            self._build_prompt(document),
            system_prompt
        )
        
        try:
            # Parse JSON response from LLM
            clarification_data = json.loads(llm_response)
            
            # Create clarification data
            clarification = ClarificationData(
                complex_terms=clarification_data.get("complex_terms", {}),
                ambiguous_concepts=clarification_data.get("ambiguous_concepts", []),
                implicit_assumptions=clarification_data.get("implicit_assumptions", []),
                clarification_notes=clarification_data.get("clarification_notes", "")
            )
            
            # Update document with clarification data
            document.clarification = clarification
            document.clarification_results = llm_response
            document.processing_stage = ProcessingStage.CLARIFIED.value
            
            # Create result
            result = TaskResult(
                task_type=self.task_type,
                success=True,
                document_id=str(document.id),
                result_data=clarification.model_dump(),
                processing_time=0  # Will be set by execute method
            )
            
            logger.info(f"Successfully clarified document {document.id}")
            return result
            
        except Exception as e:
            logger.error(f"Error parsing clarification results: {str(e)}")
            raise