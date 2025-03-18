# implementations/tasks/crystallizer_task.py
import logging
from typing import Dict, Any, Optional
import json

from core.interfaces import ITask, ITool
from core.schema import ProcessedDocument, TaskResult, TaskType, CrystallizationData

logger = logging.getLogger(__name__)

class CrystallizerTask(ITask):
    """
    Task for crystallizing document content.
    Extracts key insights, summaries, and core concepts.
    Implements the ITask interface.
    """
    
    def __init__(self, config: Dict[str, Any], tool: ITool):
        self.config = config
        self.tool = tool
        self._task_type = TaskType.CRYSTALLIZER
        logger.info(f"Initialized {self._task_type.value} task")
    
    @property
    def task_type(self) -> TaskType:
        """Get the type of this task."""
        return self._task_type
    
    async def process(self, document: ProcessedDocument) -> TaskResult:
        """
        Process a document to crystallize its content.
        
        Args:
            document: The document to process
            
        Returns:
            TaskResult containing the processing result
        """
        logger.info(f"Crystallizing document {document.id}")
        
        try:
            # Build the prompt for the document
            prompt = self.build_prompt(document)
            
            # Use the tool to process the document with schema
            tool_inputs = {
                'text': document.content,
                'instruction': prompt,
                'format': CrystallizationData.model_json_schema()  # Pass Pydantic schema
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
                # Validate response directly with the model
                crystallization_data = CrystallizationData.model_validate_json(llm_response)
                
                # Create result using validated data
                result = TaskResult(
                    task_type=self.task_type,
                    success=True,
                    document_id=str(document.id),
                    result_data=crystallization_data.model_dump(),
                    raw_response=llm_response
                )
                
                logger.info(f"Successfully crystallized document {document.id}")
                return result
                
            except Exception as e:
                logger.error(f"Error parsing crystallization results: {str(e)}")
                logger.error(f"Raw response: {llm_response}")
                return TaskResult(
                    task_type=self.task_type,
                    success=False,
                    document_id=str(document.id),
                    error_message=f"Failed to parse JSON response: {str(e)}",
                    raw_response=llm_response
                )
                
        except Exception as e:
            logger.error(f"Error in crystallizer task: {str(e)}", exc_info=True)
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
        # Include information from previous processing stages
        context_info = ""
        
        # Add contextual information
        if hasattr(document, 'contextualize') and document.contextualize:
            doc_type = getattr(document.contextualize, 'document_type', None)
            topics = getattr(document.contextualize, 'topics', [])
            
            if doc_type or topics:
                context_info += "Document context:\n"
                if doc_type:
                    context_info += f"- Type: {doc_type}\n"
                if topics:
                    context_info += f"- Topics: {', '.join(topics)}\n"
                context_info += "\n"
        
        # Add categorization information
        if hasattr(document, 'categorization') and document.categorization:
            primary_category = getattr(document.categorization, 'primary_category', None)
            tags = getattr(document.categorization, 'tags', [])
            
            if primary_category or tags:
                context_info += "Document classification:\n"
                if primary_category:
                    context_info += f"- Primary category: {primary_category}\n"
                if tags:
                    context_info += f"- Tags: {', '.join(tags)}\n"
                context_info += "\n"
        
        prompt = (
            "You are a document crystallizer. Your task is to extract and synthesize the most important "
            "information from the following document.\n\n"
            f"{context_info}"
            f"Document content:\n{document.content}\n\n"
            "Return a structured JSON object containing:\n"
            "1. executive_summary: A concise summary (3-5 sentences) of the document\n"
            "2. key_points: A list of the most important points from the document\n"
            "3. core_concepts: A list of central concepts discussed in the document\n"
            "4. conclusions: Main conclusions or takeaways from the document\n"
            "5. questions_raised: Important questions raised or left unanswered\n\n"
            "The output must match the schema provided."
        )
        return prompt