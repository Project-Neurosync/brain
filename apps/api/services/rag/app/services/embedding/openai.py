"""
OpenAI embedding service implementation.
"""

import asyncio
from typing import Dict, List, Any, Optional
import numpy as np

from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.core.config import settings
from app.services.embedding.base import BaseEmbedding


class OpenAIEmbedding(BaseEmbedding):
    """OpenAI embedding service implementation."""
    
    # Model dimensions based on OpenAI documentation
    EMBEDDING_DIMENSIONS = {
        "text-embedding-3-small": 1536,
        "text-embedding-3-large": 3072,
        "text-embedding-ada-002": 1536,
    }
    
    def __init__(self):
        """Initialize OpenAI client."""
        self.api_key = settings.embedding.openai_api_key
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required for OpenAI embeddings")
            
        self.model = settings.embedding.openai_embedding_model
        self.client = AsyncOpenAI(api_key=self.api_key)
        self.dimension = self.EMBEDDING_DIMENSIONS.get(
            self.model,
            self.EMBEDDING_DIMENSIONS["text-embedding-3-small"]  # Default fallback
        )
        
        # Set batch size based on model - newer models support larger batches
        self.batch_size = 1000 if "text-embedding-3" in self.model else 100
        
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(Exception)
    )
    async def embed_query(self, query: str) -> List[float]:
        """Generate an embedding for a single query text."""
        try:
            response = await self.client.embeddings.create(
                model=self.model,
                input=query
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Error embedding query: {e}")
            # Return a zero vector of the correct dimension as fallback
            return [0.0] * self.dimension
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(Exception)
    )
    async def embed_documents(self, documents: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of documents."""
        if not documents:
            return []
            
        # Process in batches to avoid rate limits
        all_embeddings = []
        for i in range(0, len(documents), self.batch_size):
            batch = documents[i:i+self.batch_size]
            try:
                response = await self.client.embeddings.create(
                    model=self.model,
                    input=batch
                )
                # Sort embeddings by index to ensure order matches input
                sorted_embeddings = sorted(response.data, key=lambda x: x.index)
                embeddings = [item.embedding for item in sorted_embeddings]
                all_embeddings.extend(embeddings)
            except Exception as e:
                print(f"Error embedding batch: {e}")
                # Return zero vectors for the failed batch
                zero_embeddings = [[0.0] * self.dimension for _ in range(len(batch))]
                all_embeddings.extend(zero_embeddings)
        
        return all_embeddings
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of the embeddings."""
        return self.dimension
