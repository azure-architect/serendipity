# implementations/tasks/connector_task.py
import logging
from typing import Dict, Any, Optional, List
import json

from core.interfaces import ITask, ITool
from core.schema import ProcessedDocument, TaskResult, TaskType

logger = logging.getLogger(__name__)

class ConnectorTask(ITask):
    """
    Task for connecting document content with other documents and concepts.
    Implements the ITask interface.
    """
    
    def __init__(self, config: Dict[str, Any], tool: ITool):
        self.config = config
        self.tool = tool
        self._task_type = TaskType.CONNECTOR
        self.document_corpus = []  # This would typically be loaded from a repository
        logger.info(f"Initialized {self._task_type.value} task")
    
    @property
    def task_type(self) -> TaskType:
        """Get the type of this task."""
        return self._task_type
    
    async def process(self, document: ProcessedDocument) -> TaskResult:
        """
        Process a document to create connections.
        
        Args:
            document: The document to process
            
        Returns:
            TaskResult containing the processing result
        """
        logger.info(f"Creating connections for document {document.id}")
        
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
                connection_data = json.loads(json_str)
                
                # Create result
                result = TaskResult(
                    task_type=self.task_type,
                    success=True,
                    document_id=str(document.id),
                    result_data=connection_data,
                    raw_response=llm_response
                )
                
                logger.info(f"Successfully created connections for document {document.id}")
                return result
                
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing connection results: {str(e)}")
                logger.error(f"Raw response: {llm_response}")
                return TaskResult(
                    task_type=self.task_type,
                    success=False,
                    document_id=str(document.id),
                    error_message=f"Failed to parse JSON response: {str(e)}",
                    raw_response=llm_response
                )
                
        except Exception as e:
            logger.error(f"Error in connector task: {str(e)}", exc_info=True)
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
        # Include information from all previous processing stages
        context_info = ""
        
        # Add crystallization information if available
        if hasattr(document, 'crystallization') and document.crystallization:
            summary = getattr(document.crystallization, 'executive_summary', "")
            key_points = getattr(document.crystallization, 'key_points', [])
            core_concepts = getattr(document.crystallization, 'core_concepts', [])
            
            if summary or key_points or core_concepts:
                context_info += "Document crystallization:\n"
                if summary:
                    context_info += f"- Summary: {summary}\n"
                if key_points:
                    context_info += f"- Key points: {', '.join(key_points)}\n"
                if core_concepts:
                    context_info += f"- Core concepts: {', '.join(core_concepts)}\n"
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
        
        # Add information about other documents (limited to avoid overwhelming the LLM)
        corpus_info = ""
        if self.document_corpus:
            corpus_info = "Sample of other documents in the corpus (for connection mapping):\n"
            for idx, doc in enumerate(self.document_corpus[:3]):  # Limit to 3 documents
                doc_id = getattr(doc, 'id', f"doc-{idx}")
                doc_title = getattr(doc, 'title', f"Document {idx}")
                corpus_info += f"- {doc_title} (ID: {doc_id})\n"
            corpus_info += "\n"
        
        prompt = (
            "You are a document connector. Your task is to identify relationships and connections "
            "between this document and other concepts or documents.\n\n"
            f"{context_info}"
            f"{corpus_info}"
            f"Document content:\n{document.content}\n\n"
            "Please provide the following information in JSON format:\n"
            "1. related_concepts: A list of concepts that connect to this document\n"
            "2. potential_references: A list of potential sources or references mentioned\n"
            "3. document_connections: A list of objects with 'document_id', 'connection_type', and 'strength' (1-10)\n"
            "4. dependency_chain: A list indicating logical or conceptual dependencies\n"
            "5. connection_notes: Additional notes about document connections\n\n"
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