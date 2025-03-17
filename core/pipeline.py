# core/pipeline.py
import logging
import asyncio
from typing import List, Dict, Any, Optional
import uuid

from core.schema import (
    ProcessedDocument, TaskType, ProcessingStage,
    DocumentStatus, PipelineResults
)
from tasks.factory import TaskFactory
from llm.factory import LLMFactory

logger = logging.getLogger(__name__)

class Pipeline:
    """
    Orchestrates the document processing flow through various tasks.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Initialize factories
        self.llm_factory = LLMFactory()
        self.task_factory = TaskFactory(self.llm_factory)
        
        # Document storage
        self.documents: Dict[str, ProcessedDocument] = {}
        
        logger.info("Document processing pipeline initialized")
    
    async def process_document(self, document: ProcessedDocument, stages: Optional[List[TaskType]] = None) -> PipelineResults:
        """
        Process a document through specified stages of the pipeline.
        If stages is None, process through all stages.
        """
        logger.info(f"Processing document {document.id} through pipeline")
        
        # Store document if not already stored
        if document.id not in self.documents:
            self.documents[document.id] = document
        
        # Set default stages if not specified
        if stages is None:
            stages = [
                TaskType.CONTEXTUALIZER,
                TaskType.CLARIFIER,
                TaskType.CATEGORIZER,
                TaskType.CRYSTALLIZER,
                TaskType.CONNECTOR
            ]
        
        document.status = DocumentStatus.PROCESSING
        results = PipelineResults(
            document_id=str(document.id),
            task_results={},
            success=True,
            processed_stages=[]
        )
        
        try:
            # Process each stage
            for stage in stages:
                logger.info(f"Running {stage} task for document {document.id}")
                
                # Create and execute task
                task = self.task_factory.create_task(stage, self.config.get(f"{stage.value}_config"))
                
                # For connector task, include document corpus
                if stage == TaskType.CONNECTOR:
                    # Get other documents that have been processed through crystallization
                    document_corpus = [
                        doc for doc_id, doc in self.documents.items()
                        if doc_id != document.id and 
                        doc.processing_stage >= ProcessingStage.CRYSTALLIZED.value
                    ]
                    task_result = await task.execute(document, document_corpus)
                else:
                    task_result = await task.execute(document)
                
                # Store result
                results.task_results[stage.value] = task_result
                
                # Check for failure
                if not task_result.success:
                    logger.error(f"Task {stage} failed for document {document.id}: {task_result.error_message}")
                    results.success = False
                    results.error_message = f"Failed at {stage}: {task_result.error_message}"
                    document.status = DocumentStatus.ERROR
                    return results
                
                results.processed_stages.append(stage.value)
        
        except Exception as e:
            logger.error(f"Error processing document {document.id}: {str(e)}")
            results.success = False
            results.error_message = str(e)
            document.status = DocumentStatus.ERROR
            return results
        
        # Mark document as complete
        document.status = DocumentStatus.COMPLETED
        logger.info(f"Successfully processed document {document.id} through all stages")
        return results
    
    async def batch_process_documents(self, documents: List[ProcessedDocument], stages: Optional[List[TaskType]] = None) -> Dict[str, PipelineResults]:
        """
        Process multiple documents through the pipeline.
        """
        logger.info(f"Batch processing {len(documents)} documents")
        
        tasks = []
        for document in documents:
            tasks.append(self.process_document(document, stages))
        
        # Process documents concurrently
        results_list = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Organize results by document ID
        results_dict = {}
        for i, result in enumerate(results_list):
            if isinstance(result, Exception):
                # Handle exception
                document_id = str(documents[i].id)
                logger.error(f"Error processing document {document_id}: {str(result)}")
                results_dict[document_id] = PipelineResults(
                    document_id=document_id,
                    task_results={},
                    success=False,
                    error_message=str(result)
                )
            else:
                results_dict[result.document_id] = result
        
        return results_dict
    
    def get_document(self, document_id: str) -> Optional[ProcessedDocument]:
        """
        Retrieve a document by ID.
        """
        return self.documents.get(document_id)
    
    def add_document(self, document: ProcessedDocument) -> None:
        """
        Add a document to the pipeline storage.
        """
        self.documents[document.id] = document
        logger.debug(f"Added document {document.id} to pipeline storage")
    
    def create_document(self, content: str, metadata: Dict[str, Any] = None) -> ProcessedDocument:
        """
        Create a new processed document and add it to storage.
        """
        document_id = str(uuid.uuid4())
        document = ProcessedDocument(
            id=document_id,
            content=content,
            metadata=metadata or {},
            status=DocumentStatus.PENDING,
            processing_stage=ProcessingStage.INITIAL.value
        )
        
        self.add_document(document)
        logger.info(f"Created new document with ID {document_id}")
        return document