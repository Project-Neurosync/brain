"""
Production Vector Database for NeuroSync AI Backend
Handles vector storage, semantic search, and document management using ChromaDB.
"""

from typing import List, Dict, Any, Optional, Union, Tuple
import logging
import os
import uuid
from datetime import datetime, timedelta
import asyncio
from concurrent.futures import ThreadPoolExecutor

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import numpy as np
from pydantic import BaseModel

class VectorSearchResult(BaseModel):
    """Model for vector search results."""
    id: str
    content: str
    metadata: Dict[str, Any]
    score: float
    source: Optional[str] = None
    timestamp: Optional[datetime] = None
    project_id: Optional[str] = None

class DocumentChunk(BaseModel):
    """Model for document chunks to be stored."""
    id: Optional[str] = None
    content: str
    metadata: Dict[str, Any]
    project_id: str
    source_type: str  # 'github', 'jira', 'slack', 'confluence', 'upload'
    source_id: str
    timestamp: datetime
    importance_score: Optional[float] = None

class VectorDatabase:
    """
    Production-ready vector database using ChromaDB for semantic search and document management.
    Supports project isolation, timeline-based storage, and importance scoring.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the Vector Database with ChromaDB."""
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # ChromaDB configuration
        self.persist_directory = self.config.get('persist_directory', './data/chromadb')
        self.collection_name = self.config.get('collection_name', 'neurosync_documents')
        
        # Ensure persist directory exists
        os.makedirs(self.persist_directory, exist_ok=True)
        
        # Initialize ChromaDB client
        self._client = None
        self._collection = None
        
        # Initialize embedding model
        self.embedding_model_name = self.config.get('embedding_model', 'all-MiniLM-L6-v2')
        self._embedding_model = None
        
        # Thread pool for async operations
        self._executor = ThreadPoolExecutor(max_workers=4)
        
        self.logger.info(f"Vector database initialized with persist directory: {self.persist_directory}")
    
    async def _initialize_client(self):
        """Initialize ChromaDB client and collection."""
        if self._client is None:
            def _init_client():
                client = chromadb.PersistentClient(
                    path=self.persist_directory,
                    settings=Settings(
                        anonymized_telemetry=False,
                        allow_reset=True
                    )
                )
                return client
            
            self._client = await asyncio.get_event_loop().run_in_executor(
                self._executor, _init_client
            )
            
        if self._collection is None:
            def _get_collection():
                return self._client.get_or_create_collection(
                    name=self.collection_name,
                    metadata={"description": "NeuroSync document embeddings"}
                )
            
            self._collection = await asyncio.get_event_loop().run_in_executor(
                self._executor, _get_collection
            )
            
        self.logger.info(f"ChromaDB client and collection '{self.collection_name}' initialized")
    
    async def _get_embedding_model(self):
        """Initialize and return the embedding model."""
        if self._embedding_model is None:
            def _load_model():
                return SentenceTransformer(self.embedding_model_name)
            
            self._embedding_model = await asyncio.get_event_loop().run_in_executor(
                self._executor, _load_model
            )
            self.logger.info(f"Embedding model '{self.embedding_model_name}' loaded")
        
        return self._embedding_model
    
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts."""
        model = await self._get_embedding_model()
        
        def _encode_texts():
            embeddings = model.encode(texts, convert_to_tensor=False)
            return embeddings.tolist()
        
        embeddings = await asyncio.get_event_loop().run_in_executor(
            self._executor, _encode_texts
        )
        
        return embeddings
    
    async def add_documents(self, documents: List[DocumentChunk]) -> List[str]:
        """Add document chunks to the vector database."""
        await self._initialize_client()
        
        if not documents:
            return []
        
        # Generate embeddings for document content
        texts = [doc.content for doc in documents]
        embeddings = await self.generate_embeddings(texts)
        
        # Prepare data for ChromaDB
        ids = []
        metadatas = []
        
        for i, doc in enumerate(documents):
            doc_id = doc.id or str(uuid.uuid4())
            ids.append(doc_id)
            
            # Prepare metadata with all document information
            metadata = {
                **doc.metadata,
                'project_id': doc.project_id,
                'source_type': doc.source_type,
                'source_id': doc.source_id,
                'timestamp': doc.timestamp.isoformat(),
                'importance_score': doc.importance_score or 0.5,
                'content_length': len(doc.content),
                'content_preview': doc.content[:200] + '...' if len(doc.content) > 200 else doc.content
            }
            metadatas.append(metadata)
        
        # Add to ChromaDB
        def _add_to_collection():
            self._collection.add(
                ids=ids,
                embeddings=embeddings,
                metadatas=metadatas,
                documents=texts
            )
        
        await asyncio.get_event_loop().run_in_executor(
            self._executor, _add_to_collection
        )
        
        self.logger.info(f"Added {len(documents)} documents to vector database")
        return ids
    
    async def upsert(
        self,
        vectors: List[List[float]],
        ids: Optional[List[str]] = None,
        metadatas: Optional[List[Dict[str, Any]]] = None,
        texts: Optional[List[str]] = None
    ) -> List[str]:
        """
        Upsert vectors into the database.
        
        Args:
            vectors: List of vector embeddings
            ids: Optional list of IDs for the vectors
            metadatas: Optional list of metadata dictionaries
            texts: Optional list of text content
            
        Returns:
            List of document IDs
        """
        await self._initialize_client()
        
        if not ids:
            ids = [str(uuid.uuid4()) for _ in vectors]
            
        if not metadatas:
            metadatas = [{} for _ in vectors]
            
        if not texts:
            texts = [''] * len(vectors)
        
        def _upsert_to_collection():
            self._collection.upsert(
                ids=ids,
                embeddings=vectors,
                metadatas=metadatas,
                documents=texts
            )
        
        await asyncio.get_event_loop().run_in_executor(
            self._executor, _upsert_to_collection
        )
        
        return ids
    
    async def semantic_search(
        self,
        query_text: str,
        n_results: int = 5,
        project_id: Optional[str] = None,
        source_types: Optional[List[str]] = None,
        min_importance_score: Optional[float] = None,
        date_range: Optional[Tuple[datetime, datetime]] = None
    ) -> List[VectorSearchResult]:
        """
        Perform semantic search on documents.
        
        Args:
            query_text: The search query text
            n_results: Number of results to return
            project_id: Filter by project ID
            source_types: Filter by source types (github, jira, slack, etc.)
            min_importance_score: Minimum importance score threshold
            date_range: Tuple of (start_date, end_date) for filtering
            
        Returns:
            List of VectorSearchResult objects
        """
        await self._initialize_client()
        
        # Generate embedding for query
        query_embeddings = await self.generate_embeddings([query_text])
        query_embedding = query_embeddings[0]
        
        # Build ChromaDB where clause for filtering
        where_clause = {}
        if project_id:
            where_clause['project_id'] = project_id
        if source_types:
            where_clause['source_type'] = {'$in': source_types}
        if min_importance_score is not None:
            where_clause['importance_score'] = {'$gte': min_importance_score}
        
        def _query_collection():
            return self._collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where_clause if where_clause else None,
                include=['documents', 'metadatas', 'distances']
            )
        
        results = await asyncio.get_event_loop().run_in_executor(
            self._executor, _query_collection
        )
        
        # Convert to VectorSearchResult objects
        search_results = []
        if results['ids'] and len(results['ids']) > 0:
            for i in range(len(results['ids'][0])):
                doc_id = results['ids'][0][i]
                content = results['documents'][0][i]
                metadata = results['metadatas'][0][i]
                distance = results['distances'][0][i]
                
                # Convert distance to similarity score (1 - distance)
                score = max(0, 1 - distance)
                
                # Parse timestamp if available
                timestamp = None
                if 'timestamp' in metadata:
                    try:
                        timestamp = datetime.fromisoformat(metadata['timestamp'])
                    except:
                        pass
                
                # Apply date range filter if specified
                if date_range and timestamp:
                    if not (date_range[0] <= timestamp <= date_range[1]):
                        continue
                
                search_results.append(VectorSearchResult(
                    id=doc_id,
                    content=content,
                    metadata=metadata,
                    score=score,
                    source=metadata.get('source_type'),
                    timestamp=timestamp,
                    project_id=metadata.get('project_id')
                ))
        
        self.logger.info(f"Semantic search for '{query_text}' returned {len(search_results)} results")
        return search_results
    
    async def query(
        self,
        query_embedding: List[float],
        n_results: int = 5,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[VectorSearchResult]:
        """
        Query the vector database for similar vectors using pre-computed embeddings.
        
        Args:
            query_embedding: The query vector
            n_results: Number of results to return
            filter: Optional filter dictionary
            
        Returns:
            List of VectorSearchResult objects
        """
        await self._initialize_client()
        
        def _query_collection():
            return self._collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=filter,
                include=['documents', 'metadatas', 'distances']
            )
        
        results = await asyncio.get_event_loop().run_in_executor(
            self._executor, _query_collection
        )
        
        # Convert to VectorSearchResult objects
        search_results = []
        if results['ids'] and len(results['ids']) > 0:
            for i in range(len(results['ids'][0])):
                doc_id = results['ids'][0][i]
                content = results['documents'][0][i]
                metadata = results['metadatas'][0][i]
                distance = results['distances'][0][i]
                
                # Convert distance to similarity score
                score = max(0, 1 - distance)
                
                search_results.append(VectorSearchResult(
                    id=doc_id,
                    content=content,
                    metadata=metadata,
                    score=score,
                    source=metadata.get('source_type'),
                    project_id=metadata.get('project_id')
                ))
        
        return search_results
    
    async def delete(self, ids: List[str]) -> None:
        """
        Delete vectors by their IDs.
        
        Args:
            ids: List of vector IDs to delete
        """
        await self._initialize_client()
        
        if not ids:
            return
        
        def _delete_from_collection():
            self._collection.delete(ids=ids)
        
        await asyncio.get_event_loop().run_in_executor(
            self._executor, _delete_from_collection
        )
        
        self.logger.info(f"Deleted {len(ids)} documents from vector database")
    
    async def delete_by_project(self, project_id: str) -> int:
        """
        Delete all documents for a specific project.
        
        Args:
            project_id: Project ID to delete documents for
            
        Returns:
            Number of documents deleted
        """
        await self._initialize_client()
        
        def _delete_by_project():
            # Get all documents for the project
            results = self._collection.get(
                where={'project_id': project_id},
                include=['documents']
            )
            
            if results['ids']:
                self._collection.delete(where={'project_id': project_id})
                return len(results['ids'])
            return 0
        
        deleted_count = await asyncio.get_event_loop().run_in_executor(
            self._executor, _delete_by_project
        )
        
        self.logger.info(f"Deleted {deleted_count} documents for project {project_id}")
        return deleted_count
    
    async def get_project_documents(
        self,
        project_id: str,
        source_type: Optional[str] = None,
        limit: int = 100
    ) -> List[VectorSearchResult]:
        """
        Get all documents for a specific project.
        
        Args:
            project_id: Project ID to get documents for
            source_type: Optional source type filter
            limit: Maximum number of documents to return
            
        Returns:
            List of VectorSearchResult objects
        """
        await self._initialize_client()
        
        where_clause = {'project_id': project_id}
        if source_type:
            where_clause['source_type'] = source_type
        
        def _get_documents():
            return self._collection.get(
                where=where_clause,
                limit=limit,
                include=['documents', 'metadatas']
            )
        
        results = await asyncio.get_event_loop().run_in_executor(
            self._executor, _get_documents
        )
        
        # Convert to VectorSearchResult objects
        documents = []
        if results['ids']:
            for i, doc_id in enumerate(results['ids']):
                content = results['documents'][i] if results['documents'] else ''
                metadata = results['metadatas'][i] if results['metadatas'] else {}
                
                # Parse timestamp if available
                timestamp = None
                if 'timestamp' in metadata:
                    try:
                        timestamp = datetime.fromisoformat(metadata['timestamp'])
                    except:
                        pass
                
                documents.append(VectorSearchResult(
                    id=doc_id,
                    content=content,
                    metadata=metadata,
                    score=1.0,  # No similarity score for direct retrieval
                    source=metadata.get('source_type'),
                    timestamp=timestamp,
                    project_id=metadata.get('project_id')
                ))
        
        return documents
    
    async def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive statistics about the vector database.
        
        Returns:
            Dictionary with collection statistics
        """
        await self._initialize_client()
        
        def _get_stats():
            # Get all documents to analyze
            results = self._collection.get(
                include=['metadatas']
            )
            
            total_count = len(results['ids']) if results['ids'] else 0
            
            if total_count == 0:
                return {
                    'total_documents': 0,
                    'projects': {},
                    'source_types': {},
                    'importance_scores': {'avg': 0, 'min': 0, 'max': 0},
                    'content_lengths': {'avg': 0, 'min': 0, 'max': 0},
                    'date_range': None
                }
            
            # Analyze metadata
            projects = {}
            source_types = {}
            importance_scores = []
            content_lengths = []
            timestamps = []
            
            for metadata in results['metadatas']:
                # Project analysis
                project_id = metadata.get('project_id', 'unknown')
                projects[project_id] = projects.get(project_id, 0) + 1
                
                # Source type analysis
                source_type = metadata.get('source_type', 'unknown')
                source_types[source_type] = source_types.get(source_type, 0) + 1
                
                # Importance score analysis
                importance = metadata.get('importance_score', 0.5)
                importance_scores.append(importance)
                
                # Content length analysis
                content_length = metadata.get('content_length', 0)
                content_lengths.append(content_length)
                
                # Timestamp analysis
                if 'timestamp' in metadata:
                    try:
                        timestamps.append(datetime.fromisoformat(metadata['timestamp']))
                    except:
                        pass
            
            # Calculate statistics
            stats = {
                'total_documents': total_count,
                'projects': projects,
                'source_types': source_types,
                'importance_scores': {
                    'avg': sum(importance_scores) / len(importance_scores) if importance_scores else 0,
                    'min': min(importance_scores) if importance_scores else 0,
                    'max': max(importance_scores) if importance_scores else 0
                },
                'content_lengths': {
                    'avg': sum(content_lengths) / len(content_lengths) if content_lengths else 0,
                    'min': min(content_lengths) if content_lengths else 0,
                    'max': max(content_lengths) if content_lengths else 0
                },
                'date_range': {
                    'earliest': min(timestamps).isoformat() if timestamps else None,
                    'latest': max(timestamps).isoformat() if timestamps else None
                } if timestamps else None
            }
            
            return stats
        
        stats = await asyncio.get_event_loop().run_in_executor(
            self._executor, _get_stats
        )
        
        return stats
    
    async def get_timeline_documents(
        self,
        project_id: str,
        start_date: datetime,
        end_date: datetime,
        source_types: Optional[List[str]] = None
    ) -> List[VectorSearchResult]:
        """
        Get documents within a specific timeline for a project.
        
        Args:
            project_id: Project ID to filter by
            start_date: Start date for timeline
            end_date: End date for timeline
            source_types: Optional list of source types to filter
            
        Returns:
            List of VectorSearchResult objects sorted by timestamp
        """
        # Get all project documents
        all_docs = await self.get_project_documents(project_id, limit=1000)
        
        # Filter by date range and source types
        timeline_docs = []
        for doc in all_docs:
            if doc.timestamp and start_date <= doc.timestamp <= end_date:
                if not source_types or doc.source in source_types:
                    timeline_docs.append(doc)
        
        # Sort by timestamp
        timeline_docs.sort(key=lambda x: x.timestamp or datetime.min)
        
        return timeline_docs
    
    async def cleanup_old_documents(
        self,
        project_id: str,
        days_old: int = 90,
        min_importance_score: float = 0.3
    ) -> int:
        """
        Clean up old documents with low importance scores.
        
        Args:
            project_id: Project ID to clean up
            days_old: Delete documents older than this many days
            min_importance_score: Only delete documents below this importance score
            
        Returns:
            Number of documents deleted
        """
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        # Get project documents
        all_docs = await self.get_project_documents(project_id, limit=10000)
        
        # Find documents to delete
        docs_to_delete = []
        for doc in all_docs:
            if (doc.timestamp and doc.timestamp < cutoff_date and 
                doc.metadata.get('importance_score', 0.5) < min_importance_score):
                docs_to_delete.append(doc.id)
        
        if docs_to_delete:
            await self.delete(docs_to_delete)
        
        self.logger.info(f"Cleaned up {len(docs_to_delete)} old documents for project {project_id}")
        return len(docs_to_delete)
