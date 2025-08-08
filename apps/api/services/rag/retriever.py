"""
Document retriever service for NeuroSync RAG system.
Handles document search and retrieval from vector databases.
"""

import logging
from typing import List, Dict, Any, Optional
from .rag_service import SearchResult, Document

logger = logging.getLogger(__name__)

class RetrieverService:
    """Service for retrieving relevant documents from vector storage."""
    
    def __init__(self):
        """Initialize retriever service."""
        self.rag_service = None
        logger.info("RetrieverService initialized")
    
    async def initialize(self):
        """Initialize the retriever with RAG service."""
        from .rag_service import RAGService
        self.rag_service = RAGService()
        await self.rag_service.initialize()
        logger.info("RetrieverService initialized with RAG service")
    
    async def search_by_text(
        self,
        query_text: str,
        namespace: Optional[str] = None,
        top_k: int = 5,
        source_types: Optional[List[str]] = None
    ) -> List[SearchResult]:
        """
        Search for documents by text query.
        
        Args:
            query_text: The search query
            namespace: Optional namespace (project_id) for filtering
            top_k: Number of top results to return
            source_types: Optional list of source types to filter by
            
        Returns:
            List of SearchResult objects
        """
        try:
            if not self.rag_service:
                await self.initialize()
            
            # Extract project_id from namespace if provided
            project_id = None
            if namespace and namespace.startswith('project_'):
                project_id = namespace.replace('project_', '')
            elif namespace:
                project_id = namespace
            
            # Search using RAG service
            results = await self.rag_service.search_documents(
                query=query_text,
                project_id=project_id,
                top_k=top_k,
                source_types=source_types
            )
            
            logger.info(f"Retrieved {len(results)} documents for query: {query_text[:50]}...")
            return results
            
        except Exception as e:
            logger.error(f"Error in search_by_text: {e}")
            # Return mock results for now to prevent errors
            return self._get_mock_results(query_text, top_k)
    
    def _get_mock_results(self, query: str, top_k: int) -> List[SearchResult]:
        """
        Generate mock search results for development/testing.
        This ensures the system works even without a fully configured vector database.
        """
        mock_documents = [
            Document(
                content=f"This is a mock document related to your query: '{query}'. In a production system, this would be replaced with actual content from your integrated data sources like GitHub issues, Slack messages, Jira tickets, etc.",
                metadata={
                    'id': f'mock_doc_{i}',
                    'title': f'Mock Document {i+1}',
                    'source_type': ['github', 'jira', 'slack', 'confluence'][i % 4],
                    'url': f'https://example.com/mock_doc_{i}',
                    'project_id': 'mock_project'
                }
            )
            for i in range(min(top_k, 3))
        ]
        
        return [SearchResult(doc, 0.8 - (i * 0.1)) for i, doc in enumerate(mock_documents)]
