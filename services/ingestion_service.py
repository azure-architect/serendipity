# services/ingestion_service.py
import os
import uuid
import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from utils.file_watcher import FileWatcher
from core.schema import ProcessedDocument, DocumentStatus
from core.pipeline import Pipeline
from config.defaults import INGESTION_DEFAULTS

logger = logging.getLogger(__name__)

class IngestionService:
    """
    Service for ingesting documents from file system folders and processing them
    through the META pipeline.
    """
    
    def __init__(self, pipeline: Pipeline, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the ingestion service.
        
        Args:
            pipeline: The document processing pipeline
            config: Optional configuration to override defaults
        """
        self.pipeline = pipeline
        self.config = config or {}
        self.file_watchers = []
        self.running = False
        self.processing_queue = asyncio.Queue()
        self.processed_count = 0
        self.failed_count = 0
        
        # Use defaults or override with provided config
        self.watch_folders = self.config.get("watch_folders", INGESTION_DEFAULTS["watch_folders"])
        self.processing_config = self.config.get("processing", INGESTION_DEFAULTS["processing"])
        
        # Create processing task
        self.processing_task = None
        
        logger.info("Ingestion service initialized")
    
    async def start(self):
        """Start the ingestion service and file watchers."""
        if self.running:
            logger.warning("Ingestion service is already running")
            return
            
        self.running = True
        logger.info("Starting ingestion service")
        
        # Start the processing task
        self.processing_task = asyncio.create_task(self._process_queue())
        
        # Setup file watchers for each configured folder
        for folder_config in self.watch_folders:
            await self._setup_watcher(folder_config)
        
        # Process any existing files if auto_start is enabled
        if self.processing_config.get("auto_start", True):
            await self._process_existing_files()
            
        logger.info("Ingestion service started")
    
    async def stop(self):
        """Stop the ingestion service and all file watchers."""
        if not self.running:
            return
            
        logger.info("Stopping ingestion service")
        
        # Stop all file watchers
        for watcher in self.file_watchers:
            watcher.stop()
        
        self.file_watchers = []
        
        # Cancel processing task
        if self.processing_task:
            self.processing_task.cancel()
            try:
                await self.processing_task
            except asyncio.CancelledError:
                pass
            
        self.running = False
        logger.info("Ingestion service stopped")
    
    async def _setup_watcher(self, folder_config: Dict[str, Any]):
        """
        Set up a file watcher for a specific folder.
        
        Args:
            folder_config: Configuration for the folder to watch
        """
        path = folder_config.get("path")
        if not path:
            logger.error("Missing path in folder configuration")
            return
            
        # Create the directory if it doesn't exist
        os.makedirs(path, exist_ok=True)
        
        # Create and start file watcher
        watcher = FileWatcher(
            directory=path,
            callback=self._on_file_detected,
            file_formats=folder_config.get("file_formats"),
            ignore_patterns=folder_config.get("ignore_patterns"),
            recursive=folder_config.get("recursive", False)
        )
        
        watcher.start()
        self.file_watchers.append(watcher)
        logger.info(f"Started file watcher for {path}")
    
    async def _process_existing_files(self):
        """Process any existing files in the watch folders."""
        for folder_config in self.watch_folders:
            path = folder_config.get("path")
            for file_watcher in self.file_watchers:
                if file_watcher.directory == path:
                    file_watcher.process_existing_files()
    
    async def _on_file_detected(self, document_data: Dict[str, Any]):
        """
        Callback for when a new file is detected.
        
        Args:
            document_data: Data about the detected file
        """
        # Add to processing queue
        await self.processing_queue.put(document_data)
        logger.info(f"Queued file for processing: {document_data.get('metadata', {}).get('original_filename', 'unknown')}")
    
    async def _process_queue(self):
        """Process documents from the queue."""
        batch_size = self.processing_config.get("batch_size", 10)
        interval = self.processing_config.get("interval_seconds", 5)
        
        while self.running:
            try:
                # Process up to batch_size documents
                processed = 0
                while not self.processing_queue.empty() and processed < batch_size:
                    document_data = await self.processing_queue.get()
                    asyncio.create_task(self._process_document(document_data))
                    self.processing_queue.task_done()
                    processed += 1
                
                # Wait before next batch
                await asyncio.sleep(interval)
                
            except asyncio.CancelledError:
                logger.info("Processing task cancelled")
                return
            except Exception as e:
                logger.error(f"Error in processing queue: {str(e)}", exc_info=True)
                # Wait before retrying
                await asyncio.sleep(interval)
    
    async def _process_document(self, document_data: Dict[str, Any]) -> Optional[ProcessedDocument]:
        """
        Process a document detected by the file watcher.
        
        Args:
            document_data: Data about the document
            
        Returns:
            The processed document, or None if processing failed
        """
        max_retries = self.processing_config.get("max_retries", 3)
        retry_count = 0
        
        while retry_count <= max_retries:
            try:
                # Create a ProcessedDocument from the file data
                document = ProcessedDocument(
                    id=document_data.get("id", str(uuid.uuid4())),
                    content=document_data.get("content", ""),
                    metadata=document_data.get("metadata", {}),
                    status=DocumentStatus.PENDING
                )
                
                filename = document.metadata.get("original_filename", "unknown")
                logger.info(f"Processing document {document.id} from {filename}")
                
                # Process through pipeline
                processed_document = await self.pipeline.process_document(document)
                
                # Update counts and log result
                if processed_document.status == DocumentStatus.COMPLETED:
                    self.processed_count += 1
                    logger.info(f"Successfully processed document {document.id}")
                else:
                    self.failed_count += 1
                    logger.warning(f"Document processing incomplete: {document.id}, status: {processed_document.status}")
                
                # Archive the original file if configured
                await self._handle_post_processing(document_data, processed_document)
                
                return processed_document
                
            except Exception as e:
                retry_count += 1
                logger.error(f"Error processing document (attempt {retry_count}/{max_retries}): {str(e)}", exc_info=True)
                
                if retry_count <= max_retries:
                    # Wait before retrying
                    await asyncio.sleep(retry_count * 2)
                else:
                    self.failed_count += 1
                    logger.error(f"Failed to process document after {max_retries} attempts")
                    
                    # Handle failed document
                    await self._handle_failed_document(document_data)
                    return None
    
    async def _handle_post_processing(self, document_data: Dict[str, Any], processed_document: ProcessedDocument):
        """
        Handle post-processing of documents (archiving, etc).
        
        Args:
            document_data: Original document data
            processed_document: Processed document
        """
        # Implementation for archiving can be added here
        pass
    
    async def _handle_failed_document(self, document_data: Dict[str, Any]):
        """
        Handle a failed document.
        
        Args:
            document_data: Document data that failed processing
        """
        # Implementation for handling failed documents can be added here
        pass
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the ingestion service.
        
        Returns:
            Dictionary with statistics
        """
        return {
            "running": self.running,
            "queue_size": self.processing_queue.qsize(),
            "processed_count": self.processed_count,
            "failed_count": self.failed_count,
            "watch_folders": [w.directory for w in self.file_watchers]
        }