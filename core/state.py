# core/pipeline.py
import logging
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime

from .schema import ProcessingStage, DocumentState
from .state import StateManager, LockError

logger = logging.getLogger(__name__)

class Pipeline:
    """Orchestrates the document processing pipeline."""
    
    def __init__(self, task_factory, state_manager=None, storage=None):
        """Initialize the pipeline.
        
        Args:
            task_factory: Factory for creating task processors
            state_manager: Optional state manager for tracking document states
            storage: Optional storage backend for persisting documents
        """
        self.task_factory = task_factory
        self.state_manager = state_manager or StateManager(storage)
        self.storage = storage
        self.hooks = {}  # Hooks for pipeline events
        
        # Define the standard processing sequence
        self.stage_sequence = [
            ProcessingStage.CREATED,
            ProcessingStage.CAPTURED,
            ProcessingStage.CONTEXTUALIZED,
            ProcessingStage.CLARIFIED,
            ProcessingStage.CATEGORIZED,
            ProcessingStage.CRYSTALLIZED,
            ProcessingStage.CONNECTED
        ]
        
        # Map stages to task names
        self.stage_to_task = {
            ProcessingStage.CAPTURED: "capture",
            ProcessingStage.CONTEXTUALIZED: "contextualize",
            ProcessingStage.CLARIFIED: "clarify", 
            ProcessingStage.CATEGORIZED: "categorize",
            ProcessingStage.CRYSTALLIZED: "crystallize",
            ProcessingStage.CONNECTED: "connect"
        }
    
    def process(self, document, start_stage=None, end_stage=None, agent_id="pipeline"):
        """Process a document through the pipeline.
        
        Args:
            document: The document to process
            start_stage: Optional stage to start processing from
            end_stage: Optional stage to stop processing at
            agent_id: ID of the agent initiating the processing
            
        Returns:
            The processed document
        """
        # Get current document state or create new one
        doc_state = self._get_or_create_state(document)
        
        # Determine start and end stages
        current_stage = doc_state.current_stage
        start_idx = self.stage_sequence.index(current_stage) if start_stage is None else self.stage_sequence.index(start_stage)
        
        if end_stage:
            end_idx = self.stage_sequence.index(end_stage)
        else:
            end_idx = len(self.stage_sequence) - 1
        
        # Process document through each stage
        for stage_idx in range(start_idx, end_idx + 1):
            # Get current and next stage
            if stage_idx == 0:
                # Skip processing for CREATED stage since there's no task
                continue
                
            current_stage = self.stage_sequence[stage_idx - 1]
            next_stage = self.stage_sequence[stage_idx]
            
            # Skip if document is already in or past this stage
            if self.stage_sequence.index(doc_state.current_stage) >= stage_idx:
                continue
            
            # Get the task for this stage transition
            task_name = self.stage_to_task.get(next_stage)
            if not task_name:
                logger.warning(f"No task defined for stage {next_stage}, skipping")
                continue
                
            task = self.task_factory.get_task(task_name)
            if not task:
                logger.warning(f"Task '{task_name}' not found, skipping stage {next_stage}")
                continue
            
            # Lock document for processing
            try:
                self.state_manager.lock_document(document.id, agent_id)
            except LockError as e:
                logger.error(f"Could not lock document for processing: {e}")
                return document
            
            try:
                # Process document with the task
                logger.info(f"Processing document {document.id} with task '{task_name}'")
                document = task.process(document)
                
                # Transition document state
                doc_state = self.state_manager.transition_state(
                    document_id=document.id,
                    from_stage=current_stage,
                    to_stage=next_stage,
                    agent_id=agent_id,
                    message=f"Processed with {task_name} task"
                )
                
                # Update document with new state
                document.state = doc_state
                
                # Persist document if storage is available
                if self.storage:
                    self.storage.save_document(document)
                
                # Trigger any hooks for this stage
                self._trigger_hooks(next_stage, document)
                
            except Exception as e:
                logger.error(f"Error processing document {document.id} with task '{task_name}': {e}")
                
                # Transition to error state
                try:
                    doc_state = self.state_manager.transition_state(
                        document_id=document.id,
                        from_stage=current_stage,
                        to_stage=ProcessingStage.ERROR,
                        agent_id=agent_id,
                        message=f"Error in {task_name} task: {str(e)}"
                    )
                    document.state = doc_state
                    
                    # Store error info
                    document.state.error_info = {
                        "stage": next_stage,
                        "task": task_name,
                        "error": str(e),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    
                    # Persist document if storage is available
                    if self.storage:
                        self.storage.save_document(document)
                    
                    # Trigger error hooks
                    self._trigger_hooks("error", document)
                    
                except Exception as state_error:
                    logger.error(f"Error transitioning document to error state: {state_error}")
                
                return document
            finally:
                # Release lock
                try:
                    self.state_manager.release_lock(document.id, agent_id)
                except Exception as unlock_error:
                    logger.error(f"Error releasing document lock: {unlock_error}")
        
        return document
    
    def register_hook(self, stage: str, hook: Callable):
        """Register a hook to be called when a document reaches a stage.
        
        Args:
            stage: The stage to hook into
            hook: Callable to invoke with the document as argument
        """
        if stage not in self.hooks:
            self.hooks[stage] = []
        self.hooks[stage].append(hook)
    
    def _trigger_hooks(self, stage: str, document):
        """Trigger any hooks registered for a stage.
        
        Args:
            stage: The stage that was reached
            document: The document to pass to hooks
        """
        hooks = self.hooks.get(stage, [])
        for hook in hooks:
            try:
                hook(document)
            except Exception as e:
                logger.error(f"Error in hook for stage {stage}: {e}")
    
    def _get_or_create_state(self, document):
        """Get or create a state for the document.
        
        Args:
            document: The document to get state for
            
        Returns:
            The document state
        """
        # If document already has a state, use it
        if hasattr(document, 'state') and document.state:
            return document.state
        
        # Try to get state from state manager
        doc_state = self.state_manager.get_document_state(document.id)
        
        # Create new state if none exists
        if not doc_state:
            doc_state = DocumentState(
                document_id=document.id,
                current_stage=ProcessingStage.CREATED,
                transition_history=[]
            )
        
        # Update document with state
        document.state = doc_state
        
        return doc_state