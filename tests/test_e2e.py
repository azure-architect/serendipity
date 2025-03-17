#!/usr/bin/env python
# tests/test_e2e.py

import os
import sys
import asyncio
import logging
import tempfile
import unittest
from datetime import datetime
from uuid import uuid4
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("e2e_test")

# Add project root to path if necessary
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import required modules
from core.pipeline import Pipeline
from core.state import StateManager
from storage.file_system import FileSystemStorage
from core.schema import (
    ProcessedDocument, DocumentState, ProcessingStage, 
    ContentMetadata, LLMType, TaskType
)
from tasks.factory import TaskFactory
from llm.factory import LLMFactory

class TestEndToEnd(unittest.TestCase):
    """End-to-end tests for the document processing pipeline."""
    
    async def asyncSetUp(self):
        """Set up test environment."""
        logger.info("Setting up test environment...")
        
        # Create temporary directory for storage
        self.temp_dir = tempfile.TemporaryDirectory()
        logger.info(f"Created temporary directory at: {self.temp_dir.name}")
        
        # Initialize storage
        self.storage = FileSystemStorage(self.temp_dir.name)
        logger.info("FileSystemStorage initialized")
        
        # Initialize state manager
        self.state_manager = StateManager(self.storage)
        logger.info("StateManager initialized")
        
        # Initialize LLM factory (mock implementation for testing)
        self.llm_factory = LLMFactory()
        logger.info("LLMFactory initialized")
        
        # Initialize task factory
        self.task_factory = TaskFactory(self.llm_factory)
        logger.info("TaskFactory initialized")
        
        # Initialize pipeline
        self.pipeline = Pipeline(self.storage, self.task_factory)
        logger.info("Pipeline initialized")
        
    async def asyncTearDown(self):
        """Clean up test environment."""
        logger.info("Cleaning up test environment...")
        self.temp_dir.cleanup()
        logger.info("Temporary directory removed")
        
    async def test_document_processing_flow(self):
        """Test the full document processing flow."""
        logger.info("Starting document processing flow test")
        
        # Create a test document
        document_id = str(uuid4())
        test_content = "This is a test document for the processing pipeline."
        
        document_state = DocumentState(
            document_id=document_id,
            current_stage=ProcessingStage.CREATED
        )
        
        document = ProcessedDocument(
            id=document_id,
            content=test_content,
            original_filename="test_document.txt",
            processing_stage=ProcessingStage.CREATED.value,
            state=document_state,
            ingest=ContentMetadata(
                raw_content=test_content,
                source_type="test"
            )
        )
        
        logger.info(f"Created test document with ID: {document_id}")
        
        # Save document to storage
        await self.storage.save_document(document)
        logger.info("Document saved to storage")
        
        # Verify document was saved properly
        retrieved_document = await self.storage.get_document(document_id)
        self.assertIsNotNone(retrieved_document, "Document should be retrievable from storage")
        logger.info("Document successfully retrieved from storage")
        
        self.assertEqual(retrieved_document.content, test_content, 
                        "Retrieved document content should match original")
        logger.info("Document content verified")
        
        self.assertEqual(retrieved_document.state.current_stage, ProcessingStage.CREATED, 
                        "Document should be in CREATED stage")
        logger.info("Document stage verified")
        
        # Test locking mechanism
        lock = await self.state_manager.lock_document(document_id, "test_agent")
        logger.info(f"Document locked by test_agent with lock ID: {lock.lock_id}")
        
        # Verify lock was applied
        retrieved_state = await self.storage.get_document_state(document_id)
        self.assertIsNotNone(retrieved_state.lock, "Document should be locked")
        logger.info("Document lock verified")
        
        # Unlock document
        await self.state_manager.unlock_document(document_id, "test_agent")
        logger.info("Document unlocked")
        
        # Verify unlocked state
        retrieved_state = await self.storage.get_document_state(document_id)
        self.assertIsNone(retrieved_state.lock, "Document should be unlocked")
        logger.info("Document unlock verified")
        
        # Test state transition
        await self.state_manager.transition_state(
            document_id, 
            ProcessingStage.CAPTURED, 
            "test_agent",
            "Document captured for testing"
        )
        logger.info("Document state transitioned to CAPTURED")
        
        # Verify state transition
        retrieved_state = await self.storage.get_document_state(document_id)
        self.assertEqual(retrieved_state.current_stage, ProcessingStage.CAPTURED, 
                        "Document should be in CAPTURED stage")
        self.assertEqual(retrieved_state.previous_stage, ProcessingStage.CREATED, 
                        "Previous stage should be CREATED")
        logger.info("Document state transition verified")
        
        # TODO: Add tests for actual document processing through pipeline
        # This will require mock implementations of the task classes
        
        logger.info("Document processing flow test completed successfully")
        
def run_async_test(test_func):
    """Helper function to run async test methods."""
    def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(test_func(*args, **kwargs))
    return wrapper

# Apply the async wrapper to test methods
TestEndToEnd.setUp = run_async_test(TestEndToEnd.asyncSetUp)
TestEndToEnd.tearDown = run_async_test(TestEndToEnd.asyncTearDown)
TestEndToEnd.test_document_processing_flow = run_async_test(TestEndToEnd.test_document_processing_flow)

if __name__ == "__main__":
    logger.info("Starting end-to-end tests")
    unittest.main(verbosity=2)
    logger.info("End-to-end tests completed")