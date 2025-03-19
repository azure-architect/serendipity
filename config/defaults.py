# config/defaults.py
"""
Default configuration values for the document ingestion system and processing pipeline.
"""
from core.schema import TaskType

# Define ingestion default settings
INGESTION_DEFAULTS = {
    # Ingestion folder configuration
    "watch_folders": [
        {
            "path": "./inbox",
            "recursive": True,
            "file_formats": [".txt", ".md", ".json"],
            "ignore_patterns": [".git", ".DS_Store", "~", ".tmp"],
        }
    ],
    
    # Processing configuration
    "processing": {
        "auto_start": True,
        "batch_size": 10,
        "interval_seconds": 5,
        "max_retries": 3
    },
    
    # Default document ID generation options
    "document_id_prefix": "doc",
    "use_uuid": True,
    
    # File size limits
    "max_file_size_mb": 10,
    "min_file_size_bytes": 10,
    
    # Handler mapping for different file types
    "file_type_handlers": {
        ".txt": "plain_text_handler",
        ".md": "markdown_handler",
        ".json": "json_handler",
    },
    
    # Ingestion queue configuration
    "queue_config": {
        "max_queue_size": 100,
        "processing_threads": 2,
        "priority_levels": 3
    },
    
    # Post-processing options
    "post_processing": {
        "archive_processed": True,
        "archive_path": "./processed",
        "delete_failed": False,
        "failed_path": "./failed"
    },
    
    # Event notifications
    "notifications": {
        "notify_on_success": False,
        "notify_on_failure": True,
        "notify_on_queue_full": True
    }
}

# Define pipeline default settings
PIPELINE_DEFAULTS = [
    {
        "type": "contextualizer",
        "task_type": TaskType.CONTEXTUALIZER,  # Use the enum value
        "task_config": {
            "tool": "text_processor",
            "tool_config": {
                "llm_config": {
                    "adapter": "ollama",
                    "model": "mistral:7b-instruct-fp16",
                    "temperature": 0.3,
                    "max_tokens": 1000,
                }
            }
        }
    },
    {
        "type": "clarifier",
        "task_type": TaskType.CLARIFIER,  # Use the enum value
        "task_config": {
            "tool": "text_processor",
            "tool_config": {
                "llm_config": {
                    "adapter": "ollama",
                    "model": "mistral:7b-instruct-fp16"
                }
            }
        }
    },
    {
        "type": "categorizer",
        "task_type": TaskType.CATEGORIZER,  # Use the enum value
        "task_config": {
            "tool": "text_processor",
            "tool_config": {
                "llm_config": {
                    "adapter": "ollama",
                    "model": "mistral:7b-instruct-fp16"
                }
            }
        }
    },
    {
        "type": "crystallizer",
        "task_type": TaskType.CRYSTALLIZER,  # Use the enum value
        "task_config": {
            "tool": "text_processor",
            "tool_config": {
                "llm_config": {
                    "adapter": "ollama",
                    "model": "mistral:7b-instruct-fp16"
                }
            }
        }
    },
    {
        "type": "connector",
        "task_type": TaskType.CONNECTOR,  # Use the enum value
        "task_config": {
            "tool": "text_processor",
            "tool_config": {
                "llm_config": {
                    "adapter": "ollama",
                    "model": "mistral:7b-instruct-fp16"
                }
            }
        }
    }
]