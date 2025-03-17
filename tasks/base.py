# tasks/base.py
import logging
import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

from core.schema import ProcessedDocument, TaskResult, TaskType, LLMType, LLMConfig

logger = logging.getLogger(__name__)

class Task(ABC):
    """
    Base class for all document processing tasks.
    """
    
    def __init__(self, llm_factory, config: Optional[Dict[str, Any]] = None):
        self.llm_factory = llm_factory
        self.config = config or {}
        
        # Configure LLM
        self.llm_type = self.config.get('llm_type', LLMType.OLLAMA)
        self.model_name = self.config.get('model_name', 'llama3')
        self.llm_config = LLMConfig(
            llm_type=self.llm_type,
            model_name=self.model_name,
            parameters=self.config.get('llm_parameters', {})
        )
        
        # Initialize LLM
        self.llm = self.llm_factory.create_llm(self.llm_config)
        
        logger.debug(f"Initialized {self.__class__.__name__} with {self.llm_type} LLM: {self.model_name}")
    
    @property
    @abstractmethod
    def task_type(self) -> TaskType:
        """Return the type of this task."""
        pass
    
    @abstractmethod
    async def process(self, document: ProcessedDocument) -> TaskResult:
        """
        Process a document and return the result.
        This method must be implemented by subclasses.
        """
        pass
    
    async def _call_llm(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Helper method to call the LLM with a prompt.
        """
        try:
            response = await self.llm.generate(prompt, system_prompt)
            return response.content
        except Exception as e:
            logger.error(f"Error calling LLM: {str(e)}")
            raise
    
    def _build_prompt(self, document: ProcessedDocument) -> str:
        """
        Build a prompt for the LLM based on the document.
        Can be overridden by subclasses for specific prompt formats.
        """
        return f"Process the following document:\n\n{document.content}"
    
    async def execute(self, document: ProcessedDocument) -> TaskResult:
        """
        Execute the task on a document with timing and error handling.
        """
        logger.info(f"Executing {self.task_type} task on document {document.id}")
        
        start_time = asyncio.get_event_loop().time()
        
        try:
            result = await self.process(document)
            processing_time = asyncio.get_event_loop().time() - start_time
            result.processing_time = processing_time
            
            logger.info(f"Task {self.task_type} completed in {processing_time:.2f}s for document {document.id}")
            return result
            
        except Exception as e:
            processing_time = asyncio.get_event_loop().time() - start_time
            error_message = f"Error in {self.task_type} task: {str(e)}"
            logger.error(error_message)
            
            return TaskResult(
                task_type=self.task_type,
                success=False,
                document_id=str(document.id),
                error_message=error_message,
                processing_time=processing_time
            )