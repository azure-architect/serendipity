# tasks/crystallizer.py
import logging
from typing import Dict, Any, Optional
import json

from core.schema import (
    ProcessedDocument, TaskResult, TaskType, 
    CrystallizationData, ProcessingStage
)
from .base import Task

logger = logging.getLogger(__name__)

class Crystallizer(Task):
    """
    Task for crystallizing the key insights and information from a document.
    Creates summaries, extracts key points, and identifies core concepts.
    """
    
    @property
    def task_type(self) -> TaskType:
        return TaskType.CRYSTALLIZER
    
    def _build_prompt(self, document: ProcessedDocument) -> str:
        """Build crystallizer-specific prompt."""
        # Include contextual information if available
        context_info = ""
        if hasattr(document, 'contextualize') and document.contextualize:
            doc_type = document.contextualize.document_type or "document"
            context_info = f"This is a {doc_type}.\n\n"
        
        # Include clarification information if available
        clarification_info = ""
        if hasattr(document, 'clarification') and document.clarification:
            clarification_info = "Note that the following terms have specific meanings in this context:\n"
            for term, explanation in document.clarification.complex_terms.items():
                clarification_info += f"- {term}: {explanation}\n"
            clarification_info += "\n"
        
        prompt = (
            "You are a document crystallizer. Your task is to extract and organize the most important "
            f"information from the following {context_info}document.\n\n"
            f"Document content:\n{document.content}\n\n"
            f"{clarification_info}"
            "Please provide the following information in JSON format:\n"
            "1. executive_summary: A concise summary (3-5 sentences) of the document\n"
            "2. key_points: A list of the most important points from the document\n"
            "3. core_concepts: A list of central concepts discussed in the document\n"
            "4. conclusions: Main conclusions or takeaways from the document\n"
            "5. questions_raised: Important questions raised or left unanswered\n\n"
            "Format your response as valid JSON with these fields."
        )
        return prompt
    
    async def process(self, document: ProcessedDocument) -> TaskResult:
        """Process the document to crystallize key information."""
        logger.info(f"Crystallizing document {document.id}")
        
        # Call LLM to crystallize the document
        system_prompt = (
            "You are an expert at information synthesis and distillation. Your task is to identify "
            "and extract the most important content from documents, creating clear and concise "
            "summaries, key points, and conceptual frameworks."
        )
        
        llm_response = await self._call_llm(
            self._build_prompt(document),
            system_prompt
        )
        
        try:
            # Parse JSON response from LLM
            crystallization_data = json.loads(llm_response)
            
            # Create crystallization data
            crystallization = CrystallizationData(
                executive_summary=crystallization_data.get("executive_summary", ""),
                key_points=crystallization_data.get("key_points", []),
                core_concepts=crystallization_data.get("core_concepts", []),
                conclusions=crystallization_data.get("conclusions", []),
                questions_raised=crystallization_data.get("questions_raised", [])
            )
            
            # Update document with crystallization data
            document.crystallization = crystallization
            document.crystallization_results = llm_response
            document.processing_stage = ProcessingStage.CRYSTALLIZED.value
            
            # Create result
            result = TaskResult(
                task_type=self.task_type,
                success=True,
                document_id=str(document.id),
                result_data=crystallization.model_dump(),
                processing_time=0  # Will be set by execute method
            )
            
            logger.info(f"Successfully crystallized document {document.id}")
            return result
            
        except Exception as e:
            logger.error(f"Error parsing crystallization results: {str(e)}")
            raise