"""
Vector Database for NeuroSync AI Backend
Handles vector storage and similarity search operations.
"""

from typing import List, Dict, Any, Optional, Union
import logging
import numpy as np
from pydantic import BaseModel

class VectorSearchResult(BaseModel):
    """Model for vector search results."""
    id: str
    content: str
    metadata: Dict[str, Any]
    score: float

class VectorDatabase:
    """
    Handles vector storage and similarity search operations.
    This is a simplified in-memory implementation. In production,
    this would connect to a dedicated vector database like ChromaDB, Pinecone, or Weaviate.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the Vector Database."""
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        self.vectors = {}
        self.embeddings = {}
        self.metadata = {}
    
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
        if not ids:
            import uuid
            ids = [str(uuid.uuid4()) for _ in vectors]
            
        if not metadatas:
            metadatas = [{} for _ in vectors]
            
        if texts:
            for i, text in enumerate(texts):
                metadatas[i]["text"] = text
        
        for i, vector_id in enumerate(ids):
            self.vectors[vector_id] = np.array(vectors[i])
            self.metadata[vector_id] = metadatas[i]
            
        return ids
    
    async def query(
        self,
        query_embedding: List[float],
        n_results: int = 5,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[VectorSearchResult]:
        """
        Query the vector database for similar vectors.
        
        Args:
            query_embedding: The query vector
            n_results: Number of results to return
            filter: Optional filter dictionary
            
        Returns:
            List of VectorSearchResult objects
        """
        query_vec = np.array(query_embedding)
        results = []
        
        for vec_id, vec in self.vectors.items():
            # Simple cosine similarity
            similarity = np.dot(query_vec, vec) / (np.linalg.norm(query_vec) * np.linalg.norm(vec) + 1e-9)
            
            # Apply filters if provided
            if filter:
                metadata = self.metadata[vec_id]
                match = True
                for key, value in filter.items():
                    if metadata.get(key) != value:
                        match = False
                        break
                if not match:
                    continue
            
            results.append(VectorSearchResult(
                id=vec_id,
                content=self.metadata[vec_id].get("text", ""),
                metadata=self.metadata[vec_id],
                score=float(similarity)
            ))
        
        # Sort by score in descending order and return top n_results
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:n_results]
    
    async def delete(self, ids: List[str]) -> None:
        """
        Delete vectors by their IDs.
        
        Args:
            ids: List of vector IDs to delete
        """
        for vec_id in ids:
            if vec_id in self.vectors:
                del self.vectors[vec_id]
            if vec_id in self.metadata:
                del self.metadata[vec_id]
    
    async def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the vector database.
        
        Returns:
            Dictionary with collection statistics
        """
        return {
            "vector_count": len(self.vectors),
            "dimensions": len(next(iter(self.vectors.values()))) if self.vectors else 0,
            "metadata_fields": list(set(field for meta in self.metadata.values() for field in meta.keys()))
        }
