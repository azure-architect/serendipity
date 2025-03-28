# implementations/tasks/contextualizer_task.py
import logging
from typing import Dict, Any, Optional
import json

from core.interfaces import ITask, ITool
from core.schema import ProcessedDocument, TaskResult, TaskType, ContextualizationData, ProcessingStage

logger = logging.getLogger(__name__)

class ContextualizerTask(ITask):
    """
    Task for contextualizing document content by extracting metadata.
    Implements the ITask interface.
    """
    
    def __init__(self, config: Dict[str, Any], tool: ITool):
        self.config = config
        self.tool = tool
        self._task_type = TaskType.CONTEXTUALIZER
        logger.info(f"Initialized {self._task_type.value} task")
    
    @property
    def task_type(self) -> TaskType:
        """Get the type of this task."""
        return self._task_type
    
    async def process(self, document: ProcessedDocument) -> TaskResult:
        """Process document with schema-based document type validation."""
        logger.info(f"Contextualizing document {document.id}")
        
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
                # Extract JSON from the response
                json_str = self._extract_json(llm_response)
                logger.info(f"Extracted JSON: {json_str[:100]}...")
                context_data = json.loads(json_str)
                
                # Validate document type against schema
                from core.schema import DocumentType
                
                # Get the document type from response or default to "note"
                doc_type_str = context_data.get("document_type", "note").lower()
                
                # Validate against DocumentType enum
                try:
                    # Try to match exactly with enum
                    doc_type = DocumentType(doc_type_str)
                except ValueError:
                    # If not a valid match, default to NOTE
                    doc_type = DocumentType.NOTE
                    logger.warning(f"Invalid document type '{doc_type_str}', defaulting to '{doc_type.value}'")
                    context_data["document_type"] = doc_type.value
                
                # Create contextualization data with validated document type
                contextualization = ContextualizationData(
                    document_type=doc_type.value,
                    topics=context_data.get("topics", []),
                    entities=context_data.get("entities", []),
                    related_domains=context_data.get("related_domains", []),
                    context_notes=context_data.get("context_notes")
                )
                
                # Create result
                result = TaskResult(
                    task_type=self.task_type,
                    success=True,
                    document_id=str(document.id),
                    result_data=contextualization.model_dump(),
                    raw_response=llm_response
                )
                
                logger.info(f"Successfully contextualized document {document.id} as {doc_type.value}")
                return result
                
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing contextualization results: {str(e)}")
                logger.error(f"Raw response: {llm_response}")
                return TaskResult(
                    task_type=self.task_type,
                    success=False,
                    document_id=str(document.id),
                    error_message=f"Failed to parse JSON response: {str(e)}",
                    raw_response=llm_response
                )
                
        except Exception as e:
            logger.error(f"Error in contextualizer task: {str(e)}", exc_info=True)
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
        """Build contextualizer-specific prompt with document types from schema."""
        from core.schema import DocumentType
        
        # Get all valid document types from the enum
        valid_types = [t.value for t in DocumentType]
        type_choices = ", ".join(valid_types)
        
        prompt = (
            "You are a document contextualizer. Your task is to analyze the following document "
            "and extract key contextual information.\n\n"
            f"Document content:\n{document.content}\n\n"
            "Please provide the following information in JSON format:\n"
            f"1. document_type: The type of document (must be one of: {type_choices})\n"
            "2. topics: A list of main topics covered in the document\n"
            "3. entities: A list of key entities mentioned (people, organizations, products, etc.)\n"
            "4. related_domains: A list of knowledge domains related to this document\n"
            "5. context_notes: Any additional contextual information that might be relevant\n\n"
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