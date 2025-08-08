"""
Production-ready RAG (Retrieval-Augmented Generation) service for NeuroSync.
Handles document retrieval, context building, and AI response generation.
"""

import logging
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from ..vectorstore.base import BaseVectorStore
from ..vectorstore.chroma import ChromaVectorStore
from ..llm.factory import LLMFactory
from models.database import get_db
from models.project import Project

logger = logging.getLogger(__name__)

class Document:
    """Document model for RAG system."""
    
    def __init__(self, content: str, metadata: Dict[str, Any] = None):
        self.content = content
        self.metadata = metadata or {}
        self.id = metadata.get('id', '')
        self.source_type = metadata.get('source_type', 'document')
        self.title = metadata.get('title', 'Untitled')
        self.url = metadata.get('url')
        self.created_at = metadata.get('created_at', datetime.utcnow())

class SearchResult:
    """Search result with document and relevance score."""
    
    def __init__(self, document: Document, score: float):
        self.document = document
        self.score = score

class RAGService:
    """Production-ready RAG service for NeuroSync."""
    
    def __init__(self, vector_store: BaseVectorStore = None):
        """Initialize RAG service with vector store."""
        self.vector_store = vector_store or ChromaVectorStore()
        self.llm = None
        logger.info("RAG service initialized")
    
    async def initialize(self):
        """Initialize the RAG service components."""
        try:
            # Initialize vector store
            await self.vector_store.initialize()
            
            # Initialize LLM
            self.llm = LLMFactory.get_llm()
            
            logger.info("RAG service components initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize RAG service: {e}")
            raise
    
    async def search_documents(
        self,
        query: str,
        project_id: Optional[str] = None,
        top_k: int = 5,
        source_types: Optional[List[str]] = None
    ) -> List[SearchResult]:
        """
        Search for relevant documents using vector similarity.
        
        Args:
            query: Search query text
            project_id: Optional project ID for filtering
            top_k: Number of top results to return
            source_types: Optional list of source types to filter by
            
        Returns:
            List of SearchResult objects
        """
        try:
            # Build namespace for project-specific search
            namespace = f"project_{project_id}" if project_id else "global"
            
            # Build metadata filters
            filters = {}
            if source_types:
                filters['source_type'] = {'$in': source_types}
            
            # Search vector store
            results = await self.vector_store.search(
                query=query,
                namespace=namespace,
                top_k=top_k,
                filters=filters
            )
            
            # Convert to SearchResult objects
            search_results = []
            for result in results:
                doc = Document(
                    content=result.get('content', ''),
                    metadata=result.get('metadata', {})
                )
                doc.score = result.get('score', 0.0)
                search_results.append(SearchResult(doc, doc.score))
            
            logger.info(f"Found {len(search_results)} documents for query: {query[:50]}...")
            return search_results
            
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            return []

    async def add_document(
        self,
        doc_id: str,
        content: str,
        metadata: Dict[str, Any]
    ) -> bool:
        """
        Add a document to the RAG system.
        
        Args:
            doc_id: Unique document identifier
            content: Document text content
            metadata: Document metadata including title, source, project_id, etc.
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Build namespace for project-specific storage
            project_id = metadata.get('project_id')
            namespace = f"project_{project_id}" if project_id else "global"
            
            # Add document to vector store
            success = await self.vector_store.add(
                doc_id=doc_id,
                content=content,
                metadata=metadata,
                namespace=namespace
            )
            
            if success:
                logger.info(f"Successfully added document {doc_id} to RAG system")
            else:
                logger.error(f"Failed to add document {doc_id} to RAG system")
                
            return success
            
        except Exception as e:
            logger.error(f"Error adding document {doc_id}: {e}")
            return False

    async def generate_response(
        self,
        query: str,
        context_documents: List[Document],
        project_id: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024
    ) -> Dict[str, Any]:
        """
        Generate AI response using retrieved documents as context.
        
        Args:
            query: User query
            context_documents: Retrieved documents for context
            project_id: Optional project ID
            temperature: LLM temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Dictionary with response, sources, and metadata
        """
        try:
            if not self.llm:
                self.llm = LLMFactory.get_llm()
            
            # Build context from documents
            context_parts = []
            sources = []
            
            for doc in context_documents:
                # Add document content to context
                context_parts.append(f"Source: {doc.title}\nContent: {doc.content}\n")
                
                # Add to sources list
                sources.append({
                    'title': doc.title,
                    'type': doc.source_type,
                    'url': doc.url,
                    'relevance_score': getattr(doc, 'score', 0.0)
                })
            
            context = "\n---\n".join(context_parts)
            
            # Build prompt with context
            project_context = f" about project {project_id}" if project_id else ""
            
            prompt = f"""You are NeuroSync AI, an intelligent assistant for software development teams. 
Based on the following context from the user's integrated data sources, please answer their question{project_context}.

Context from integrated sources:
{context}

Question: {query}

Please provide a helpful and accurate answer based on the context provided. If the context doesn't contain enough information to answer the question completely, please say so and provide what information you can. Be specific and reference the sources when relevant."""

            # Generate response
            response = await self.llm.complete(
                prompt=prompt,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return {
                'answer': response.text or "I'm sorry, I couldn't generate a response.",
                'sources': sources,
                'confidence': self._calculate_confidence(context_documents, query),
                'context_used': len(context_documents),
                'tokens_used': getattr(response, 'usage', {}).get('total_tokens', 0)
            }
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return {
                'answer': "I'm sorry, I encountered an error while generating a response.",
                'sources': [],
                'confidence': 0.0,
                'context_used': 0,
                'tokens_used': 0
            }
    
    async def query(
        self,
        query: str,
        project_id: Optional[str] = None,
        max_results: int = 5,
        include_sources: bool = True,
        source_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Complete RAG query: search + generate response.
        
        Args:
            query: User query
            project_id: Optional project ID for filtering
            max_results: Maximum number of documents to retrieve
            include_sources: Whether to include source information
            source_types: Optional list of source types to filter by
            
        Returns:
            Complete response with answer, sources, and metadata
        """
        try:
            # Search for relevant documents
            search_results = await self.search_documents(
                query=query,
                project_id=project_id,
                top_k=max_results,
                source_types=source_types
            )
            
            # Extract documents
            documents = [result.document for result in search_results]
            
            # Generate response
            response = await self.generate_response(
                query=query,
                context_documents=documents,
                project_id=project_id
            )
            
            # Add search metadata
            response['search_results'] = len(search_results)
            response['query'] = query
            response['project_id'] = project_id
            
            if not include_sources:
                response.pop('sources', None)
            
            return response
            
        except Exception as e:
            logger.error(f"Error in RAG query: {e}")
            return {
                'answer': "I'm sorry, I encountered an error while processing your query.",
                'sources': [],
                'confidence': 0.0,
                'search_results': 0,
                'query': query,
                'project_id': project_id
            }
    
    def _calculate_confidence(self, documents: List[Document], query: str) -> float:
        """Calculate confidence score based on retrieved documents."""
        if not documents:
            return 0.0
        
        # Simple confidence calculation based on number and quality of documents
        base_confidence = min(len(documents) / 5.0, 1.0)  # More documents = higher confidence
        
        # Adjust based on document relevance (if available)
        avg_score = sum(getattr(doc, 'score', 0.5) for doc in documents) / len(documents)
        
        return min(base_confidence * avg_score, 1.0)
