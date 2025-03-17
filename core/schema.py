# core/schema.py
from enum import Enum
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field

class ProcessingStage(Enum):
    """Enum for the different processing stages of a thought."""
    INITIAL = "initial"
    CAPTURED = "captured"
    CONTEXTUALIZED = "contextualized"
    CLARIFIED = "clarified"
    CATEGORIZED = "categorized"
    CRYSTALLIZED = "crystallized"
    CONNECTED = "connected"

class TaskType(Enum):
    """Enum for the different types of tasks."""
    CONTEXTUALIZER = "contextualizer"
    CLARIFIER = "clarifier"
    CATEGORIZER = "categorizer"
    CRYSTALLIZER = "crystallizer"
    CONNECTOR = "connector"

class LLMType(Enum):
    """Enum for the different types of LLMs."""
    OLLAMA = "ollama"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"

class DocumentStatus(Enum):
    """Enum for the different statuses of a document."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"

class LLMConfig(BaseModel):
    """Configuration for an LLM."""
    llm_type: LLMType
    model_name: str
    parameters: Dict[str, Any] = Field(default_factory=dict)

class LLMResponse(BaseModel):
    """Response from an LLM."""
    content: str
    raw_response: Optional[Dict[str, Any]] = None
    processing_time: float = 0.0
    token_usage: Optional[Dict[str, int]] = None

class DocumentConnection(BaseModel):
    """Connection between documents."""
    document_id: str
    connection_type: str = "related"
    strength: int = 5  # 1-10 scale

class ContextualizationData(BaseModel):
    """Data structure for contextualizing a document."""
    document_type: Optional[str] = None
    topics: List[str] = Field(default_factory=list)
    entities: List[str] = Field(default_factory=list)
    related_domains: List[str] = Field(default_factory=list)
    context_notes: Optional[str] = None

class ClarificationData(BaseModel):
    """Data structure for clarifying a document."""
    complex_terms: Dict[str, str] = Field(default_factory=dict)
    ambiguous_concepts: List[str] = Field(default_factory=list)
    implicit_assumptions: List[str] = Field(default_factory=list)
    clarification_notes: str = ""

class CategorizationData(BaseModel):
    """Data structure for categorizing a document."""
    primary_category: Optional[str] = None
    secondary_categories: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    relevance_scores: Dict[str, int] = Field(default_factory=dict)
    classification_notes: str = ""

class CrystallizationData(BaseModel):
    """Data structure for crystallizing a document."""
    executive_summary: str = ""
    key_points: List[str] = Field(default_factory=list)
    core_concepts: List[str] = Field(default_factory=list)
    conclusions: List[str] = Field(default_factory=list)
    questions_raised: List[str] = Field(default_factory=list)

class ConnectionData(BaseModel):
    """Data structure for connecting a document to other documents or concepts."""
    related_concepts: List[str] = Field(default_factory=list)
    potential_references: List[str] = Field(default_factory=list)
    document_connections: List[DocumentConnection] = Field(default_factory=list)
    dependency_chain: List[str] = Field(default_factory=list)
    connection_notes: str = ""

class ProcessStage(BaseModel):
    """Represents a single stage in the processing history."""
    stage: str
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

class ProcessedDocument(BaseModel):
    """Represents a processed document with all its metadata and processing information."""
    id: str
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    status: DocumentStatus = DocumentStatus.PENDING
    processing_stage: str = ProcessingStage.INITIAL.value
    processing_history: List[ProcessStage] = Field(default_factory=list)
    
    # Results from each processing stage
    contextualize: Optional[ContextualizationData] = None
    contextualize_results: Optional[str] = None
    
    clarification: Optional[ClarificationData] = None
    clarification_results: Optional[str] = None
    
    categorization: Optional[CategorizationData] = None
    categorization_results: Optional[str] = None
    
    crystallization: Optional[CrystallizationData] = None
    crystallization_results: Optional[str] = None
    
    connection: Optional[ConnectionData] = None
    connection_results: Optional[str] = None

class TaskResult(BaseModel):
    """Result of a task execution."""
    task_type: TaskType
    success: bool
    document_id: str
    result_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    processing_time: float = 0.0

class PipelineResults(BaseModel):
    """Results of a pipeline execution."""
    document_id: str
    task_results: Dict[str, TaskResult] = Field(default_factory=dict)
    success: bool = True
    error_message: Optional[str] = None
    processed_stages: List[str] = Field(default_factory=list)