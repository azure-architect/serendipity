# services/ingestion_service.py
import os
import uuid
import asyncio
import logging
import json
import shutil
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
        self.processed_count = 0
        self.failed_count = 0
        
        # Import configuration with fallbacks to defaults
        self.watch_folders = self.config.get("watch_folders", INGESTION_DEFAULTS["watch_folders"])
        self.processing_config = self.config.get("processing", INGESTION_DEFAULTS["processing"])
        self.file_type_handlers = self.config.get("file_type_handlers", INGESTION_DEFAULTS["file_type_handlers"])
        self.queue_config = self.config.get("queue_config", INGESTION_DEFAULTS["queue_config"])
        self.post_processing = self.config.get("post_processing", INGESTION_DEFAULTS["post_processing"])
        self.notifications = self.config.get("notifications", INGESTION_DEFAULTS["notifications"])
        
        # Configure queue based on settings
        max_queue_size = self.queue_config.get("max_queue_size", 100)
        self.processing_queue = asyncio.Queue(maxsize=max_queue_size)
        
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
        try:
            await self.processing_queue.put(document_data)
            logger.info(f"Queued file for processing: {document_data.get('metadata', {}).get('original_filename', 'unknown')}")
        except asyncio.QueueFull:
            logger.error("Processing queue is full, cannot add new document")
            if self.notifications.get("notify_on_queue_full", True):
                # In a real system, this would trigger an alert or notification
                pass
    
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
                # Check file size limits
                file_size = document_data.get("metadata", {}).get("file_size", 0)
                max_size_bytes = self.config.get("max_file_size_mb", INGESTION_DEFAULTS["max_file_size_mb"]) * 1024 * 1024
                min_size_bytes = self.config.get("min_file_size_bytes", INGESTION_DEFAULTS["min_file_size_bytes"])
                
                if file_size > max_size_bytes:
                    logger.warning(f"File exceeds maximum size limit: {file_size} bytes > {max_size_bytes} bytes")
                    await self._handle_failed_document(document_data, error="File size exceeds limit")
                    return None
                
                if file_size < min_size_bytes:
                    logger.warning(f"File below minimum size limit: {file_size} bytes < {min_size_bytes} bytes")
                    await self._handle_failed_document(document_data, error="File size below minimum")
                    return None
                
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
                    
                    # Send notification if configured
                    if self.notifications.get("notify_on_success", False):
                        # In a real system, this would trigger a success notification
                        pass
                else:
                    self.failed_count += 1
                    logger.warning(f"Document processing incomplete: {document.id}, status: {processed_document.status}")
                    
                    # Send notification if configured
                    if self.notifications.get("notify_on_failure", True):
                        # In a real system, this would trigger a failure notification
                        pass
                
                # Archive the original file if configured
                await self._handle_post_processing(document_data, processed_document)
                
                return processed_document
                
            except Exception as e:
                retry_count += 1
                logger.error(f"Error processing document (attempt {retry_count}/{max_retries}): {str(e)}", exc_info=True)
                
                if retry_count <= max_retries:
                    # Wait before retrying with exponential backoff
                    await asyncio.sleep(retry_count * 2)
                else:
                    self.failed_count += 1
                    logger.error(f"Failed to process document after {max_retries} attempts")
                    
                    # Handle failed document
                    await self._handle_failed_document(document_data, error=str(e))
                    return None
    
    async def _handle_post_processing(self, document_data: Dict[str, Any], processed_document: ProcessedDocument):
        """
        Handle post-processing of documents (archiving, etc).
        
        Args:
            document_data: Original document data
            processed_document: Processed document
        """
        # Skip if archiving is disabled
        if not self.post_processing.get("archive_processed", True):
            logger.debug(f"Archiving disabled, skipping post-processing for document {processed_document.id}")
            return
        
        # Get the original file path
        original_path = document_data.get("metadata", {}).get("original_path")
        if not original_path:
            logger.warning(f"No original path found for document {processed_document.id}, cannot archive")
            return
        
        # Create archive directory if it doesn't exist
        archive_path = self.post_processing.get("archive_path", "./processed")
        os.makedirs(archive_path, exist_ok=True)
        
        # Generate archive filename
        original_filename = document_data.get("metadata", {}).get("original_filename", "unknown")
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        archive_filename = f"{timestamp}_{processed_document.id}_{original_filename}"
        archive_filepath = os.path.join(archive_path, archive_filename)
        
        try:
            # Move the original file to the archive directory instead of copying
            shutil.move(original_path, archive_filepath)
            logger.info(f"Moved document {processed_document.id} from {original_path} to {archive_filepath}")
            
            # Also save the processed document as JSON for reference
            processed_json_path = os.path.join(archive_path, f"{timestamp}_{processed_document.id}.json")
            
            # Prepare document for serialization
            if hasattr(processed_document, 'model_dump'):
                # Pydantic v2 model
                doc_dict = processed_document.model_dump()
            elif hasattr(processed_document, 'dict'):
                # Pydantic v1 model
                doc_dict = processed_document.dict()
            else:
                # Regular object - convert to dict manually
                doc_dict = {
                    "id": processed_document.id,
                    "content": processed_document.content,
                    "metadata": processed_document.metadata,
                    "status": str(processed_document.status),
                    "processing_stage": processed_document.processing_stage
                }
                
                # Add results from each stage if available
                for stage in ["contextualize", "clarify", "categorize", "crystallize", "connect"]:
                    if hasattr(processed_document, f"{stage}_results"):
                        doc_dict[f"{stage}_results"] = getattr(processed_document, f"{stage}_results")
            
            # Write the JSON file
            with open(processed_json_path, 'w', encoding='utf-8') as f:
                json.dump(doc_dict, f, indent=2, default=str)
            
            logger.info(f"Saved processed document data to {processed_json_path}")
        except Exception as e:
            logger.error(f"Error archiving document {processed_document.id}: {str(e)}", exc_info=True)





    
    async def _handle_failed_document(self, document_data: Dict[str, Any], error: str = "Unknown error"):
        """
        Handle a failed document.
        
        Args:
            document_data: Document data that failed processing
            error: Error message describing the failure
        """
        # Get the original file path
        original_path = document_data.get("metadata", {}).get("original_path")
        if not original_path:
            logger.warning("No original path found for failed document, cannot process")
            return
        
        # Create failed directory if it doesn't exist
        failed_path = self.post_processing.get("failed_path", "./failed")
        os.makedirs(failed_path, exist_ok=True)
        
        # Generate failed filename
        original_filename = document_data.get("metadata", {}).get("original_filename", "unknown")
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        failed_filename = f"failed_{timestamp}_{original_filename}"
        failed_filepath = os.path.join(failed_path, failed_filename)
        
        try:
            # Copy the original file to the failed directory
            shutil.copy2(original_path, failed_filepath)
            logger.info(f"Moved failed document to {failed_filepath}")
            
            # Add error information to document data
            failure_info = document_data.copy()
            failure_info["failure"] = {
                "timestamp": datetime.now().isoformat(),
                "error_message": error
            }
            
            # Save the document data as JSON for debugging
            failed_json_path = os.path.join(failed_path, f"failed_{timestamp}_data.json")
            with open(failed_json_path, 'w', encoding='utf-8') as f:
                json.dump(failure_info, f, indent=2, default=str)
            
            logger.info(f"Saved failed document data to {failed_json_path}")
            
            # Delete the original file if configured
            if self.post_processing.get("delete_failed", False):
                try:
                    os.remove(original_path)
                    logger.info(f"Deleted original failed document: {original_path}")
                except Exception as e:
                    logger.error(f"Error deleting failed document {original_path}: {str(e)}")
                    
        except Exception as e:
            logger.error(f"Error handling failed document: {str(e)}", exc_info=True)
    
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
            "watch_folders": [w.directory for w in self.file_watchers],
            "archive_path": self.post_processing.get("archive_path", "./processed"),
            "failed_path": self.post_processing.get("failed_path", "./failed")
        }