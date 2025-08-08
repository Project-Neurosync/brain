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
            namespace: Optional namespace/collection to get document from
            
        Returns:
            Document if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def search(
        self,
        query: str,
        k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None,
        namespace: Optional[str] = None
    ) -> List[SearchResult]:
        """
        Search for documents similar to the query.
        
        Args:
            query: The search query
            k: Number of results to return
            filter_metadata: Optional metadata filter
            namespace: Optional namespace/collection to search in
            
        Returns:
            List of search results with documents and similarity scores
        """
        pass
    
    @abstractmethod
    async def search_by_vector(
        self,
        embedding: List[float],
        k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None,
        namespace: Optional[str] = None
    ) -> List[SearchResult]:
        """
        Search for documents using a vector embedding.
        
        Args:
            embedding: The query embedding vector
            k: Number of results to return
            filter_metadata: Optional metadata filter
            namespace: Optional namespace/collection to search in
            
        Returns:
            List of search results with documents and similarity scores
        """
        pass
    
    @abstractmethod
    async def delete(
        self,
        document_ids: List[str],
        namespace: Optional[str] = None
    ) -> bool:
        """
        Delete documents by ID.
        
        Args:
            document_ids: List of document IDs to delete
            namespace: Optional namespace/collection to delete from
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def delete_namespace(
        self,
        namespace: str
    ) -> bool:
        """
        Delete an entire namespace/collection.
        
        Args:
            namespace: Namespace/collection to delete
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def get_namespaces(self) -> List[str]:
        """
        Get all available namespaces/collections.
        
        Returns:
            List of namespace/collection names
        """
        pass
