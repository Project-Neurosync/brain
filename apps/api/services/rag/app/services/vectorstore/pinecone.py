"""
Pinecone vector store implementation.
"""

import json
import uuid
from typing import Dict, List, Any, Optional, Union, Tuple
import asyncio

from pinecone import Pinecone, PodSpec
from pinecone.data.index import Index as PineconeIndex

from app.core.config import settings
from app.services.vectorstore.base import BaseVectorStore, Document, SearchResult


class PineconeVectorStore(BaseVectorStore):
    """Pinecone vector store implementation."""
    
    def __init__(self, index_name: str = None):
        """Initialize Pinecone client and get index."""
        if not settings.vectorstore.pinecone_api_key:
            raise ValueError("PINECONE_API_KEY environment variable is required for Pinecone")
        
        if not index_name:
            index_name = settings.vectorstore.pinecone_index_name
            if not index_name:
                raise ValueError("Pinecone index name is required")
        
        self.index_name = index_name
        self.embedding_dim = settings.vectorstore.embedding_dimension
        
        # Initialize Pinecone client
        self.pc = Pinecone(api_key=settings.vectorstore.pinecone_api_key)
        
        # Check if index exists, if not create it
        self._ensure_index_exists()
        
        # Get index
        self.index = self.pc.Index(self.index_name)
    
    def _ensure_index_exists(self):
        """Ensure the index exists, create if it doesn't."""
        # List existing indexes
        existing_indexes = [idx["name"] for idx in self.pc.list_indexes()]
        
        # Create index if it doesn't exist
        if self.index_name not in existing_indexes:
            self.pc.create_index(
                name=self.index_name,
                dimension=self.embedding_dim,
                metric="cosine",
                spec=PodSpec(
                    environment=settings.vectorstore.pinecone_environment,
                    pod_type=settings.vectorstore.pinecone_pod_type,
                    pods=1
                )
            )
            print(f"Created new Pinecone index: {self.index_name}")
    
    async def add_documents(
        self, 
        documents: List[Document],
        namespace: Optional[str] = None
    ) -> List[str]:
        """Add documents to Pinecone index."""
        vectors = []
        doc_ids = []
        
        for doc in documents:
            # Ensure document has an ID
            if not doc.id:
                doc.id = str(uuid.uuid4())
            
            # Ensure document has an embedding
            if not doc.embedding:
                raise ValueError(f"Document {doc.id} has no embedding")
            
            # Create Pinecone vector
            vector = {
                "id": doc.id,
                "values": doc.embedding,
                "metadata": {
                    "content": doc.content,
                    **doc.metadata
                }
            }
            
            vectors.append(vector)
            doc_ids.append(doc.id)
        
        # Upload vectors in batches
        batch_size = 100
        for i in range(0, len(vectors), batch_size):
            batch = vectors[i:i+batch_size]
            await asyncio.to_thread(
                self.index.upsert,
                vectors=batch,
                namespace=namespace or ""
            )
        
        return doc_ids
    
    async def get_document(
        self,
        document_id: str,
        namespace: Optional[str] = None
    ) -> Optional[Document]:
        """Get a document by ID."""
        try:
            response = await asyncio.to_thread(
                self.index.fetch,
                ids=[document_id],
                namespace=namespace or ""
            )
            
            if not response or document_id not in response.vectors:
                return None
                
            vector_data = response.vectors[document_id]
            
            # Extract content from metadata
            content = vector_data.metadata.pop("content", "")
            
            return Document(
                id=document_id,
                content=content,
                metadata=vector_data.metadata,
                embedding=vector_data.values
            )
            
        except Exception as e:
            print(f"Error fetching document {document_id}: {e}")
            return None
    
    async def search(
        self,
        query: str,
        k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None,
        namespace: Optional[str] = None
    ) -> List[SearchResult]:
        """
        Search for documents similar to the query.
        
        Note: This method requires an embedding model to convert the query to a vector.
        The embedding model should be injected or this method should be implemented
        in a subclass that has access to the embedding model.
        """
        raise NotImplementedError(
            "The search method requires an embedding model to convert the query to a vector. "
            "Use search_by_vector instead or implement this method in a subclass "
            "that has access to the embedding model."
        )
    
    async def search_by_vector(
        self,
        embedding: List[float],
        k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None,
        namespace: Optional[str] = None
    ) -> List[SearchResult]:
        """Search for documents using a vector embedding."""
        try:
            query_response = await asyncio.to_thread(
                self.index.query,
                vector=embedding,
                top_k=k,
                namespace=namespace or "",
                filter=filter_metadata,
                include_metadata=True,
                include_values=True
            )
            
            results = []
            for match in query_response.matches:
                # Extract content from metadata
                content = match.metadata.pop("content", "")
                
                document = Document(
                    id=match.id,
                    content=content,
                    metadata=match.metadata,
                    embedding=match.values if hasattr(match, "values") else None
                )
                
                results.append(
                    SearchResult(
                        document=document,
                        score=float(match.score)
                    )
                )
            
            return results
            
        except Exception as e:
            print(f"Error searching by vector: {e}")
            return []
    
    async def delete(
        self,
        document_ids: List[str],
        namespace: Optional[str] = None
    ) -> bool:
        """Delete documents by ID."""
        try:
            await asyncio.to_thread(
                self.index.delete,
                ids=document_ids,
                namespace=namespace or ""
            )
            return True
        except Exception as e:
            print(f"Error deleting documents: {e}")
            return False
    
    async def delete_namespace(
        self,
        namespace: str
    ) -> bool:
        """Delete an entire namespace/collection."""
        try:
            # Pinecone doesn't have a direct namespace delete, 
            # so we have to delete all vectors in the namespace
            await asyncio.to_thread(
                self.index.delete,
                delete_all=True,
                namespace=namespace
            )
            return True
        except Exception as e:
            print(f"Error deleting namespace {namespace}: {e}")
            return False
    
    async def get_namespaces(self) -> List[str]:
        """Get all available namespaces/collections."""
        try:
            # Pinecone doesn't have a direct API to list namespaces in v2
            # This is a workaround using describe_index_stats
            stats = await asyncio.to_thread(self.index.describe_index_stats)
            
            # Extract namespaces from stats
            namespaces = list(stats.namespaces.keys()) if hasattr(stats, "namespaces") else []
            return namespaces
        except Exception as e:
            print(f"Error getting namespaces: {e}")
            return []
