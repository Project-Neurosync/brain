"""
Base abstract class for embedding services.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union


class BaseEmbedding(ABC):
    """Abstract base class for embedding services."""
    
    @abstractmethod
    async def embed_query(self, query: str) -> List[float]:
        """
        Generate an embedding for a single query text.
        
        Args:
            query: The text to embed
            
        Returns:
            List of embedding values representing the text
        """
        pass
    
    @abstractmethod
    async def embed_documents(self, documents: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of documents.
        
        Args:
            documents: List of texts to embed
            
        Returns:
            List of embeddings, one for each document
        """
        pass
    
    @abstractmethod
    def get_embedding_dimension(self) -> int:
        """
        Get the dimension of the embeddings.
        
        Returns:
            Dimension of the embedding vectors
        """
        pass
