"""
Base abstract class for vector store implementations.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union, Tuple
from pydantic import BaseModel


class Document(BaseModel):
    """Document model with content and metadata."""
    id: str
    content: str
    metadata: Dict[str, Any] = {}
    embedding: Optional[List[float]] = None


class SearchResult(BaseModel):
    """Search result model."""
    document: Document
    score: float


class BaseVectorStore(ABC):
    """Abstract base class for vector store implementations."""
    
    @abstractmethod
    async def add_documents(
        self, 
        documents: List[Document],
        namespace: Optional[str] = None
    ) -> List[str]:
        """
        Add documents to the vector store.
        
        Args:
            documents: List of documents to add
            namespace: Optional namespace/collection to add documents to
            
        Returns:
            List of document IDs that were added
        """
        pass
    
    @abstractmethod
    async def get_document(
        self,
        document_id: str,
        namespace: Optional[str] = None
    ) -> Optional[Document]:
        """
        Get a document by ID.
        
        Args:
            document_id: ID of the document to retrieve
            namespace: Optional namespace/collection to search in
            
        Returns:
            Document if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def delete_document(
        self,
        document_id: str,
        namespace: Optional[str] = None
    ) -> bool:
        """
        Delete a document by ID.
        
        Args:
            document_id: ID of the document to delete
            namespace: Optional namespace/collection to delete from
            
        Returns:
            True if document was deleted, False if not found
        """
        pass
    
    @abstractmethod
    async def search(
        self,
        query_embedding: List[float],
        top_k: int = 10,
        namespace: Optional[str] = None,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """
        Search for similar documents using vector similarity.
        
        Args:
            query_embedding: Query vector to search with
            top_k: Number of top results to return
            namespace: Optional namespace/collection to search in
            filter_metadata: Optional metadata filters
            
        Returns:
            List of search results ordered by similarity score
        """
        pass
    
    @abstractmethod
    async def search_by_text(
        self,
        query_text: str,
        top_k: int = 10,
        namespace: Optional[str] = None,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """
        Search for similar documents using text query.
        
        Args:
            query_text: Text query to search with
            top_k: Number of top results to return
            namespace: Optional namespace/collection to search in
            filter_metadata: Optional metadata filters
            
        Returns:
            List of search results ordered by similarity score
        """
        pass
    
    @abstractmethod
    async def list_namespaces(self) -> List[str]:
        """
        List all available namespaces.
        
        Returns:
            List of namespace names
        """
        pass
    
    @abstractmethod
    async def delete_namespace(self, namespace: str) -> bool:
        """
        Delete an entire namespace and all its documents.
        
        Args:
            namespace: Name of the namespace to delete
            
        Returns:
            True if namespace was deleted, False if not found
        """
        pass
    
    @abstractmethod
    async def get_stats(self, namespace: Optional[str] = None) -> Dict[str, Any]:
        """
        Get statistics about the vector store.
        
        Args:
            namespace: Optional namespace to get stats for
            
        Returns:
            Dictionary with statistics
        """
        pass
