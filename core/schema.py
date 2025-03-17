# core/schema.py
from enum import Enum
from datetime import datetime
from typing import Optional, List, Dict, Any, UUID
from uuid import uuid4

class ProcessingStage(str, Enum):
    """Defines the valid processing stages a document can be in."""
    CREATED = "created"
    CAPTURED = "captured"
    CONTEXTUALIZED = "contextualized"
    CLARIFIED = "clarified"
    CATEGORIZED = "categorized"
    CRYSTALLIZED = "crystallized"
    CONNECTED = "connected"
    ERROR = "error"

class StateTransition:
    """Represents a transition from one state to another."""
    def __init__(self,
                 from_stage: ProcessingStage,
                 to_stage: ProcessingStage,
                 agent_id: str,
                 timestamp: datetime = None,
                 message: Optional[str] = None):
        self.from_stage = from_stage
        self.to_stage = to_stage
        self.agent_id = agent_id
        self.timestamp = timestamp or datetime.utcnow()
        self.message = message

class StateLock:
    """Represents a lock on a document for exclusive access."""
    def __init__(self,
                 locked_by: str,
                 acquired_at: datetime = None,
                 expires_at: datetime = None,
                 lock_id: str = None):
        self.locked_by = locked_by
        self.acquired_at = acquired_at or datetime.utcnow()
        self.expires_at = expires_at
        self.lock_id = lock_id or str(uuid4())

class DocumentState:
    """Represents the complete state of a document in the processing pipeline."""
    def __init__(self,
                 document_id: str,
                 current_stage: ProcessingStage = ProcessingStage.CREATED,
                 previous_stage: Optional[ProcessingStage] = None,
                 transition_history: List[StateTransition] = None,
                 lock: Optional[StateLock] = None,
                 metadata: Dict[str, Any] = None,
                 last_updated: datetime = None,
                 error_info: Optional[Dict[str, Any]] = None,
                 content_hash: Optional[str] = None,
                 version: int = 1):
        self.document_id = document_id
        self.current_stage = current_stage
        self.previous_stage = previous_stage
        self.transition_history = transition_history or []
        self.lock = lock
        self.metadata = metadata or {}
        self.last_updated = last_updated or datetime.utcnow()
        self.error_info = error_info
        self.content_hash = content_hash
        self.version = version