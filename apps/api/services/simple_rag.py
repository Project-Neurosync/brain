"""
Simple RAG service for NeuroSync that works with the existing chat system.
This searches real uploaded documents from the database.
"""

import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from models.database import get_db
from models.document import Document

logger = logging.getLogger(__name__)

class SimpleDocument:
    """Simple document model."""
    
    def __init__(self, content: str, metadata: Dict[str, Any] = None):
        self.content = content
        self.metadata = metadata or {}
        self.title = metadata.get('title', 'Untitled') if metadata else 'Untitled'
        self.source_type = metadata.get('source_type', 'document') if metadata else 'document'
        self.url = metadata.get('url') if metadata else None

class SimpleSearchResult:
    """Simple search result."""
    
    def __init__(self, document: SimpleDocument, score: float):
        self.document = document
        self.score = score

class SimpleRAGService:
    """Simple RAG service that searches real uploaded documents."""
    
    def __init__(self):
        """Initialize simple RAG service."""
        self.initialized = False
        logger.info("SimpleRAGService initialized")
    
    async def initialize(self):
        """Initialize the service."""
        self.initialized = True
        logger.info("SimpleRAGService initialized successfully")
    
    def _calculate_relevance_score(self, document_content: str, query: str) -> float:
        """Calculate a simple relevance score based on keyword matching."""
        query_words = query.lower().split()
        content_words = document_content.lower().split()
        
        # Count matching words
        matches = sum(1 for word in query_words if word in content_words)
        
        # Calculate score as percentage of query words found
        if len(query_words) == 0:
            return 0.0
        
        score = matches / len(query_words)
        return min(score, 1.0)  # Cap at 1.0
    
    async def search_documents(
        self,
        query: str,
        project_id: Optional[str] = None,
        top_k: int = 5
    ) -> List[SimpleSearchResult]:
        """
        Search for relevant documents in the database.
        Returns real uploaded documents that match the query.
        """
        try:
            # Get database session
            db = next(get_db())
            
            # Query documents from database
            db_query = db.query(Document)
            
            # Filter by project if specified
            if project_id:
                db_query = db_query.filter(Document.project_id == project_id)
            
            # Get all documents
            documents = db_query.all()
            
            logger.info(f"SimpleRAGService found {len(documents)} documents for query: {query[:50]}...")
            
            if not documents:
                # Return empty results if no documents found
                return []
            
            # Calculate relevance scores and create results
            results = []
            for doc in documents:
                # Calculate relevance score
                score = self._calculate_relevance_score(doc.content, query)
                
                # Only include documents with some relevance
                if score > 0.0:
                    simple_doc = SimpleDocument(
                        content=doc.content,
                        metadata={
                            'title': doc.title,
                            'source_type': doc.source,
                            'url': doc.document_metadata.get('url') if doc.document_metadata else None,
                            'project_id': str(doc.project_id),
                            'filename': doc.document_metadata.get('filename') if doc.document_metadata else doc.title,
                            'document_id': str(doc.id)
                        }
                    )
                    results.append(SimpleSearchResult(simple_doc, score))
            
            # Sort by relevance score (highest first)
            results.sort(key=lambda x: x.score, reverse=True)
            
            # Return top_k results
            top_results = results[:top_k]
            
            logger.info(f"Returning {len(top_results)} relevant documents")
            return top_results
            
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            # Return empty results on error
            return []
