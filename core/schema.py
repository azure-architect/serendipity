# core/schema.py
from enum import Enum
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from uuid import uuid4, UUID


class VectorizedModel(BaseModel):
    """Base class for models that include vector embeddings."""
    embedding: Optional[List[float]] = None
    embedding_model: Optional[str] = None
    embedding_dimension: Optional[int] = None
    embedding_updated_at: Optional[datetime] = None


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


class StateTransition(VectorizedModel):
    """Represents a transition from one state to another."""
    from_stage: ProcessingStage
    to_stage: ProcessingStage
    agent_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    message: Optional[str] = None


class AgentAccess(VectorizedModel):
    """Defines which agents can access and modify documents at each stage."""
    stage: ProcessingStage
    read_access: List[str] = []  # List of agent IDs with read access
    write_access: List[str] = []  # List of agent IDs with write/transition access


class StateLock(VectorizedModel):
    """Represents a lock on a document for exclusive access."""
    locked_by: str  # Agent ID
    acquired_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime
    lock_id: UUID = Field(default_factory=uuid4)


class DocumentState(VectorizedModel):
    """Represents the complete state of a document in the processing pipeline."""
    document_id: str
    current_stage: ProcessingStage = ProcessingStage.CREATED
    previous_stage: Optional[ProcessingStage] = None
    transition_history: List[StateTransition] = []
    lock: Optional[StateLock] = None
    metadata: Dict[str, Any] = {}
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    error_info: Optional[Dict[str, Any]] = None
    content_hash: Optional[str] = None  # For change detection
    version: int = 1

    model_config = {
        "validate_assignment": True
    }

    @field_validator('transition_history')
    def validate_transition_history(cls, v, info):
        """Validate that transition history matches current stage."""
        if not v:
            return v
        
        # Check that the last transition matches the current state
        values = info.data
        if 'current_stage' in values and v and v[-1].to_stage != values['current_stage']:
            raise ValueError("Last transition doesn't match current stage")
        return v


class ContentMetadata(VectorizedModel):
    """Metadata about the content being processed."""
    raw_content: str
    source_type: str  # idea/task/youtube/claude
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    creator: Optional[str] = None
    input_format: Optional[str] = None


class ContextualizationData(VectorizedModel):
    """Data produced by the contextualization agent."""
    document_type: Optional[str] = None
    topics: List[str] = []
    entities: List[str] = []
    related_domains: List[str] = []
    context_notes: Optional[str] = None


class ClarificationData(VectorizedModel):
    """Data produced by the clarification agent."""
    summary: Optional[str] = None
    key_points: List[str] = []
    questions_addressed: List[str] = []
    ambiguities_resolved: List[str] = []
    structured_representation: Optional[Dict[str, Any]] = None


class CrystallizationData(VectorizedModel):
    """Data produced by the crystallization agent."""
    insights: List[str] = []
    action_items: List[str] = []
    implications: List[str] = []
    potential_applications: List[str] = []
    value_assessment: Optional[str] = None


class FragmentEmbedding(VectorizedModel):
    """Represents an embedding for a specific content fragment."""
    fragment: str
    fragment_embedding: List[float]  # Specific to the fragment


class VectorizationData(VectorizedModel):
    """Data produced by the vectorization agent."""
    embedding_model: Optional[str] = None
    embedding_dimension: Optional[int] = None
    semantic_coordinates: Optional[Dict[str, Any]] = None
    fragment_embeddings: List[FragmentEmbedding] = []


class ConnectionMapEntry(VectorizedModel):
    """Represents a connection to another document."""
    target_id: UUID
    relationship: str
    strength: float
    connection_type: Optional[str] = None
    bidirectional: bool = False
    discovered_at: datetime = Field(default_factory=datetime.utcnow)
    discovered_by: Optional[str] = None
    context: Optional[str] = None
    confidence: float = 1.0
    tags: List[str] = []
    metadata: Dict[str, Any] = {}


class DatabaseData(VectorizedModel):
    """Data produced by the database agent."""
    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    version: int = 1
    tags: List[str] = []
    connection_map: List[ConnectionMapEntry] = []


class ProcessedDocument(VectorizedModel):
    """A complete document that has been processed through the pipeline."""
    # Core document identification
    id: UUID = Field(default_factory=uuid4)
    original_filename: Optional[str] = None
    original_path: Optional[str] = None
    
    # Current state tracking
    processing_stage: str  # Current stage in the pipeline
    processing_history: List[Dict[str, Any]] = []  # Log of all processing steps
    
    # Content at each stage of processing
    content: str  # The original raw content
    ingest: ContentMetadata
    contextualize: Optional[ContextualizationData] = None
    clarify: Optional[ClarificationData] = None
    crystallize: Optional[CrystallizationData] = None
    vectorize: Optional[VectorizationData] = None
    database: Optional[DatabaseData] = None
    
    # Agent results
    capture_results: Optional[str] = None
    contextualize_results: Optional[str] = None
    clarify_results: Optional[str] = None
    categorize_results: Optional[str] = None
    crystallize_results: Optional[str] = None
    connect_results: Optional[str] = None
    
    # State management
    state: DocumentState


# Additional types that might be used in other parts of the system
class TaskType(str, Enum):
    """Types of tasks in the processing pipeline."""
    CONTEXTUALIZER = "contextualizer"
    CLARIFIER = "clarifier"
    CATEGORIZER = "categorizer"
    CRYSTALLIZER = "crystallizer"
    CONNECTION_MAPPER = "connection_mapper"


class LLMType(str, Enum):
    """Types of LLMs supported by the system."""
    OLLAMA = "ollama"
    OPENAI = "openai"
    # Add other LLM providers as needed


class LLMConfig(BaseModel):
    """Configuration for an LLM."""
    llm_type: LLMType
    model_name: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    

class LLMResponse(BaseModel):
    """Response from an LLM."""
    content: str
    raw_response: Dict[str, Any] = Field(default_factory=dict)
    processing_time: float
    token_usage: Optional[Dict[str, int]] = None


class TaskResult(BaseModel):
    """Result from a task execution."""
    task_type: TaskType
    success: bool
    document_id: str
    result_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    processing_time: float  # in seconds