"""
Vector Database Operations for NeuroSync API
Implements semantic search and document storage using ChromaDB
"""

import logging
from typing import Dict, List, Any, Optional, Union
from uuid import UUID
import os
import json
import chromadb
from chromadb.utils import embedding_functions
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor

# Create logger
logger = logging.getLogger(__name__)

class VectorDatabaseService:
    """
    Vector Database service using ChromaDB for semantic search and document storage
    """
    
    def __init__(self, persist_directory: str = "./vector_db"):
        """
        Initialize Vector Database service
        
        Args:
            persist_directory: Directory for persistent storage
        """
        self.persist_directory = persist_directory
        
        # Ensure directory exists
        os.makedirs(persist_directory, exist_ok=True)
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(path=persist_directory)
        
        # Initialize sentence transformer embedding function
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        
        # Initialize thread pool for parallel processing
        self.executor = ThreadPoolExecutor(max_workers=5)
        
        logger.info(f"Vector Database service initialized with persistence at {persist_directory}")
    
    def _get_collection(self, project_id: UUID):
        """Get or create collection for project"""
        collection_name = f"project_{str(project_id).replace('-', '')}"
        return self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embedding_function,
            metadata={"project_id": str(project_id)}
        )
    
    async def add_documents(
        self, 
        project_id: UUID, 
        documents: List[Dict[str, Any]], 
        batch_size: int = 20
    ) -> Dict[str, Any]:
        """
        Add documents to vector database
        
        Args:
            project_id: Project ID to associate documents with
            documents: List of documents to add
                Each document must have:
                - 'id': Unique identifier
                - 'content': Text content for embedding
                - 'metadata': Dict with source, type, etc.
            batch_size: Maximum batch size for processing
            
        Returns:
            Dict with results
        """
        try:
            logger.info(f"Adding {len(documents)} documents to vector database for project {project_id}")
            
            collection = self._get_collection(project_id)
            
            # Prepare document batches for processing
            batches = [documents[i:i + batch_size] for i in range(0, len(documents), batch_size)]
            successful_adds = 0
            errors = []
            
            for batch in batches:
                try:
                    # Extract data from documents
                    ids = [str(doc.get("id")) for doc in batch]
                    contents = [doc.get("content") for doc in batch]
                    metadatas = [self._prepare_metadata(doc.get("metadata", {})) for doc in batch]
                    
                    # Add to collection
                    collection.add(
                        ids=ids,
                        documents=contents,
                        metadatas=metadatas
                    )
                    
                    successful_adds += len(batch)
                    logger.debug(f"Successfully added batch of {len(batch)} documents")
                    
                except Exception as e:
                    logger.error(f"Error adding document batch: {str(e)}")
                    errors.append(str(e))
            
            return {
                "success": True if successful_adds > 0 else False,
                "items_added": successful_adds,
                "total_items": len(documents),
                "errors": errors
            }
            
        except Exception as e:
            logger.error(f"Error adding documents: {str(e)}")
            return {
                "success": False,
                "items_added": 0,
                "total_items": len(documents),
                "errors": [str(e)]
            }
    
    def _prepare_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare metadata for ChromaDB
        - Convert non-primitive types to strings
        - Ensure proper format for filtering
        """
        result = {}
        
        # Process each field in metadata
        for key, value in metadata.items():
            # Skip null values
            if value is None:
                continue
                
            # Convert datetime to ISO format string
            if isinstance(value, datetime):
                result[key] = value.isoformat()
            # Convert UUID to string
            elif isinstance(value, UUID):
                result[key] = str(value)
            # Convert lists/dicts to JSON strings
            elif isinstance(value, (dict, list)):
                result[key] = json.dumps(value)
            # Keep primitive types as is
            else:
                result[key] = value
                
        # Add timestamp if not present
        if "timestamp" not in result:
            result["timestamp"] = datetime.utcnow().isoformat()
            
        return result
    
    async def semantic_search(
        self, 
        project_id: UUID, 
        query: str, 
        limit: int = 10, 
        filters: Optional[Dict[str, Any]] = None,
        min_importance_score: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Search for documents semantically
        
        Args:
            project_id: Project ID to search in
            query: Search query
            limit: Maximum number of results
            filters: Optional metadata filters
            min_importance_score: Minimum importance score (0.0-1.0)
            
        Returns:
            List of matching documents with scores
        """
        try:
            collection = self._get_collection(project_id)
            
            # Prepare filters
            where_clause = {}
            if filters:
                for key, value in filters.items():
                    where_clause[key] = value
            
            # Add importance score filter if specified
            if min_importance_score > 0:
                where_clause["importance_score"] = {"$gte": min_importance_score}
            
            # Execute search
            results = collection.query(
                query_texts=[query],
                n_results=limit,
                where=where_clause if where_clause else None
            )
            
            # Format results
            documents = []
            if results and results.get("documents"):
                for i, doc in enumerate(results["documents"][0]):
                    if i < len(results["metadatas"][0]) and i < len(results["distances"][0]):
                        # Convert score from distance to similarity (0-1)
                        score = 1.0 - min(1.0, max(0.0, results["distances"][0][i]))
                        
                        documents.append({
                            "id": results["ids"][0][i],
                            "content": doc,
                            "metadata": results["metadatas"][0][i],
                            "score": score
                        })
            
            return documents
            
        except Exception as e:
            logger.error(f"Error searching documents: {str(e)}")
            return []
    
    async def get_project_documents(
        self, 
        project_id: UUID,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all documents for a project
        
        Args:
            project_id: Project ID
            limit: Maximum number of documents to return
            filters: Optional metadata filters
            
        Returns:
            List of documents
        """
        try:
            collection = self._get_collection(project_id)
            
            # Execute query
            results = collection.query(
                query_texts=None,  # No query means get all
                n_results=limit,
                where=filters
            )
            
            # Format results
            documents = []
            if results and results.get("documents"):
                for i, doc in enumerate(results["documents"][0]):
                    if i < len(results["metadatas"][0]):
                        documents.append({
                            "id": results["ids"][0][i],
                            "content": doc,
                            "metadata": results["metadatas"][0][i]
                        })
            
            return documents
            
        except Exception as e:
            logger.error(f"Error getting project documents: {str(e)}")
            return []
    
    async def get_timeline_documents(
        self, 
        project_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        source_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get documents within a time range
        
        Args:
            project_id: Project ID
            start_date: Start date for filter
            end_date: End date for filter
            source_type: Optional source type filter (github, jira, slack, etc.)
            limit: Maximum number of documents to return
            
        Returns:
            List of documents
        """
        try:
            filters = {}
            
            # Add date filters if specified
            if start_date or end_date:
                start_str = start_date.isoformat() if start_date else None
                end_str = end_date.isoformat() if end_date else None
                
                if start_str and end_str:
                    filters["timestamp"] = {"$gte": start_str, "$lte": end_str}
                elif start_str:
                    filters["timestamp"] = {"$gte": start_str}
                elif end_str:
                    filters["timestamp"] = {"$lte": end_str}
            
            # Add source type filter if specified
            if source_type:
                filters["source_type"] = source_type
                
            return await self.get_project_documents(project_id, limit, filters)
            
        except Exception as e:
            logger.error(f"Error getting timeline documents: {str(e)}")
            return []
    
    async def cleanup_old_documents(
        self, 
        project_id: UUID,
        older_than_days: int = 365,
        min_importance_score: float = 0.7
    ) -> Dict[str, Any]:
        """
        Delete old documents with low importance
        
        Args:
            project_id: Project ID
            older_than_days: Age threshold in days
            min_importance_score: Importance threshold
            
        Returns:
            Dict with results
        """
        try:
            collection = self._get_collection(project_id)
            cutoff_date = (datetime.utcnow() - timedelta(days=older_than_days)).isoformat()
            
            # Query for old documents with low importance
            results = collection.query(
                query_texts=None,
                where={
                    "timestamp": {"$lt": cutoff_date},
                    "importance_score": {"$lt": min_importance_score}
                },
                n_results=1000
            )
            
            # Delete if any found
            deleted_count = 0
            if results and results.get("ids") and results["ids"][0]:
                collection.delete(ids=results["ids"][0])
                deleted_count = len(results["ids"][0])
                
            return {
                "success": True,
                "deleted_count": deleted_count
            }
            
        except Exception as e:
            logger.error(f"Error cleaning up documents: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "deleted_count": 0
            }
    
    async def get_collection_stats(self, project_id: UUID) -> Dict[str, Any]:
        """
        Get statistics for a project collection
        
        Args:
            project_id: Project ID
            
        Returns:
            Dict with collection statistics
        """
        try:
            collection = self._get_collection(project_id)
            
            # Get count
            count = collection.count()
            
            # Get source type distribution
            source_types = collection.query(
                query_texts=None,
                where={},
                include=["metadatas"]
            )
            
            sources = {}
            if source_types and source_types.get("metadatas"):
                for metadata in source_types["metadatas"][0]:
                    source = metadata.get("source_type")
                    if source:
                        sources[source] = sources.get(source, 0) + 1
            
            return {
                "document_count": count,
                "source_distribution": sources,
                "collection_name": collection.name
            }
            
        except Exception as e:
            logger.error(f"Error getting collection stats: {str(e)}")
            return {
                "error": str(e),
                "document_count": 0
            }
