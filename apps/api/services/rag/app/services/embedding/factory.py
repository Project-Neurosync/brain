"""
Embedding factory for creating embedding service instances based on configuration.
"""

from app.core.config import settings, EmbeddingProvider
from app.services.embedding.base import BaseEmbedding
from app.services.embedding.openai import OpenAIEmbedding


class EmbeddingFactory:
    """Factory for creating embedding service instances."""
    
    @staticmethod
    def create_embedding_service() -> BaseEmbedding:
        """
        Create an embedding service instance based on the configured provider.
        
        Returns:
            BaseEmbedding: An instance of the configured embedding provider.
            
        Raises:
            ValueError: If the configured provider is not supported.
        """
        provider = settings.embedding.provider
        
        if provider == EmbeddingProvider.OPENAI:
            return OpenAIEmbedding()
        else:
            raise ValueError(f"Unsupported embedding provider: {provider}")


# Create a singleton instance
embedding_service = EmbeddingFactory.create_embedding_service()
