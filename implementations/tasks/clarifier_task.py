# implementations/tasks/clarifier_task.py
import logging
from typing import Dict, Any, Optional
import json

from core.interfaces import ITask, ITool
from core.schema import ProcessedDocument, TaskResult, TaskType

logger = logging.getLogger(__name__)

class ClarifierTask(ITask):
    """
    Task for clarifying document content by identifying and explaining
    complex concepts, ambiguities, and implicit assumptions.
    Implements the ITask interface.
    """
    
    def __init__(self, config: Dict[str, Any], tool: ITool):
        self.config = config
        self.tool = tool
        self._task_type = TaskType.CLARIFIER
        logger.info(f"Initialized {self._task_type.value} task")
    
    @property
    def task_type(self) -> TaskType:
        """Get the type of this task."""
        return self._task_type
    
    async def process(self, document: ProcessedDocument) -> TaskResult:
        """
        Process a document to clarify its content.
        
        Args:
            document: The document to process
            
        Returns:
            TaskResult containing the processing result
        """
        logger.info(f"Clarifying document {document.id}")
        
        try:
            # Build the prompt for the document
            prompt = self.build_prompt(document)
            
            # Use the tool to process the document
            tool_inputs = {
                'text': document.content,
                'instruction': prompt
            }
            
            # Execute the tool
            logger.info(f"Executing tool for document {document.id}")
            tool_result = await self.tool.execute(tool_inputs)
            
            if not tool_result.get('success', False):
                error_msg = tool_result.get('error', 'Unknown error in text processor tool')
                logger.error(f"Tool execution failed: {error_msg}")
                return TaskResult(
                    task_type=self.task_type,
                    success=False,
                    document_id=str(document.id),
                    error_message=error_msg
                )
            
            # Parse the result
            logger.info(f"Got tool result for document {document.id}, parsing result")
            llm_response = tool_result.get('result', '')
            
            try:
                # Try to parse JSON from the response
                json_str = self._extract_json(llm_response)
                logger.info(f"Extracted JSON: {json_str[:100]}...")
                clarification_data = json.loads(json_str)
                
                # Create result
                result = TaskResult(
                    task_type=self.task_type,
                    success=True,
                    document_id=str(document.id),
                    result_data=clarification_data,
                    raw_response=llm_response
                )
                
                logger.info(f"Successfully clarified document {document.id}")
                return result
                
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing clarification results: {str(e)}")
                logger.error(f"Raw response: {llm_response}")
                return TaskResult(
                    task_type=self.task_type,
                    success=False,
                    document_id=str(document.id),
                    error_message=f"Failed to parse JSON response: {str(e)}",
                    raw_response=llm_response
                )
                
        except Exception as e:
            logger.error(f"Error in clarifier task: {str(e)}", exc_info=True)
            return TaskResult(
                task_type=self.task_type,
                success=False,
                document_id=str(document.id),
                error_message=str(e)
            )
    
    def get_tool(self) -> ITool:
        """Get the tool used by this task."""
        return self.tool
    
    def build_prompt(self, document: ProcessedDocument) -> str:
        """Build a prompt for the document."""
        # Include contextual information if available
        context_info = ""
        if hasattr(document, 'contextualize') and document.contextualize:
            doc_type = getattr(document.contextualize, 'document_type', None)
            topics = getattr(document.contextualize, 'topics', [])
            entities = getattr(document.contextualize, 'entities', [])
            
            if doc_type or topics or entities:
                context_info = "Based on previous contextual analysis:\n"
                if doc_type:
                    context_info += f"- Document type: {doc_type}\n"
                if topics:
                    context_info += f"- Topics: {', '.join(topics)}\n"
                if entities:
                    context_info += f"- Key entities: {', '.join(entities)}\n"
                context_info += "\n"
        
        prompt = (
            "You are a document clarifier. Your task is to identify and explain ambiguous or complex "
            "concepts in the following document.\n\n"
            f"{context_info}"
            f"Document content:\n{document.content}\n\n"
            "Please provide the following information in JSON format:\n"
            "1. complex_terms: A dictionary of complex terms or jargon and their explanations\n"
            "2. ambiguous_concepts: A list of concepts that may be unclear or need further explanation\n"
            "3. implicit_assumptions: A list of assumptions that are implied but not explicitly stated\n"
            "4. clarification_notes: Any additional notes that would help to clarify the document content\n\n"
            "Format your response as valid JSON with these fields."
        )
        return prompt
    
    def _extract_json(self, text: str) -> str:
        """
        Extract JSON from text that may contain additional content.
        """
        # Look for JSON between curly braces
        start_idx = text.find('{')
        end_idx = text.rfind('}')
        
        if start_idx >= 0 and end_idx > start_idx:
            return text[start_idx:end_idx+1]
        
        # If no JSON structure found, return the original text
        # (will likely cause a JSON parsing error, which is handled by the caller)
        return text