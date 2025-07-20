"""
NeuroSync AI Backend - Vector Store Service
Handles embeddings, vector storage, and semantic search using ChromaDB
"""

import logging
import uuid
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import numpy as np

from ..config.settings import get_settings

logger = logging.getLogger(__name__)

class VectorService:
    """Service for managing vector embeddings and semantic search"""
    
    def __init__(self):
        self.settings = get_settings()
        
        # Initialize ChromaDB client
        self.chroma_client = chromadb.PersistentClient(
            path=self.settings.vector_db_path,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Initialize embedding model
        self.embedding_model = SentenceTransformer(self.settings.embedding_model)
        
        # Cache for collections
        self._collections = {}
        
    def get_or_create_collection(self, project_id: str) -> chromadb.Collection:
        """Get or create a collection for a specific project"""
        collection_name = f"project_{project_id}"
        
        if collection_name not in self._collections:
            try:
                # Try to get existing collection
                collection = self.chroma_client.get_collection(name=collection_name)
                logger.info(f"Retrieved existing collection: {collection_name}")
            except Exception:
                # Create new collection if it doesn't exist
                collection = self.chroma_client.create_collection(
                    name=collection_name,
                    metadata={"project_id": project_id, "created_at": datetime.utcnow().isoformat()}
                )
                logger.info(f"Created new collection: {collection_name}")
            
            self._collections[collection_name] = collection
        
        return self._collections[collection_name]
    
    async def add_documents(
        self, 
        project_id: str, 
        documents: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Add documents to the vector store"""
        collection = self.get_or_create_collection(project_id)
        
        processed_docs = []
        embeddings = []
        ids = []
        metadatas = []
        
        for doc in documents:
            try:
                # Generate unique ID
                doc_id = doc.get('id', str(uuid.uuid4()))
                
                # Prepare document content for embedding
                content = self._prepare_content_for_embedding(doc)
                
                # Generate embedding
                embedding = self.embedding_model.encode(content).tolist()
                
                # Prepare metadata
                metadata = {
                    "source_type": doc.get('source_type', 'unknown'),
                    "created_at": doc.get('created_at', datetime.utcnow().isoformat()),
                    "file_path": doc.get('file_path', ''),
                    "title": doc.get('title', ''),
                    "content_length": len(content),
                    **doc.get('metadata', {})
                }
                
                processed_docs.append(content)
                embeddings.append(embedding)
                ids.append(doc_id)
                metadatas.append(metadata)
                
                logger.debug(f"Processed document {doc_id} for embedding")
                
            except Exception as e:
                logger.error(f"Error processing document for embedding: {str(e)}")
                continue
        
        if processed_docs:
            try:
                # Add to ChromaDB
                collection.add(
                    documents=processed_docs,
                    embeddings=embeddings,
                    ids=ids,
                    metadatas=metadatas
                )
                
                logger.info(f"Added {len(processed_docs)} documents to collection {project_id}")
                
                return {
                    "success": True,
                    "documents_added": len(processed_docs),
                    "collection_name": f"project_{project_id}"
                }
                
            except Exception as e:
                logger.error(f"Error adding documents to ChromaDB: {str(e)}")
                return {
                    "success": False,
                    "error": str(e),
                    "documents_added": 0
                }
        
        return {
            "success": False,
            "error": "No valid documents to add",
            "documents_added": 0
        }
    
    async def search_documents(
        self, 
        project_id: str, 
        query: str, 
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search for relevant documents using semantic similarity"""
        collection = self.get_or_create_collection(project_id)
        
        try:
            # Generate query embedding
            query_embedding = self.embedding_model.encode(query).tolist()
            
            # Prepare where clause for filtering
            where_clause = {}
            if filters:
                where_clause = self._build_where_clause(filters)
            
            # Search in ChromaDB
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=limit,
                where=where_clause if where_clause else None,
                include=["documents", "metadatas", "distances"]
            )
            
            # Process results
            documents = []
            if results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    document = {
                        "id": results['ids'][0][i],
                        "content": doc,
                        "metadata": results['metadatas'][0][i],
                        "relevance_score": 1 - results['distances'][0][i],  # Convert distance to similarity
                        "source_type": results['metadatas'][0][i].get('source_type', 'unknown'),
                        "file_path": results['metadatas'][0][i].get('file_path', ''),
                        "title": results['metadatas'][0][i].get('title', '')
                    }
                    documents.append(document)
            
            logger.info(f"Found {len(documents)} relevant documents for query in project {project_id}")
            return documents
            
        except Exception as e:
            logger.error(f"Error searching documents: {str(e)}")
            return []
    
    async def update_document(
        self, 
        project_id: str, 
        document_id: str, 
        updated_content: str,
        updated_metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Update an existing document in the vector store"""
        collection = self.get_or_create_collection(project_id)
        
        try:
            # Generate new embedding
            embedding = self.embedding_model.encode(updated_content).tolist()
            
            # Prepare metadata
            metadata = updated_metadata or {}
            metadata["updated_at"] = datetime.utcnow().isoformat()
            metadata["content_length"] = len(updated_content)
            
            # Update in ChromaDB
            collection.update(
                ids=[document_id],
                documents=[updated_content],
                embeddings=[embedding],
                metadatas=[metadata]
            )
            
            logger.info(f"Updated document {document_id} in project {project_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating document: {str(e)}")
            return False
    
    async def delete_document(self, project_id: str, document_id: str) -> bool:
        """Delete a document from the vector store"""
        collection = self.get_or_create_collection(project_id)
        
        try:
            collection.delete(ids=[document_id])
            logger.info(f"Deleted document {document_id} from project {project_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting document: {str(e)}")
            return False
    
    async def get_collection_stats(self, project_id: str) -> Dict[str, Any]:
        """Get statistics about a project's vector collection"""
        collection = self.get_or_create_collection(project_id)
        
        try:
            count = collection.count()
            
            # Get sample of metadata to analyze source types
            sample_results = collection.get(limit=min(100, count), include=["metadatas"])
            
            source_types = {}
            if sample_results['metadatas']:
                for metadata in sample_results['metadatas']:
                    source_type = metadata.get('source_type', 'unknown')
                    source_types[source_type] = source_types.get(source_type, 0) + 1
            
            return {
                "total_documents": count,
                "source_types": source_types,
                "collection_name": f"project_{project_id}",
                "embedding_model": self.settings.embedding_model
            }
            
        except Exception as e:
            logger.error(f"Error getting collection stats: {str(e)}")
            return {
                "total_documents": 0,
                "source_types": {},
                "collection_name": f"project_{project_id}",
                "error": str(e)
            }
    
    def _prepare_content_for_embedding(self, doc: Dict[str, Any]) -> str:
        """Prepare document content for embedding generation"""
        content_parts = []
        
        # Add title if available
        if doc.get('title'):
            content_parts.append(f"Title: {doc['title']}")
        
        # Add main content
        if doc.get('content'):
            content_parts.append(doc['content'])
        
        # Add file path context
        if doc.get('file_path'):
            content_parts.append(f"File: {doc['file_path']}")
        
        # Add any additional text fields
        for field in ['description', 'summary', 'tags']:
            if doc.get(field):
                if isinstance(doc[field], list):
                    content_parts.append(f"{field.title()}: {', '.join(doc[field])}")
                else:
                    content_parts.append(f"{field.title()}: {doc[field]}")
        
        content = "\n".join(content_parts)
        
        # Truncate if too long (most embedding models have token limits)
        max_length = 8000  # Conservative limit for most models
        if len(content) > max_length:
            content = content[:max_length] + "..."
        
        return content
    
    def _build_where_clause(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Build ChromaDB where clause from filters"""
        where_clause = {}
        
        # Handle source type filtering
        if 'source_type' in filters:
            source_types = filters['source_type']
            if isinstance(source_types, str):
                where_clause['source_type'] = source_types
            elif isinstance(source_types, list):
                where_clause['source_type'] = {"$in": source_types}
        
        # Handle date range filtering
        if 'date_range' in filters:
            date_range = filters['date_range']
            if 'start' in date_range:
                where_clause['created_at'] = {"$gte": date_range['start']}
            if 'end' in date_range:
                if 'created_at' in where_clause:
                    where_clause['created_at']['$lte'] = date_range['end']
                else:
                    where_clause['created_at'] = {"$lte": date_range['end']}
        
        # Handle file path filtering
        if 'file_path' in filters:
            file_path = filters['file_path']
            if isinstance(file_path, str):
                where_clause['file_path'] = {"$contains": file_path}
            elif isinstance(file_path, list):
                where_clause['file_path'] = {"$in": file_path}
        
        return where_clause
    
    async def similarity_search_with_score_threshold(
        self, 
        project_id: str, 
        query: str, 
        score_threshold: float = 0.7,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search for documents with a minimum similarity score"""
        all_results = await self.search_documents(project_id, query, limit * 2)  # Get more to filter
        
        # Filter by score threshold
        filtered_results = [
            doc for doc in all_results 
            if doc['relevance_score'] >= score_threshold
        ]
        
        return filtered_results[:limit]
    
    async def get_similar_documents(
        self, 
        project_id: str, 
        document_id: str, 
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Find documents similar to a given document"""
        collection = self.get_or_create_collection(project_id)
        
        try:
            # Get the document
            result = collection.get(ids=[document_id], include=["documents", "embeddings"])
            
            if not result['documents'] or not result['documents'][0]:
                return []
            
            # Use the document's embedding to find similar ones
            embedding = result['embeddings'][0]
            
            similar_results = collection.query(
                query_embeddings=[embedding],
                n_results=limit + 1,  # +1 because the original document will be included
                include=["documents", "metadatas", "distances"]
            )
            
            # Process and filter out the original document
            documents = []
            if similar_results['documents'] and similar_results['documents'][0]:
                for i, doc in enumerate(similar_results['documents'][0]):
                    doc_id = similar_results['ids'][0][i]
                    if doc_id != document_id:  # Exclude the original document
                        document = {
                            "id": doc_id,
                            "content": doc,
                            "metadata": similar_results['metadatas'][0][i],
                            "relevance_score": 1 - similar_results['distances'][0][i],
                            "source_type": similar_results['metadatas'][0][i].get('source_type', 'unknown'),
                            "file_path": similar_results['metadatas'][0][i].get('file_path', ''),
                            "title": similar_results['metadatas'][0][i].get('title', '')
                        }
                        documents.append(document)
            
            return documents[:limit]
            
        except Exception as e:
            logger.error(f"Error finding similar documents: {str(e)}")
            return []
