# implementations/tools/text_processor.py
import logging
from typing import Dict, Any, Optional

from core.interfaces import ITool, ILLM

logger = logging.getLogger(__name__)

class TextProcessor(ITool):
    """
    A tool for processing text using an LLM.
    """
    
    def __init__(self, config: Dict[str, Any], llm: ILLM):
        self._name = "text_processor"
        self._description = "Process text using language models"
        self.config = config
        self.llm = llm
        logger.info(f"Initialized {self._name} tool")
    
    @property
    def name(self) -> str:
        """Get the tool's name."""
        return self._name
    
    @property
    def description(self) -> str:
        """Get the tool's description."""
        return self._description
    
    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the tool with the provided inputs.
        
        Args:
            inputs: Dictionary containing:
                - 'text': Text to process
                - 'instruction': Processing instruction
                
        Returns:
            Dictionary containing the processed result
        """
        text = inputs.get('text', '')
        instruction = inputs.get('instruction', 'Process the following text:')
        
        if not text:
            logger.warning("No text provided for processing")
            return {"error": "No text provided"}
        
        try:
            prompt = f"{instruction}\n\n{text}"
            
            # Use the LLM to process the text
            result = await self.llm.generate(
                prompt=prompt,
                temperature=self.config.get('temperature', 0.7),
                max_tokens=self.config.get('max_tokens', 1000)
            )
            
            return {
                "result": result,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error executing text processor tool: {str(e)}")
            return {
                "error": str(e),
                "success": False
            }
    
    def get_llm(self) -> ILLM:
        """Get the LLM used by this tool."""
        return self.llm