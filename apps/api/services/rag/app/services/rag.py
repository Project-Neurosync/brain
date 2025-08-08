"""
RAG (Retrieval-Augmented Generation) service for question answering.

This service combines the retrieval of relevant documents with an LLM to generate
accurate and grounded responses to user queries.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Union, Tuple, Callable, AsyncGenerator

# Remove problematic imports for now - we'll use direct instantiation
# from app.core.config import settings
# from app.services.vectorstore.base import Document
# from app.services.llm.factory import llm
# from app.services.retriever import RetrieverService

import os
from typing import Dict, List, Any, Optional

# Set up logger
logger = logging.getLogger(__name__)


class RAGService:
    """RAG service for question answering."""
    
    def __init__(
        self,
        retriever: Optional[RetrieverService] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ):
        """
        Initialize the RAG service.
        
        Args:
            retriever: Retriever service. If not provided, a new one will be created.
            max_tokens: Maximum tokens for LLM response.
            temperature: Temperature for LLM response generation.
        """
        self.retriever = retriever or RetrieverService()
        self.max_tokens = max_tokens or settings.model.max_tokens
        self.temperature = temperature or settings.model.temperature
        
    async def add_documents(
        self,
        texts: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        namespace: Optional[str] = None,
        document_ids: Optional[List[str]] = None,
    ) -> List[str]:
        """
        Add documents to the retrieval system.
        
        Args:
            texts: List of text contents to add
            metadatas: Optional list of metadata dictionaries for each text
            namespace: Optional namespace to add documents to
            document_ids: Optional list of document IDs to use
            
        Returns:
            List of document IDs that were added
        """
        return await self.retriever.add_texts(texts, metadatas, namespace, document_ids)
    
    async def generate_answer(
        self,
        question: str,
        namespace: Optional[str] = None,
        k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None,
        streaming: bool = False,
        callback: Optional[Callable[[str], None]] = None,
    ) -> Union[str, AsyncGenerator[str, None]]:
        """
        Generate an answer to a question using RAG.
        
        Args:
            question: The user's question
            namespace: Optional namespace to search in
            k: Number of documents to retrieve
            filter_metadata: Optional metadata filter for retrieval
            streaming: Whether to stream the response
            callback: Optional callback function for streaming
            
        Returns:
            The generated answer or a streaming generator
        """
        # Retrieve relevant documents
        documents = await self.retriever.similarity_search(
            query=question,
            k=k,
            filter_metadata=filter_metadata,
            namespace=namespace,
            rerank=True,
        )
        
        # Prepare prompt with retrieved context
        prompt = self._create_prompt(question, documents)
        
        # Generate answer with LLM
        if streaming:
            return self._stream_answer(prompt, callback)
        else:
            response = await llm.complete(
                prompt=prompt,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
            return response.text
    
    async def _stream_answer(
        self,
        prompt: str,
        callback: Optional[Callable[[str], None]] = None,
    ) -> AsyncGenerator[str, None]:
        """Stream the answer from the LLM."""
        async for chunk in llm.stream_complete(
            prompt=prompt,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        ):
            if callback:
                callback(chunk)
            yield chunk
    
    def _create_prompt(self, question: str, documents: List[Document]) -> str:
        """
        Create a prompt for the LLM with retrieved documents as context.
        
        Args:
            question: The user's question
            documents: Retrieved relevant documents
            
        Returns:
            A formatted prompt string
        """
        # Extract and format context from documents
        context_parts = []
        for i, doc in enumerate(documents):
            context_parts.append(f"Document {i+1}:\n{doc.content}\n")
        
        context = "\n".join(context_parts)
        
        # Create full prompt with context and question
        return f"""
You are a helpful AI assistant. Answer the question based ONLY on the following context:

{context}

Question: {question}

Answer:
""".strip()
    
    def _format_sources(self, documents: List[Document]) -> str:
        """Format source information for retrieved documents."""
        sources = []
        for i, doc in enumerate(documents):
            source_info = f"Source {i+1}: "
            
            # Get source information from metadata if available
            if "source" in doc.metadata:
                source_info += doc.metadata["source"]
            elif "url" in doc.metadata:
                source_info += doc.metadata["url"]
            elif "title" in doc.metadata:
                source_info += doc.metadata["title"]
            elif "file_path" in doc.metadata:
                source_info += doc.metadata["file_path"]
            else:
                source_info += f"Document ID: {doc.id}"
                
            sources.append(source_info)
        
        return "\n".join(sources)
