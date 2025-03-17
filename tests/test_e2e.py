# tests/test_end_to_end.py
import os, sys
import shutil
import time
import json
from pathlib import Path
import tempfile
import unittest

# Add the project root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


# Import your main components
from tasks.factory import TaskFactory
from llm.factory import LLMFactory
from core.pipeline import Pipeline
from core.state import StateManager
from storage.file_system import FileSystemStorage
from utils.file_watcher import FileWatcher



class EndToEndTest(unittest.TestCase):
    """End-to-end test of the document processing pipeline."""
    
    def setUp(self):
        """Set up test environment."""
        # Create temporary directories
        self.test_dir = tempfile.mkdtemp()
        self.inbox_dir = os.path.join(self.test_dir, "inbox")
        self.output_dir = os.path.join(self.test_dir, "output")
        os.makedirs(self.inbox_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Create factories
        self.llm_factory = LLMFactory()
        self.task_factory = TaskFactory(self.llm_factory)
        
        # Create storage
        self.storage = FileSystemStorage(self.output_dir)
        
        # Create state manager
        self.state_manager = StateManager(self.storage)
        
        # Create pipeline
        self.pipeline = Pipeline(self.task_factory, self.state_manager, self.storage)
        
        # Create file watcher
        self.watcher = FileWatcher(self.inbox_dir, self.pipeline.process)
    
    def tearDown(self):
        """Clean up test environment."""
        # Stop watcher
        if hasattr(self, 'watcher') and self.watcher:
            self.watcher.stop()
        
        # Remove test directory
        if hasattr(self, 'test_dir') and os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_basic_processing(self):
        """Test basic document processing flow."""
        # Start the watcher
        self.watcher.start()
        
        # Create a test document file
        test_content = "This is a test document for end-to-end testing."
        test_file_path = os.path.join(self.inbox_dir, "test_document.txt")
        with open(test_file_path, 'w') as f:
            f.write(test_content)
        
        # Wait for processing to complete
        # In a real test, you might use events or polling to properly wait
        time.sleep(5)
        
        # Check if document was processed
        # Look for output files in the output directory
        output_files = list(Path(self.output_dir).glob("*.json"))
        self.assertGreaterEqual(len(output_files), 1, "No output files found")
        
        # Check the content of the output file
        with open(output_files[0], 'r') as f:
            processed_doc = json.load(f)
        
        # Verify document has been processed
        self.assertEqual(processed_doc["content"], test_content)
        self.assertIn("state", processed_doc)
        
        # Verify document went through the pipeline stages
        # In a real test, you'd check for specific outputs at each stage
        if "state" in processed_doc:
            self.assertNotEqual(processed_doc["state"]["current_stage"], "created")