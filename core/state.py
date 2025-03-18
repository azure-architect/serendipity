# core/state.py
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Any
import uuid
import asyncio
from enum import Enum

from .schema import (
    DocumentState, ProcessingStage, StateTransition, 
    StateLock, ProcessedDocument
)

logger = logging.getLogger(__name__)


class LockError(Exception):
    """Exception raised for errors in document locking."""
    pass


class StateManager:
    """
    Manages document state transitions and locking.
    """
    
    def __init__(self, storage_interface=None):
        self.storage = storage_interface
        self.locks = {}  # In-memory tracking of locks
        self.lock_timeout = timedelta(minutes=10)  # Default lock timeout
    
    async def get_document_state(self, document_id: str) -> Optional[DocumentState]:
        """
        Get the current state of a document.
        """
        if self.storage:
            return await self.storage.get_document_state(document_id)
        return None
        
    async def transition_state(self, 
                              document_id: str, 
                              to_stage: ProcessingStage, 
                              agent_id: str, 
                              message: Optional[str] = None) -> DocumentState:
        """
        Transition a document to a new processing stage.
        """
        # Get current state
        doc_state = await self.get_document_state(document_id)
        if not doc_state:
            raise ValueError(f"Document {document_id} not found")
            
        # Check if document is locked
        if doc_state.lock and doc_state.lock.locked_by != agent_id:
            raise LockError(f"Document {document_id} is locked by {doc_state.lock.locked_by}")
            
        # Create transition record
        transition = StateTransition(
            from_stage=doc_state.current_stage,
            to_stage=to_stage,
            agent_id=agent_id,
            timestamp=datetime.utcnow(),
            message=message
        )
        
        # Log the transition
        logger.info(f"Document {document_id} transitioning from {doc_state.current_stage.value} to {to_stage.value} by {agent_id}")
        
        # Update state
        doc_state.previous_stage = doc_state.current_stage
        doc_state.current_stage = to_stage
        doc_state.transition_history.append(transition)
        doc_state.last_updated = datetime.utcnow()
        
        # Save updated state
        if self.storage:
            await self.storage.save_document_state(doc_state)
            
        return doc_state
        
    async def lock_document(self, 
                           document_id: str, 
                           agent_id: str, 
                           timeout_minutes: int = None) -> StateLock:
        """
        Lock a document for exclusive access.
        """
        # Get current state
        doc_state = await self.get_document_state(document_id)
        if not doc_state:
            raise ValueError(f"Document {document_id} not found")
            
        # Check if already locked
        if doc_state.lock:
            # Check if lock expired
            if doc_state.lock.expires_at > datetime.utcnow():
                raise LockError(f"Document {document_id} is already locked by {doc_state.lock.locked_by}")
                
        # Create new lock
        timeout = timeout_minutes or self.lock_timeout.total_seconds() / 60
        lock = StateLock(
            locked_by=agent_id,
            acquired_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(minutes=timeout),
            lock_id=uuid.uuid4()
        )
        
        # Update state
        doc_state.lock = lock
        doc_state.last_updated = datetime.utcnow()
        
        # Save updated state
        if self.storage:
            await self.storage.save_document_state(doc_state)
            
        # Track lock in memory
        self.locks[document_id] = lock
            
        return lock
        
    async def unlock_document(self, document_id: str, agent_id: str) -> bool:
        """
        Unlock a document.
        """
        # Get current state
        doc_state = await self.get_document_state(document_id)
        if not doc_state:
            raise ValueError(f"Document {document_id} not found")
            
        # Check if locked by this agent
        if not doc_state.lock:
            return True  # Already unlocked
            
        if doc_state.lock.locked_by != agent_id:
            raise LockError(f"Document {document_id} is locked by {doc_state.lock.locked_by}, not {agent_id}")
            
        # Remove lock
        doc_state.lock = None
        doc_state.last_updated = datetime.utcnow()
        
        # Save updated state
        if self.storage:
            await self.storage.save_document_state(doc_state)
            
        # Remove from in-memory tracking
        if document_id in self.locks:
            del self.locks[document_id]
            
        return True
        
    async def refresh_lock(self, document_id: str, agent_id: str) -> StateLock:
        """
        Refresh a document lock to prevent expiration.
        """
        # Get current state
        doc_state = await self.get_document_state(document_id)
        if not doc_state or not doc_state.lock:
            raise LockError(f"Document {document_id} is not locked")
            
        # Check if locked by this agent
        if doc_state.lock.locked_by != agent_id:
            raise LockError(f"Document {document_id} is locked by {doc_state.lock.locked_by}, not {agent_id}")
            
        # Refresh lock
        timeout_minutes = self.lock_timeout.total_seconds() / 60
        doc_state.lock.expires_at = datetime.utcnow() + timedelta(minutes=timeout_minutes)
        doc_state.last_updated = datetime.utcnow()
        
        # Save updated state
        if self.storage:
            await self.storage.save_document_state(doc_state)
            
        # Update in-memory tracking
        self.locks[document_id] = doc_state.lock
            
        return doc_state.lock
        
    async def check_expired_locks(self):
        """
        Check for and clean up expired locks.
        """
        now = datetime.utcnow()
        expired_locks = []
        
        for document_id, lock in self.locks.items():
            if lock.expires_at <= now:
                expired_locks.append(document_id)
                
        for document_id in expired_locks:
            doc_state = await self.get_document_state(document_id)
            if doc_state and doc_state.lock:
                doc_state.lock = None
                doc_state.last_updated = now
                logger.info(f"Removed expired lock for document {document_id}")
                
                if self.storage:
                    await self.storage.save_document_state(doc_state)
                    
            if document_id in self.locks:
                del self.locks[document_id]