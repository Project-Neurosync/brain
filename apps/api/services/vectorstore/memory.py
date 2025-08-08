"""
In-memory vector store implementation for NeuroSync RAG system.
Provides a simple in-memory vector store for development and testing.
"""

import logging
from typing import List, Dict, Any, Optional
import asyncio

from .base import BaseVectorStore

logger = logging.getLogger(__name__)

class MemoryVectorStore(BaseVectorStore):
    """In-memory implementation of vector store for development/testing."""
    
    def __init__(self):
        """Initialize memory vector store."""
        self.documents = {}  # namespace -> list of documents
        self.initialized = False
        logger.info("MemoryVectorStore initialized")
    
    async def initialize(self):
        """Initialize memory vector store."""
        try:
            self.initialized = True
            logger.info("MemoryVectorStore initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize MemoryVectorStore: {e}")
            raise
    
    async def search(
        self,
        query: str,
        namespace: str = "",
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar documents in memory.
        
        Args:
            query: Search query text
            namespace: Namespace for filtering
            top_k: Number of results to return
            filters: Additional metadata filters
            
        Returns:
            List of search results with content and metadata
        """
        try:
            # Get documents from namespace
            docs = self.documents.get(namespace, [])
            
            # Simple text matching for development
            results = []
            for doc in docs:
                # Simple relevance scoring based on keyword matching
                score = self._calculate_relevance(query, doc)
                if score > 0:
                    results.append({
                        'content': doc['content'],
                        'metadata': doc['metadata'],
                        'score': score
                    })
            
            # Sort by score and return top_k
            results.sort(key=lambda x: x['score'], reverse=True)
            return results[:top_k]
            
        except Exception as e:
            logger.error(f"Error searching MemoryVectorStore: {e}")
            return []
    
    async def upsert(
        self,
        documents: List[Dict[str, Any]],
        namespace: str = ""
    ) -> bool:
        """
        Upsert documents into memory store.
        
        Args:
            documents: List of documents with content and metadata
            namespace: Namespace for the documents
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if namespace not in self.documents:
                self.documents[namespace] = []
            
            for doc in documents:
                # Remove existing document with same ID if it exists
                doc_id = doc.get('id')
                if doc_id:
                    self.documents[namespace] = [
                        d for d in self.documents[namespace] 
                        if d.get('id') != doc_id
                    ]
                
                # Add new document
                self.documents[namespace].append(doc)
            
            logger.info(f"Upserted {len(documents)} documents to namespace: {namespace}")
            return True
            
        except Exception as e:
            logger.error(f"Error upserting to MemoryVectorStore: {e}")
            return False
    
    async def delete(self, ids: List[str], namespace: str = "") -> bool:
        """Delete documents by IDs."""
        try:
            if namespace in self.documents:
                self.documents[namespace] = [
                    doc for doc in self.documents[namespace]
                    if doc.get('id') not in ids
                ]
            
            logger.info(f"Deleted {len(ids)} documents from namespace: {namespace}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting from MemoryVectorStore: {e}")
            return False
    
    def _calculate_relevance(self, query: str, document: Dict[str, Any]) -> float:
        """
        Calculate relevance score between query and document.
        Simple implementation for development.
        """
        query_lower = query.lower()
        content_lower = document.get('content', '').lower()
        title_lower = document.get('metadata', {}).get('title', '').lower()
        
        # Count keyword matches
        query_words = set(query_lower.split())
        content_words = set(content_lower.split())
        title_words = set(title_lower.split())
        
        # Calculate overlap
        content_overlap = len(query_words.intersection(content_words))
        title_overlap = len(query_words.intersection(title_words))
        
        # Weight title matches higher
        score = (content_overlap + title_overlap * 2) / len(query_words)
        
        return min(score, 1.0)
