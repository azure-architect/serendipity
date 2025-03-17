# defaults.py
"""
Default values and constants used throughout the system.
"""

# Default paths
DEFAULT_BASE_PATH = "."
DEFAULT_FOLDERS = {
    "capture": "1-Capture",
    "contextualize": "2-Contextualize",
    "clarify": "3-Clarify",
    "categorize": "4-Categorize",
    "crystallize": "5-Crystallize",
    "connect": "6-Connect"
}

# Default LLM settings
DEFAULT_LLM_PROVIDER = "ollama"
DEFAULT_LLM_MODEL = "llama3"
DEFAULT_TEMPERATURE = 0.7
DEFAULT_MAX_TOKENS = 1000

# Default task processing order
DEFAULT_TASK_SEQUENCE = [
    "contextualizer",
    "clarifier",
    "categorizer",
    "crystallizer", 
    "connector"
]

# Default prompt templates
DEFAULT_PROMPT_TEMPLATES = {
    "capture": "You are acting as the Capture agent. Your role is to efficiently capture raw thoughts exactly as they are presented, without alteration or judgment. Your task is to acknowledge receipt of the following thought content: '{thought_content}'",
    
    "contextualize": "You are acting as the Contextualize agent. Your role is to analyze the following thought content and add essential metadata without altering the original content. Thought content: '{thought_content}'",
    
    "clarify": "You are acting as the Clarify agent. Your role is to expand and develop the following thought into a more complete form while preserving its essence. Thought content: '{thought_content}'",
    
    "categorize": "You are acting as the Categorize agent. Your role is to connect this thought to existing knowledge frameworks and identify patterns. Thought content: '{thought_content}'",
    
    "crystallize": "You are acting as the Crystallize agent. Your role is to transform the processed thought into its most useful and actionable form. Thought content: '{thought_content}'",
    
    "connect": "You are acting as the Connect agent. Your role is to integrate this processed thought into broader knowledge systems. Thought content: '{thought_content}'"
}

# File extension handling
SUPPORTED_EXTENSIONS = ['.txt', '.md', '.json']
MARKDOWN_EXTENSIONS = ['.md', '.markdown']
TEXT_EXTENSIONS = ['.txt', '.text']
JSON_EXTENSIONS = ['.json']

# Timeout and retry settings
DEFAULT_LLM_TIMEOUT = 60  # seconds
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_DELAY = 2  # seconds