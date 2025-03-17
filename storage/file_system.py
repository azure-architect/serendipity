# storage/file_system.py
import os
import json
import asyncio
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime
import shutil
from uuid import UUID

from core.schema import (
    ProcessedDocument, DocumentState, ProcessingStage,
    StateTransition, StateLock
)

logger = logging.getLogger(__name__)


class FileSystemStorage:
    """
    File system implementation of document storage.
    """
    
    def __init__(self, base_path: str):
        self.base_path = base_path
        self.documents_path = os.path.join(base_path, "documents")
        self.states_path = os.path.join(base_path, "states")
        
        # Ensure directories exist
        os.makedirs(self.documents_path, exist_ok=True)
        os.makedirs(self.states_path, exist_ok=True)
        
        logger.info(f"Initialized file system storage at {base_path}")
    
    async def save_document(self, document: ProcessedDocument) -> str:
        """
        Save a document to the file system.
        """
        document_id = str(document.id)
        document_path = os.path.join(self.documents_path, f"{document_id}.json")
        
        # Update timestamp
        document.state.last_updated = datetime.utcnow()
        
        # Save document to file
        with open(document_path, "w", encoding="utf-8") as f:
            f.write(document.model_dump_json(indent=2))
        
        logger.debug(f"Saved document {document_id} to {document_path}")
        return document_id
    
    async def get_document(self, document_id: str) -> Optional[ProcessedDocument]:
        """
        Retrieve a document from the file system.
        """
        document_path = os.path.join(self.documents_path, f"{document_id}.json")
        
        if not os.path.exists(document_path):
            logger.warning(f"Document {document_id} not found at {document_path}")
            return None
        
        try:
            with open(document_path, "r", encoding="utf-8") as f:
                document_data = json.load(f)
            
            # Deserialize to ProcessedDocument
            document = ProcessedDocument.model_validate(document_data)
            return document
            
        except Exception as e:
            logger.error(f"Error loading document {document_id}: {str(e)}")
            return None
    
    async def delete_document(self, document_id: str) -> bool:
        """
        Delete a document from the file system.
        """
        document_path = os.path.join(self.documents_path, f"{document_id}.json")
        state_path = os.path.join(self.states_path, f"{document_id}.json")
        
        success = True
        
        # Delete document file if it exists
        if os.path.exists(document_path):
            try:
                os.remove(document_path)
                logger.debug(f"Deleted document file {document_path}")
            except Exception as e:
                logger.error(f"Error deleting document file {document_path}: {str(e)}")
                success = False
        
        # Delete state file if it exists
        if os.path.exists(state_path):
            try:
                os.remove(state_path)
                logger.debug(f"Deleted state file {state_path}")
            except Exception as e:
                logger.error(f"Error deleting state file {state_path}: {str(e)}")
                success = False
        
        return success
    
    async def list_documents(self, 
                            stage: Optional[ProcessingStage] = None,
                            limit: int = 100) -> List[ProcessedDocument]:
        """
        List documents, optionally filtered by processing stage.
        """
        documents = []
        
        # List all document files
        for filename in os.listdir(self.documents_path):
            if not filename.endswith(".json"):
                continue
                
            document_id = filename.removesuffix(".json")
            document = await self.get_document(document_id)
            
            if document:
                # Filter by stage if specified
                if stage and document.state.current_stage != stage:
                    continue
                    
                documents.append(document)
                
                # Respect the limit
                if len(documents) >= limit:
                    break
        
        return documents
    
    async def save_document_state(self, state: DocumentState) -> bool:
        """
        Save a document state to the file system.
        """
        document_id = state.document_id
        state_path = os.path.join(self.states_path, f"{document_id}.json")
        
        # Update timestamp
        state.last_updated = datetime.utcnow()
        
        # Save state to file
        try:
            with open(state_path, "w", encoding="utf-8") as f:
                f.write(state.model_dump_json(indent=2))
            
            logger.debug(f"Saved document state {document_id} to {state_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving document state {document_id}: {str(e)}")
            return False
    
    async def get_document_state(self, document_id: str) -> Optional[DocumentState]:
        """
        Retrieve a document state from the file system.
        """
        state_path = os.path.join(self.states_path, f"{document_id}.json")
        
        if not os.path.exists(state_path):
            # Check if the document exists but state doesn't
            document_path = os.path.join(self.documents_path, f"{document_id}.json")
            if os.path.exists(document_path):
                # Get state from document
                document = await self.get_document(document_id)
                if document:
                    return document.state
            
            logger.warning(f"Document state {document_id} not found at {state_path}")
            return None
        
        try:
            with open(state_path, "r", encoding="utf-8") as f:
                state_data = json.load(f)
            
            # Deserialize to DocumentState
            state = DocumentState.model_validate(state_data)
            return state
            
        except Exception as e:
            logger.error(f"Error loading document state {document_id}: {str(e)}")
            return None
    
    async def get_documents_by_criteria(self, 
                                      locked: bool = None,
                                      error_state: bool = None,
                                      stage: Optional[ProcessingStage] = None,
                                      limit: int = 100) -> List[ProcessedDocument]:
        """
        Get documents matching specific criteria.
        """
        all_documents = await self.list_documents(limit=limit)
        filtered_documents = []
        
        for document in all_documents:
            # Apply filters
            if locked is not None and bool(document.state.lock) != locked:
                continue
                
            if error_state is not None:
                is_error = document.state.current_stage == ProcessingStage.ERROR
                if is_error != error_state:
                    continue
            
            if stage is not None and document.state.current_stage != stage:
                continue
                
            filtered_documents.append(document)
            
            # Respect the limit
            if len(filtered_documents) >= limit:
                break
        
        return filtered_documents