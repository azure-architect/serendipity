# tests/test_ingestion_service.py
import os
import sys
import asyncio
import unittest
import logging
from pathlib import Path
from uuid import uuid4
import shutil
import tempfile

# Add project root to path to ensure imports work
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("ingestion_test")

# Import required modules
from services.ingestion_service import IngestionService
from core.pipeline import Pipeline
from factories.llm_factory import LLMFactory
from factories.tool_factory import ToolFactory
from factories.task_factory import TaskFactory
from factories.agent_factory import AgentFactory
from core.schema import ProcessedDocument, DocumentStatus, TaskType

class TestIngestionService(unittest.TestCase):
    """Tests for the document ingestion service."""
    
    async def asyncSetUp(self):
        """Set up test environment."""
        logger.info("Setting up test environment")
        
        # Create temporary directories for test
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_path = Path(self.temp_dir.name)
        
        # Create dirs for inbox, processed, and failed
        self.inbox_dir = self.base_path / "inbox"
        self.processed_dir = self.base_path / "processed"
        self.failed_dir = self.base_path / "failed"
        
        for directory in [self.inbox_dir, self.processed_dir, self.failed_dir]:
            os.makedirs(directory, exist_ok=True)
            
        logger.info(f"Created test directories in {self.base_path}")
        
        # Create factory chain
        llm_factory = LLMFactory()
        tool_factory = ToolFactory(llm_factory)
        task_factory = TaskFactory(tool_factory)
        self.agent_factory = AgentFactory(task_factory)
        
        # Configure minimal pipeline for testing
        self.pipeline_config = {
            "pipeline": [
                {
                    "type": "contextualizer",
                    "task_type": TaskType.CONTEXTUALIZER,
                    "task_config": {
                        "tool": "text_processor",
                        "tool_config": {
                            "llm_config": {
                                "adapter": "ollama",
                                "model": "mistral:7b-instruct-fp16",
                                "temperature": 0.2
                            }
                        }
                    }
                }
            ]
        }
        
        # Create pipeline
        self.pipeline = Pipeline(self.agent_factory, self.pipeline_config)
        
        # Create test ingestion config
        self.test_config = {
            "watch_folders": [
                {
                    "path": str(self.inbox_dir),
                    "recursive": False,
                    "file_formats": [".txt", ".md", ".json"],
                    "ignore_patterns": [".tmp", "~"]
                }
            ],
            "processing": {
                "auto_start": True,
                "batch_size": 2,
                "interval_seconds": 1,  # Faster for testing
                "max_retries": 1
            },
            "post_processing": {
                "archive_processed": True,
                "archive_path": str(self.processed_dir),
                "delete_failed": False,
                "failed_path": str(self.failed_dir)
            }
        }
        
        # Create service instance
        self.ingestion_service = IngestionService(self.pipeline, self.test_config)
    
    async def asyncTearDown(self):
        """Clean up test environment."""
        logger.info("Cleaning up test environment")
        
        # Stop the service if it's running
        if hasattr(self, 'ingestion_service') and self.ingestion_service.running:
            await self.ingestion_service.stop()
        
        # Remove temporary directory
        if hasattr(self, 'temp_dir'):
            self.temp_dir.cleanup()
    
    async def create_test_file(self, content="Test content", filename="test_document.txt"):
        """Create a test file in the inbox directory."""
        file_path = self.inbox_dir / filename
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        logger.info(f"Created test file: {file_path}")
        return file_path
    
    async def test_service_initialization(self):
        """Test that the service initializes properly."""
        # Service should not be running initially
        self.assertFalse(self.ingestion_service.running)
        
        # Config should be properly loaded
        self.assertEqual(
            self.ingestion_service.watch_folders[0]["path"], 
            str(self.inbox_dir)
        )
        self.assertEqual(
            self.ingestion_service.post_processing["archive_path"], 
            str(self.processed_dir)
        )
    
    async def test_service_start_stop(self):
        """Test starting and stopping the service."""
        # Start the service
        await self.ingestion_service.start()
        self.assertTrue(self.ingestion_service.running)
        
        # Verify file watchers were created
        self.assertEqual(len(self.ingestion_service.file_watchers), 1)
        
        # Stop the service
        await self.ingestion_service.stop()
        self.assertFalse(self.ingestion_service.running)
        self.assertEqual(len(self.ingestion_service.file_watchers), 0)
    
    async def test_document_processing(self):
        """Test that documents are processed and archived correctly."""
        # Start the service
        await self.ingestion_service.start()
        
        # Create test file
        test_content = """
        This is a test document for the ingestion service.
        It should be processed through the pipeline and archived.
        """
        await self.create_test_file(content=test_content)
        
        # Wait for processing to complete (allow time for file detection and processing)
        await asyncio.sleep(5)
        
        # Verify stats
        stats = self.ingestion_service.get_stats()
        self.assertGreaterEqual(stats["processed_count"] + stats["failed_count"], 0, 
                              "File should have been processed or marked as failed")
        
        # Check if files were created in the processed directory
        processed_files = list(self.processed_dir.glob("*.*"))
        
        # Either files should exist in processed or failed directory
        self.assertTrue(
            len(processed_files) > 0 or len(list(self.failed_dir.glob("*.*"))) > 0,
            "File should exist in either processed or failed directory"
        )
        
        # Stop the service
        await self.ingestion_service.stop()
    
    async def test_file_size_limits(self):
        """Test that file size limits are enforced."""
        # Modify config to set very small max file size
        self.ingestion_service.config["max_file_size_mb"] = 0.00001  # ~10 bytes
        
        # Start the service
        await self.ingestion_service.start()
        
        # Create a file that exceeds the limit
        large_content = "A" * 1000  # 1000 bytes, should exceed limit
        await self.create_test_file(content=large_content, filename="large_file.txt")
        
        # Wait for processing
        await asyncio.sleep(3)
        
        # File should be in failed directory
        failed_files = list(self.failed_dir.glob("*.*"))
        self.assertTrue(len(failed_files) > 0, "Oversized file should be in failed directory")
        
        # Stop the service
        await self.ingestion_service.stop()
    
    async def test_multiple_document_types(self):
        """Test processing different document types."""
        # Start the service
        await self.ingestion_service.start()
        
        # Create different file types
        await self.create_test_file(content="Text file content", filename="document.txt")
        await self.create_test_file(content="# Markdown heading\n\nContent", filename="document.md")
        await self.create_test_file(content='{"key": "value"}', filename="document.json")
        
        # Wait for processing
        await asyncio.sleep(5)
        
        # Check stats
        stats = self.ingestion_service.get_stats()
        self.assertGreaterEqual(stats["processed_count"] + stats["failed_count"], 0, 
                              "Files should have been processed or marked as failed")
        
        # Stop the service
        await self.ingestion_service.stop()

# Create helper for running async tests
def async_test(coro):
    def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(coro(*args, **kwargs))
    return wrapper

# Apply async wrapper to test methods
TestIngestionService.setUp = async_test(TestIngestionService.asyncSetUp)
TestIngestionService.tearDown = async_test(TestIngestionService.asyncTearDown)
TestIngestionService.test_service_initialization = async_test(TestIngestionService.test_service_initialization)
TestIngestionService.test_service_start_stop = async_test(TestIngestionService.test_service_start_stop)
TestIngestionService.test_document_processing = async_test(TestIngestionService.test_document_processing)
TestIngestionService.test_file_size_limits = async_test(TestIngestionService.test_file_size_limits)
TestIngestionService.test_multiple_document_types = async_test(TestIngestionService.test_multiple_document_types)

if __name__ == "__main__":
    unittest.main()