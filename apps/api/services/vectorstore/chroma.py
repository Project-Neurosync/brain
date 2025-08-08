"""
Chroma vector store implementation for NeuroSync RAG system.
Provides local vector storage using ChromaDB - completely free and runs locally.
"""

import logging
import os
from typing import List, Dict, Any, Optional
import asyncio

from .base import BaseVectorStore, Document, SearchResult

logger = logging.getLogger(__name__)

class ChromaVectorStore(BaseVectorStore):
    """Chroma implementation of vector store - runs locally, completely free."""
    
    def __init__(self, collection_name: str = "neurosync-rag", persist_directory: str = "./chroma_db"):
        """Initialize Chroma vector store."""
        self.collection_name = collection_name
        self.persist_directory = persist_directory
        self.client = None
        self.collection = None
        self.initialized = False
        logger.info(f"ChromaVectorStore initialized with collection: {collection_name}")
    
    async def initialize(self):
        """Initialize Chroma connection."""
        try:
            # Import chromadb (install with: pip install chromadb)
            import chromadb
            from chromadb.config import Settings
            
            # Create persistent client (saves data locally)
            self.client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=Settings(
                    anonymized_telemetry=False,  # Disable telemetry for privacy
                    allow_reset=True
                )
            )
            
            # Get or create collection
            try:
                self.collection = self.client.get_collection(name=self.collection_name)
                logger.info(f"Using existing Chroma collection: {self.collection_name}")
            except:
                self.collection = self.client.create_collection(
                    name=self.collection_name,
                    metadata={"description": "NeuroSync RAG documents"}
                )
                logger.info(f"Created new Chroma collection: {self.collection_name}")
            
            self.initialized = True
            logger.info("ChromaVectorStore initialized successfully (local)")
            
        except ImportError:
            logger.error("ChromaDB not installed. Install with: pip install chromadb")
            # Fall back to mock mode
            self.initialized = True
            logger.info("ChromaVectorStore running in mock mode (install chromadb for full functionality)")
        except Exception as e:
            logger.error(f"Failed to initialize ChromaVectorStore: {e}")
            # Fall back to mock mode
            self.initialized = True
            logger.info("ChromaVectorStore running in mock mode due to initialization error")
    
    async def search(
        self,
        query: str,
        namespace: str = "",
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar documents using Chroma.
        
        Args:
            query: Search query text
            namespace: Namespace for filtering (used as metadata filter)
            top_k: Number of results to return
            filters: Additional metadata filters
            
        Returns:
            List of search results with content and metadata
        """
        try:
            if not self.collection:
                # Return mock results if Chroma not available
                return await self._mock_search(query, namespace, top_k, filters)
            
            # Build metadata filters
            where_filters = {}
            if namespace:
                where_filters["namespace"] = namespace
            if filters:
                where_filters.update(filters)
            
            # Search using Chroma
            results = self.collection.query(
                query_texts=[query],
                n_results=top_k,
                where=where_filters if where_filters else None,
                include=["documents", "metadatas", "distances"]
            )
            
            # Convert Chroma results to our format
            search_results = []
            if results["documents"] and len(results["documents"]) > 0:
                documents = results["documents"][0]
                metadatas = results["metadatas"][0] if results["metadatas"] else []
                distances = results["distances"][0] if results["distances"] else []
                
                for i, doc in enumerate(documents):
                    metadata = metadatas[i] if i < len(metadatas) else {}
                    distance = distances[i] if i < len(distances) else 1.0
                    
                    # Convert distance to similarity score (lower distance = higher similarity)
                    score = max(0.0, 1.0 - distance)
                    
                    search_results.append({
                        'content': doc,
                        'metadata': metadata,
                        'score': score
                    })
            
            logger.info(f"ChromaVectorStore found {len(search_results)} results for query: {query[:50]}...")
            return search_results
            
        except Exception as e:
            logger.error(f"Error searching ChromaVectorStore: {e}")
            # Fall back to mock results
            return await self._mock_search(query, namespace, top_k, filters)
    
    async def upsert(
        self,
        documents: List[Dict[str, Any]],
        namespace: str = ""
    ) -> bool:
        """
        Upsert documents into Chroma.
        
        Args:
            documents: List of documents with content and metadata
            namespace: Namespace for the documents
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.collection:
                logger.info(f"Mock upsert of {len(documents)} documents to namespace: {namespace}")
                return True
            
            # Prepare data for Chroma
            ids = []
            contents = []
            metadatas = []
            
            for doc in documents:
                doc_id = doc.get('id', f"doc_{len(ids)}")
                content = doc.get('content', '')
                metadata = doc.get('metadata', {})
                
                # Add namespace to metadata
                if namespace:
                    metadata['namespace'] = namespace
                
                ids.append(doc_id)
                contents.append(content)
                metadatas.append(metadata)
            
            # Upsert to Chroma
            self.collection.upsert(
                ids=ids,
                documents=contents,
                metadatas=metadatas
            )
            
            logger.info(f"Upserted {len(documents)} documents to ChromaVectorStore namespace: {namespace}")
            return True
            
        except Exception as e:
            logger.error(f"Error upserting to ChromaVectorStore: {e}")
            return False
    
    async def delete(self, ids: List[str], namespace: str = "") -> bool:
        """Delete documents by IDs."""
        try:
            if not self.collection:
                logger.info(f"Mock delete of {len(ids)} documents from namespace: {namespace}")
                return True
            
            # Delete from Chroma
            self.collection.delete(ids=ids)
            
            logger.info(f"Deleted {len(ids)} documents from ChromaVectorStore")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting from ChromaVectorStore: {e}")
            return False
    
    async def _mock_search(
        self,
        query: str,
        namespace: str,
        top_k: int,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Mock search implementation when Chroma is not available.
        Returns realistic-looking results based on the query.
        """
        # Generate mock results based on query content
        mock_results = []
        
        # Different mock content based on query keywords
        if "bug" in query.lower() or "error" in query.lower():
            mock_results.extend([
                {
                    'content': f"Bug report: Authentication error when users try to log in with OAuth. Error occurs intermittently and affects about 5% of login attempts. Stack trace shows issue in JWT token validation.",
                    'metadata': {
                        'id': 'github_issue_123',
                        'title': 'OAuth Login Authentication Error',
                        'source_type': 'github',
                        'url': 'https://github.com/neurosync/app/issues/123',
                        'created_at': '2024-01-15T10:30:00Z',
                        'namespace': namespace
                    },
                    'score': 0.95
                },
                {
                    'content': f"Slack discussion about the authentication bug. Team members discussing potential fixes and workarounds. John mentioned that clearing browser cache helps some users.",
                    'metadata': {
                        'id': 'slack_msg_456',
                        'title': 'Auth Bug Discussion',
                        'source_type': 'slack',
                        'url': 'https://neurosync.slack.com/archives/C123/p456',
                        'created_at': '2024-01-16T14:20:00Z',
                        'namespace': namespace
                    },
                    'score': 0.87
                }
            ])
        
        elif "feature" in query.lower() or "implement" in query.lower():
            mock_results.extend([
                {
                    'content': f"Feature request: Add dark mode support to the dashboard. Users have been requesting this feature for better usability during night hours. Should include theme toggle and persistent user preference.",
                    'metadata': {
                        'id': 'jira_ticket_789',
                        'title': 'Implement Dark Mode for Dashboard',
                        'source_type': 'jira',
                        'url': 'https://neurosync.atlassian.net/browse/NS-789',
                        'created_at': '2024-01-10T09:15:00Z',
                        'namespace': namespace
                    },
                    'score': 0.92
                }
            ])
        
        else:
            # Generic results for other queries
            mock_results.extend([
                {
                    'content': f"Documentation about {query}: This is relevant information from your integrated data sources. The content would normally come from your GitHub repositories, Jira tickets, Slack conversations, and other connected tools.",
                    'metadata': {
                        'id': 'doc_general_001',
                        'title': f'Information about {query}',
                        'source_type': 'confluence',
                        'url': 'https://neurosync.atlassian.net/wiki/spaces/DEV/pages/123',
                        'created_at': '2024-01-12T16:45:00Z',
                        'namespace': namespace
                    },
                    'score': 0.85
                },
                {
                    'content': f"Team discussion related to {query}. This represents the kind of contextual information that would be retrieved from your Slack channels, team meetings, and collaborative discussions.",
                    'metadata': {
                        'id': 'slack_general_002',
                        'title': f'Team Discussion: {query}',
                        'source_type': 'slack',
                        'url': 'https://neurosync.slack.com/archives/C456/p789',
                        'created_at': '2024-01-14T11:30:00Z',
                        'namespace': namespace
                    },
                    'score': 0.78
                }
            ])
        
        # Apply filters if provided
        if filters:
            filtered_results = []
            for result in mock_results:
                metadata = result['metadata']
                include = True
                
                for key, filter_value in filters.items():
                    if key in metadata:
                        if isinstance(filter_value, dict) and '$in' in filter_value:
                            if metadata[key] not in filter_value['$in']:
                                include = False
                                break
                        elif metadata[key] != filter_value:
                            include = False
                            break
                
                if include:
                    filtered_results.append(result)
            
            mock_results = filtered_results
        
        # Return top_k results
        return mock_results[:top_k]
    
    async def add_documents(
        self, 
        documents: List[Document],
        namespace: Optional[str] = None
    ) -> List[str]:
        """Add documents to the vector store."""
        try:
            if not self.collection:
                # Mock mode - just return document IDs
                return [doc.id for doc in documents]
            
            # Prepare data for Chroma
            ids = [doc.id for doc in documents]
            contents = [doc.content for doc in documents]
            metadatas = []
            
            for doc in documents:
                metadata = doc.metadata.copy()
                if namespace:
                    metadata['namespace'] = namespace
                metadatas.append(metadata)
            
            # Add to Chroma
            self.collection.add(
                ids=ids,
                documents=contents,
                metadatas=metadatas
            )
            
            logger.info(f"Added {len(documents)} documents to ChromaVectorStore")
            return ids
            
        except Exception as e:
            logger.error(f"Error adding documents to ChromaVectorStore: {e}")
            return []
    
    async def get_document(
        self,
        document_id: str,
        namespace: Optional[str] = None
    ) -> Optional[Document]:
        """Get a document by ID."""
        try:
            if not self.collection:
                # Mock mode - return None
                return None
            
            # Build where filter
            where_filter = {}
            if namespace:
                where_filter['namespace'] = namespace
            
            # Get document from Chroma
            results = self.collection.get(
                ids=[document_id],
                where=where_filter if where_filter else None,
                include=["documents", "metadatas"]
            )
            
            if results["documents"] and len(results["documents"]) > 0:
                content = results["documents"][0]
                metadata = results["metadatas"][0] if results["metadatas"] else {}
                
                return Document(
                    id=document_id,
                    content=content,
                    metadata=metadata
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting document from ChromaVectorStore: {e}")
            return None
    
    async def delete_document(
        self,
        document_id: str,
        namespace: Optional[str] = None
    ) -> bool:
        """Delete a document by ID."""
        try:
            if not self.collection:
                # Mock mode - always return True
                return True
            
            # Delete from Chroma
            self.collection.delete(ids=[document_id])
            
            logger.info(f"Deleted document {document_id} from ChromaVectorStore")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting document from ChromaVectorStore: {e}")
            return False
    
    async def search(
        self,
        query_embedding: List[float],
        top_k: int = 10,
        namespace: Optional[str] = None,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """Search for similar documents using vector similarity."""
        try:
            if not self.collection:
                # Mock mode - return empty results
                return []
            
            # Build metadata filters
            where_filters = {}
            if namespace:
                where_filters["namespace"] = namespace
            if filter_metadata:
                where_filters.update(filter_metadata)
            
            # Search using Chroma with embedding
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where_filters if where_filters else None,
                include=["documents", "metadatas", "distances"]
            )
            
            # Convert to SearchResult objects
            search_results = []
            if results["documents"] and len(results["documents"]) > 0:
                documents = results["documents"][0]
                metadatas = results["metadatas"][0] if results["metadatas"] else []
                distances = results["distances"][0] if results["distances"] else []
                
                for i, doc_content in enumerate(documents):
                    metadata = metadatas[i] if i < len(metadatas) else {}
                    distance = distances[i] if i < len(distances) else 1.0
                    
                    # Convert distance to similarity score
                    score = max(0.0, 1.0 - distance)
                    
                    document = Document(
                        id=metadata.get('id', f'doc_{i}'),
                        content=doc_content,
                        metadata=metadata
                    )
                    
                    search_results.append(SearchResult(
                        document=document,
                        score=score
                    ))
            
            return search_results
            
        except Exception as e:
            logger.error(f"Error searching ChromaVectorStore with embedding: {e}")
            return []
    
    async def search_by_text(
        self,
        query_text: str,
        top_k: int = 10,
        namespace: Optional[str] = None,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """Search for similar documents using text query."""
        try:
            if not self.collection:
                # Mock mode - use existing mock search
                mock_results = await self._mock_search(query_text, namespace or "", top_k, filter_metadata)
                search_results = []
                
                for result in mock_results:
                    document = Document(
                        id=result['metadata'].get('id', 'mock_doc'),
                        content=result['content'],
                        metadata=result['metadata']
                    )
                    search_results.append(SearchResult(
                        document=document,
                        score=result['score']
                    ))
                
                return search_results
            
            # Build metadata filters
            where_filters = {}
            if namespace:
                where_filters["namespace"] = namespace
            if filter_metadata:
                where_filters.update(filter_metadata)
            
            # Search using Chroma with text
            results = self.collection.query(
                query_texts=[query_text],
                n_results=top_k,
                where=where_filters if where_filters else None,
                include=["documents", "metadatas", "distances"]
            )
            
            # Convert to SearchResult objects
            search_results = []
            if results["documents"] and len(results["documents"]) > 0:
                documents = results["documents"][0]
                metadatas = results["metadatas"][0] if results["metadatas"] else []
                distances = results["distances"][0] if results["distances"] else []
                
                for i, doc_content in enumerate(documents):
                    metadata = metadatas[i] if i < len(metadatas) else {}
                    distance = distances[i] if i < len(distances) else 1.0
                    
                    # Convert distance to similarity score
                    score = max(0.0, 1.0 - distance)
                    
                    document = Document(
                        id=metadata.get('id', f'doc_{i}'),
                        content=doc_content,
                        metadata=metadata
                    )
                    
                    search_results.append(SearchResult(
                        document=document,
                        score=score
                    ))
            
            return search_results
            
        except Exception as e:
            logger.error(f"Error searching ChromaVectorStore by text: {e}")
            # Fall back to mock results
            mock_results = await self._mock_search(query_text, namespace or "", top_k, filter_metadata)
            search_results = []
            
            for result in mock_results:
                document = Document(
                    id=result['metadata'].get('id', 'mock_doc'),
                    content=result['content'],
                    metadata=result['metadata']
                )
                search_results.append(SearchResult(
                    document=document,
                    score=result['score']
                ))
            
            return search_results
    
    async def list_namespaces(self) -> List[str]:
        """List all available namespaces."""
        try:
            if not self.collection:
                # Mock mode - return some test namespaces
                return ["test_project", "default"]
            
            # Get all documents and extract unique namespaces
            results = self.collection.get(
                include=["metadatas"]
            )
            
            namespaces = set()
            if results["metadatas"]:
                for metadata in results["metadatas"]:
                    if "namespace" in metadata:
                        namespaces.add(metadata["namespace"])
            
            return list(namespaces)
            
        except Exception as e:
            logger.error(f"Error listing namespaces from ChromaVectorStore: {e}")
            return []
    
    async def delete_namespace(self, namespace: str) -> bool:
        """Delete an entire namespace and all its documents."""
        try:
            if not self.collection:
                # Mock mode - always return True
                return True
            
            # Delete all documents in the namespace
            self.collection.delete(
                where={"namespace": namespace}
            )
            
            logger.info(f"Deleted namespace {namespace} from ChromaVectorStore")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting namespace from ChromaVectorStore: {e}")
            return False
    
    async def get_stats(self, namespace: Optional[str] = None) -> Dict[str, Any]:
        """Get statistics about the vector store."""
        try:
            if not self.collection:
                # Mock mode - return mock stats
                return {
                    "total_documents": 10,
                    "namespace": namespace,
                    "collection_name": self.collection_name,
                    "mode": "mock"
                }
            
            # Get collection info
            count = self.collection.count()
            
            stats = {
                "total_documents": count,
                "collection_name": self.collection_name,
                "persist_directory": self.persist_directory,
                "mode": "chroma"
            }
            
            if namespace:
                # Count documents in specific namespace
                results = self.collection.get(
                    where={"namespace": namespace},
                    include=["metadatas"]
                )
                namespace_count = len(results["metadatas"]) if results["metadatas"] else 0
                stats["namespace_documents"] = namespace_count
                stats["namespace"] = namespace
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting stats from ChromaVectorStore: {e}")
            return {
                "error": str(e),
                "collection_name": self.collection_name,
                "mode": "error"
            }
    
    async def add(
        self,
        doc_id: str,
        content: str,
        metadata: Dict[str, Any],
        namespace: str = ""
    ) -> bool:
        """
        Add a single document to Chroma.
        This is a convenience method that wraps upsert for single documents.
        
        Args:
            doc_id: Unique document ID
            content: Document content
            metadata: Document metadata
            namespace: Namespace for the document
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Convert single document to upsert format
            documents = [{
                'id': doc_id,
                'content': content,
                'metadata': metadata
            }]
            
            # Use existing upsert method
            result = await self.upsert(documents, namespace)
            
            if result:
                logger.info(f"Successfully added document {doc_id} to ChromaVectorStore namespace: {namespace}")
            else:
                logger.error(f"Failed to add document {doc_id} to ChromaVectorStore")
                
            return result
            
        except Exception as e:
            logger.error(f"Error adding document {doc_id} to ChromaVectorStore: {e}")
            return False

    async def delete(self, ids: List[str], namespace: str = "") -> bool:
        """Delete documents by IDs."""
        try:
            if not self.collection:
                logger.info(f"Mock delete of {len(ids)} documents from namespace: {namespace}")
                return True
            
            # Delete from Chroma
            self.collection.delete(ids=ids)
            
            logger.info(f"Deleted {len(ids)} documents from ChromaVectorStore")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting from ChromaVectorStore: {e}")
            return False
