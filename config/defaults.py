# ingestion/defaults.py
"""
Default configuration values for the document ingestion system.
"""

# Ingestion folder configuration
WATCH_FOLDERS = [
    {
        "path": "./inbox",
        "recursive": True,
        "file_formats": [".txt", ".md", ".json"],
        "ignore_patterns": [".git", ".DS_Store", "~", ".tmp"],
    }
]

# Processing configuration
PROCESSING_CONFIG = {
    "auto_start": True,
    "batch_size": 10,
    "interval_seconds": 5,
    "max_retries": 3
}

# Default document ID generation options
DOCUMENT_ID_PREFIX = "doc"
USE_UUID = True

# File size limits
MAX_FILE_SIZE_MB = 10
MIN_FILE_SIZE_BYTES = 10

# Handler mapping for different file types
FILE_TYPE_HANDLERS = {
    ".txt": "plain_text_handler",
    ".md": "markdown_handler",
    ".json": "json_handler",
    # Can be extended with more handlers
}

# Ingestion queue configuration
QUEUE_CONFIG = {
    "max_queue_size": 100,
    "processing_threads": 2,
    "priority_levels": 3
}

# Post-processing options
POST_PROCESSING = {
    "archive_processed": True,
    "archive_path": "./processed",
    "delete_failed": False,
    "failed_path": "./failed"
}

# Event notifications
NOTIFICATIONS = {
    "notify_on_success": False,
    "notify_on_failure": True,
    "notify_on_queue_full": True
}