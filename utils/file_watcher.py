# utils/file_watcher.py
import os
import time
import logging
import json
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Callable, Dict, Any, Optional
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

logger = logging.getLogger(__name__)

class DocumentCreatedEvent(FileSystemEventHandler):
    """Handler for file system events that trigger document processing."""
    
    def __init__(self, callback, file_formats=None, ignore_patterns=None):
        """Initialize with a callback to invoke when a document is created.
        
        Args:
            callback: Function or coroutine to call with the document object
            file_formats: Optional list of file extensions to process
            ignore_patterns: Optional list of patterns to ignore
        """
        self.callback = callback
        self.file_formats = file_formats or ['.txt', '.md', '.json']
        self.ignore_patterns = ignore_patterns or ['.git', '.DS_Store', '~', '.tmp']
        self._processing_lock = set()  # Track files being processed to avoid duplicates
    
    def should_process_file(self, file_path: str) -> bool:
        """Determine if a file should be processed.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if file should be processed, False otherwise
        """
        # Check file extension
        _, ext = os.path.splitext(file_path)
        if ext.lower() not in self.file_formats:
            return False
        
        # Check ignore patterns
        filename = os.path.basename(file_path)
        for pattern in self.ignore_patterns:
            if pattern in filename:
                return False
        
        return True
    
    def read_file(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Read a file and create a document object.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Document object, or None if file couldn't be read
        """
        try:
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Get file metadata
            file_stats = os.stat(file_path)
            file_name = os.path.basename(file_path)
            file_extension = os.path.splitext(file_name)[1].lower()
            
            # Generate a document ID
            document_id = f"doc-{int(time.time())}-{hash(file_path) % 10000}"
            
            # Create basic document object
            document = {
                "id": document_id,
                "content": content,
                "metadata": {
                    "original_filename": file_name,
                    "original_path": file_path,
                    "file_size": file_stats.st_size,
                    "created_at": datetime.fromtimestamp(file_stats.st_ctime).isoformat(),
                    "modified_at": datetime.fromtimestamp(file_stats.st_mtime).isoformat(),
                    "file_extension": file_extension,
                }
            }
            
            # Handle JSON files specially if they're already in our format
            if file_extension == '.json':
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        json_content = json.load(f)
                    
                    # If this looks like one of our documents, use it directly
                    if isinstance(json_content, dict) and 'id' in json_content and 'content' in json_content:
                        # Still update file metadata
                        if 'metadata' not in json_content:
                            json_content['metadata'] = {}
                        json_content['metadata'].update(document['metadata'])
                        document = json_content
                except json.JSONDecodeError:
                    # Not a valid JSON file, treat as regular content
                    pass
            
            return document
        
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return None
    
    def on_created(self, event):
        """Handle file creation events.
        
        Args:
            event: The file system event
        """
        # Skip directories
        if event.is_directory:
            return
        
        # Get file path
        file_path = event.src_path
        
        # Check if file should be processed
        if not self.should_process_file(file_path):
            return
        
        # Avoid processing the same file multiple times
        if file_path in self._processing_lock:
            return
        
        try:
            self._processing_lock.add(file_path)
            logger.info(f"New file detected: {file_path}")
            
            # Wait a moment to ensure file is fully written
            # This helps avoid partial reads of files still being written
            time.sleep(0.5)
            
            # Process the file
            document = self.read_file(file_path)
            if document:
                if asyncio.iscoroutinefunction(self.callback):
                    # Handle async callback - need to run it in the main event loop
                    try:
                        # Try to get an existing event loop
                        loop = asyncio.get_event_loop()
                    except RuntimeError:
                        # No event loop in this thread, create a new one
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                    
                    # Run the coroutine using the appropriate method
                    if loop.is_running():
                        # If loop is running, use call_soon_threadsafe
                        future = asyncio.run_coroutine_threadsafe(self.callback(document), loop)
                    else:
                        # If the loop isn't running, run the coroutine directly
                        loop.run_until_complete(self.callback(document))
                else:
                    # Direct call for non-async functions
                    self.callback(document)
        finally:
            self._processing_lock.remove(file_path)


class FileWatcher:
    """Watches a directory for new files and processes them."""
    
    def __init__(self, 
                directory: str, 
                callback: Callable, 
                file_formats=None, 
                ignore_patterns=None,
                recursive=False):
        """Initialize the file watcher.
        
        Args:
            directory: Directory to watch
            callback: Function to call with new documents
            file_formats: Optional list of file extensions to process
            ignore_patterns: Optional list of patterns to ignore
            recursive: Whether to watch subdirectories
        """
        self.directory = directory
        self.callback = callback
        self.file_formats = file_formats
        self.ignore_patterns = ignore_patterns
        self.recursive = recursive
        self.observer = None
    
    def start(self):
        """Start watching the directory."""
        # Create directory if it doesn't exist
        os.makedirs(self.directory, exist_ok=True)
        
        # Process existing files
        self.process_existing_files()
        
        # Start watching for new files
        event_handler = DocumentCreatedEvent(
            self.callback, 
            self.file_formats, 
            self.ignore_patterns
        )
        
        self.observer = Observer()
        self.observer.schedule(
            event_handler, 
            self.directory, 
            recursive=self.recursive
        )
        self.observer.start()
        
        logger.info(f"Started watching directory: {self.directory}")
    
    def stop(self):
        """Stop watching the directory."""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            logger.info(f"Stopped watching directory: {self.directory}")
    
    def process_existing_files(self):
        """Process any existing files in the directory."""
        logger.info(f"Processing existing files in {self.directory}")
        
        event_handler = DocumentCreatedEvent(
            self.callback, 
            self.file_formats, 
            self.ignore_patterns
        )
        
        # Walk directory and process files
        if self.recursive:
            for root, _, files in os.walk(self.directory):
                for file_name in files:
                    file_path = os.path.join(root, file_name)
                    if event_handler.should_process_file(file_path):
                        document = event_handler.read_file(file_path)
                        if document:
                            if asyncio.iscoroutinefunction(self.callback):
                                # Handle async callback similarly to on_created
                                try:
                                    loop = asyncio.get_event_loop()
                                except RuntimeError:
                                    loop = asyncio.new_event_loop()
                                    asyncio.set_event_loop(loop)
                                
                                if loop.is_running():
                                    future = asyncio.run_coroutine_threadsafe(self.callback(document), loop)
                                else:
                                    loop.run_until_complete(self.callback(document))
                            else:
                                self.callback(document)
        else:
            for file_name in os.listdir(self.directory):
                file_path = os.path.join(self.directory, file_name)
                if os.path.isfile(file_path) and event_handler.should_process_file(file_path):
                    document = event_handler.read_file(file_path)
                    if document:
                        if asyncio.iscoroutinefunction(self.callback):
                            # Handle async callback similarly to on_created
                            try:
                                loop = asyncio.get_event_loop()
                            except RuntimeError:
                                loop = asyncio.new_event_loop()
                                asyncio.set_event_loop(loop)
                            
                            if loop.is_running():
                                future = asyncio.run_coroutine_threadsafe(self.callback(document), loop)
                            else:
                                loop.run_until_complete(self.callback(document))
                        else:
                            self.callback(document)