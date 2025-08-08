"""
Base abstract class for LLM providers.
This defines the interface that all LLM implementations must follow.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, AsyncGenerator, Union, Callable
from pydantic import BaseModel


class ChatMessage(BaseModel):
    """Chat message structure."""
    role: str  # 'system', 'user', 'assistant'
    content: str


class CompletionResponse(BaseModel):
    """Response model for completions."""
    text: str
    usage: Dict[str, int] = {}
    model: str = ""
    finish_reason: Optional[str] = None
    

class BaseLLM(ABC):
    """Abstract base class for LLM implementations."""
    
    @abstractmethod
    async def complete(
        self, 
        prompt: str, 
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        streaming: Optional[bool] = False,
        callback: Optional[Callable[[str], None]] = None,
        **kwargs
    ) -> CompletionResponse:
        """
        Complete a prompt with the LLM.
        
        Args:
            prompt: The prompt to complete
            temperature: Control randomness (0-1)
            max_tokens: Maximum tokens to generate
            streaming: Whether to stream the response
            callback: Function to call with each chunk when streaming
            **kwargs: Additional model-specific parameters
            
        Returns:
            CompletionResponse with the generated text and metadata
        """
        pass

    @abstractmethod
    async def stream_complete(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        Stream a completion from the LLM.
        
        Args:
            prompt: The prompt to complete
            temperature: Control randomness (0-1)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional model-specific parameters
            
        Yields:
            Chunks of the generated text as they become available
        """
        pass
    
    @abstractmethod
    async def chat_complete(
        self,
        messages: List[ChatMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        streaming: Optional[bool] = False,
        callback: Optional[Callable[[str], None]] = None,
        **kwargs
    ) -> CompletionResponse:
        """
        Complete a chat conversation with the LLM.
        
        Args:
            messages: List of chat messages
            temperature: Control randomness (0-1)
            max_tokens: Maximum tokens to generate
            streaming: Whether to stream the response
            callback: Function to call with each chunk when streaming
            **kwargs: Additional model-specific parameters
            
        Returns:
            CompletionResponse with the generated text and metadata
        """
        pass

    @abstractmethod
    async def stream_chat_complete(
        self,
        messages: List[ChatMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        Stream a chat completion from the LLM.
        
        Args:
            messages: List of chat messages
            temperature: Control randomness (0-1)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional model-specific parameters
            
        Yields:
            Chunks of the generated text as they become available
        """
        pass

    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """
        Count the number of tokens in a text string.
        
        Args:
            text: The text to count tokens for
            
        Returns:
            Number of tokens
        """
        pass

    @abstractmethod
    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """
        Estimate the cost of a completion based on token counts.
        
        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            
        Returns:
            Estimated cost in USD
        """
        pass
