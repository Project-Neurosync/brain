"""
Enhanced retriever service for RAG applications.

This service combines embedding generation with vector store retrieval to provide
a comprehensive document retrieval system with advanced filtering and re-ranking.
"""

import asyncio
from typing import Dict, List, Any, Optional, Union, Tuple
import uuid
import logging

from app.core.config import settings
from app.services.vectorstore.base import BaseVectorStore, Document, SearchResult
from app.services.embedding.factory import embedding_service
from app.services.vectorstore.pinecone import PineconeVectorStore

# Set up logger
logger = logging.getLogger(__name__)


class RetrieverService:
    """Enhanced retrieval service for RAG applications."""
    
    def __init__(
        self,
        vector_store: Optional[BaseVectorStore] = None,
    ):
        """
        Initialize the retriever service.
        
        Args:
            vector_store: Vector store implementation. If not provided,
                         a PineconeVectorStore will be created.
        """
        self.vector_store = vector_store or PineconeVectorStore()
        self.embedding_service = embedding_service
    
    async def add_texts(
        self,
        texts: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        namespace: Optional[str] = None,
        document_ids: Optional[List[str]] = None,
    ) -> List[str]:
        """
        Add texts to the vector store with embeddings.
        
        Args:
            texts: List of text contents to add
            metadatas: Optional list of metadata dictionaries for each text
            namespace: Optional namespace to add documents to
            document_ids: Optional list of document IDs to use
            
        Returns:
            List of document IDs that were added
        """
        # Generate embeddings for all texts
        embeddings = await self.embedding_service.embed_documents(texts)
        
        # Create document objects
        documents = []
        for i, (text, embedding) in enumerate(zip(texts, embeddings)):
            # Get or generate document ID
            doc_id = None
            if document_ids and i < len(document_ids):
                doc_id = document_ids[i]
            if not doc_id:
                doc_id = str(uuid.uuid4())
                
            # Get metadata if available
            metadata = {}
            if metadatas and i < len(metadatas):
                metadata = metadatas[i]
                
            # Create document
            document = Document(
                id=doc_id,
                content=text,
                metadata=metadata,
                embedding=embedding
            )
            documents.append(document)
            
        # Add documents to vector store
        try:
            return await self.vector_store.add_documents(documents, namespace)
        except Exception as e:
            logger.error(f"Error adding documents to vector store: {e}")
            return []
    
    async def similarity_search(
        self,
        query: str,
        k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None,
        namespace: Optional[str] = None,
        rerank: bool = False,
    ) -> List[Document]:
        """
        Search for documents similar to the query text.
        
        Args:
            query: The search query
            k: Number of documents to return
            filter_metadata: Optional metadata filter
            namespace: Optional namespace to search in
            rerank: Whether to rerank results using additional criteria
            
        Returns:
            List of retrieved documents
        """
        try:
            # Generate query embedding
            query_embedding = await self.embedding_service.embed_query(query)
            
            # Search by vector
            results = await self.vector_store.search_by_vector(
                embedding=query_embedding,
                k=k if not rerank else k * 2,  # Get more results if reranking
                filter_metadata=filter_metadata,
                namespace=namespace
            )
            
            # Extract documents from search results
            documents = [result.document for result in results]
            
            # Apply reranking if requested
            if rerank and documents:
                documents = await self._rerank_results(query, documents)
                documents = documents[:k]  # Trim to requested number
                
            return documents
            
        except Exception as e:
            logger.error(f"Error in similarity search: {e}")
            return []
    
    async def _rerank_results(
        self,
        query: str,
        documents: List[Document],
    ) -> List[Document]:
        """
        Rerank results using additional criteria beyond vector similarity.
        
        Args:
            query: The original search query
            documents: The documents to rerank
            
        Returns:
            Reranked list of documents
        """
        # This is a placeholder for more advanced reranking logic
        # In a production system, this would use techniques like:
        # - BM25 or other keyword matching
        # - Query-document term overlap
        # - Document freshness
        # - Document authority/source quality
        # - Cross-encoder reranking
        
        # Simple term overlap scoring as an example
        reranked = []
        query_terms = set(query.lower().split())
        
        for doc in documents:
            # Calculate term overlap score
            doc_terms = set(doc.content.lower().split())
            overlap = len(query_terms.intersection(doc_terms))
            
            # Combine with existing score if available
            score = overlap
            if hasattr(doc, "score") and doc.score is not None:
                score = doc.score * 0.7 + overlap * 0.3
                
            # Store score in document metadata for sorting
            if "metadata" not in doc:
                doc.metadata = {}
            doc.metadata["rerank_score"] = score
            reranked.append(doc)
            
        # Sort by rerank score
        reranked.sort(key=lambda d: d.metadata.get("rerank_score", 0), reverse=True)
        return reranked
    
    async def delete_documents(
        self,
        document_ids: List[str],
        namespace: Optional[str] = None,
    ) -> bool:
        """
        Delete documents from the vector store.
        
        Args:
            document_ids: List of document IDs to delete
            namespace: Optional namespace to delete from
            
        Returns:
            True if successful, False otherwise
        """
        try:
            return await self.vector_store.delete(document_ids, namespace)
        except Exception as e:
            logger.error(f"Error deleting documents: {e}")
            return False
    
    async def get_document(
        self,
        document_id: str,
        namespace: Optional[str] = None,
    ) -> Optional[Document]:
        """
        Get a document by ID.
        
        Args:
            document_id: Document ID to retrieve
            namespace: Optional namespace to get from
            
        Returns:
            Document if found, None otherwise
        """
        try:
            return await self.vector_store.get_document(document_id, namespace)
        except Exception as e:
            logger.error(f"Error getting document: {e}")
            return None
