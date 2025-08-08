"""
Groq LLM implementation for NeuroSync using direct HTTP API.
"""

import asyncio
import logging
import logging
import os
import json
import aiohttp
from typing import Dict, List, Any, Optional, AsyncGenerator, Callable
from pydantic import BaseModel, Field

try:
    import tiktoken
except ImportError:
    tiktoken = None

from .base import BaseLLM, ChatMessage, CompletionResponse as BaseCompletionResponse

logger = logging.getLogger(__name__)


class CompletionUsage(BaseModel):
    """Token usage information from Groq API."""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    
    class Config:
        extra = "ignore"  # Ignore extra fields like queue_time


class CompletionChoice(BaseModel):
    """Completion choice from Groq API."""
    index: int
    message: Dict[str, Any]
    finish_reason: Optional[str] = None


class CompletionResponse(BaseModel):
    """Response from Groq API completion."""
    id: str
    object: str
    created: int
    model: str
    choices: List[CompletionChoice]
    usage: CompletionUsage
    
    class Config:
        extra = "ignore"  # Ignore extra fields


class GroqLLM(BaseLLM):
    """Groq LLM implementation using direct HTTP API."""
    
    def __init__(self, api_key: str, model_name: str = "llama3-8b-8192"):
        """Initialize the Groq HTTP client."""
        logger.info(f"GroqLLM.__init__ called with model: {model_name}")
        
        self.api_key = api_key
        if not self.api_key:
            logger.error("No API key provided to GroqLLM")
            raise ValueError("GROQ_API_KEY is required for Groq LLM")
            
        logger.info(f"API key provided: {self.api_key[:20]}...")
        self.model_name = model_name
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"
        
        logger.info(f"GroqLLM initialized successfully with HTTP method")
        
        # Initialize encoder if tiktoken is available
        if tiktoken:
            try:
                self.encoder = tiktoken.encoding_for_model("gpt-4")
            except:
                self.encoder = None
        else:
            self.encoder = None
        
        # Groq pricing (approximate, as of 2024)
        self.input_cost_per_token = 0.0000001  # $0.0001 per 1K tokens
        self.output_cost_per_token = 0.0000002  # $0.0002 per 1K tokens
        
    async def _http_chat_complete(
        self,
        messages: List[ChatMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> BaseCompletionResponse:
        """HTTP method for Groq API using exact working implementation."""
        logger.info(f"🔥 Making HTTP request to Groq API...")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Convert ChatMessage objects to dict format
        message_dicts = []
        for msg in messages:
            if hasattr(msg, 'role') and hasattr(msg, 'content'):
                message_dicts.append({"role": msg.role, "content": msg.content})
            else:
                # Handle dict format
                message_dicts.append(msg)
        
        data = {
            "model": self.model_name,
            "messages": message_dicts,
            "temperature": temperature or 0.7,
            "max_tokens": max_tokens or 1024
        }
        
        logger.info(f"🔥 Request data: {json.dumps(data, indent=2)[:200]}...")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.base_url, headers=headers, json=data) as response:
                    logger.info(f"🔥 Response status: {response.status}")
                    
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"🔥 SUCCESS! Groq API response received")
                        
                        # Extract text from Groq API response
                        text = ""
                        if "choices" in result and len(result["choices"]) > 0:
                            message = result["choices"][0].get("message", {})
                            text = message.get("content", "")
                        
                        # Extract usage information
                        usage_info = result.get("usage", {})
                        usage = {
                            "prompt_tokens": usage_info.get("prompt_tokens", 0),
                            "completion_tokens": usage_info.get("completion_tokens", 0),
                            "total_tokens": usage_info.get("total_tokens", 0)
                        }
                        
                        # Return in expected BaseCompletionResponse format
                        return BaseCompletionResponse(
                            text=text,
                            usage=usage,
                            model=result.get("model", self.model_name),
                            finish_reason=result["choices"][0].get("finish_reason") if result.get("choices") else None
                        )
                    else:
                        error_text = await response.text()
                        logger.error(f"🔥 ERROR! HTTP {response.status}: {error_text}")
                        raise Exception(f"HTTP {response.status}: {error_text}")
                        
        except Exception as e:
            logger.error(f"🔥 EXCEPTION: {e}")
            raise
        
    async def complete(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        streaming: Optional[bool] = False,
        callback: Optional[Callable[[str], None]] = None,
        **kwargs
    ) -> BaseCompletionResponse:
        """Complete a prompt with Groq using HTTP method."""
        logger.info(f"🔥 GroqLLM.complete called with HTTP method")
        
        # Convert prompt to messages format
        messages = [ChatMessage(role="user", content=prompt)]
        return await self._http_chat_complete(
            messages, 
            temperature=temperature, 
            max_tokens=max_tokens
        )

    async def stream_complete(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Stream a completion from Groq."""
        messages = [ChatMessage(role="user", content=prompt)]
        async for chunk in self.stream_chat_complete(
            messages, 
            temperature=temperature, 
            max_tokens=max_tokens, 
            **kwargs
        ):
            yield chunk
    
    async def chat_complete(
        self,
        messages: List[ChatMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        streaming: Optional[bool] = False,
        callback: Optional[Callable[[str], None]] = None,
        **kwargs
    ) -> BaseCompletionResponse:
        """Complete a chat conversation with Groq using HTTP method."""
        logger.info(f"🔥 GroqLLM.chat_complete called with HTTP method")
        
        return await self._http_chat_complete(
            messages, 
            temperature=temperature, 
            max_tokens=max_tokens
        )

    async def stream_chat_complete(
        self,
        messages: List[ChatMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Stream a chat completion from Groq (simplified for now)."""
        logger.info(f"🔥 GroqLLM.stream_chat_complete called - using non-streaming fallback")
        
        # For now, use non-streaming and yield the complete response
        # TODO: Implement proper streaming with HTTP method later
        response = await self._http_chat_complete(
            messages, 
            temperature=temperature, 
            max_tokens=max_tokens
        )
        
        # Extract text from response and yield it
        if response.text:
            # Simulate streaming by yielding the text in chunks
            text = response.text
            chunk_size = 50  # Characters per chunk
            
            for i in range(0, len(text), chunk_size):
                chunk = text[i:i + chunk_size]
                yield chunk
                # Small delay to simulate streaming
                await asyncio.sleep(0.1)
        else:
            yield "I'm sorry, I couldn't generate a response."

    def count_tokens(self, text: str) -> int:
        """Count the number of tokens in a text string."""
        try:
            if self.encoder:
                return len(self.encoder.encode(text))
            else:
                # Fallback: rough estimation
                return int(len(text.split()) * 1.3)  # Approximate tokens per word
        except Exception:
            # Fallback: rough estimation
            return int(len(text.split()) * 1.3)  # Approximate tokens per word

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Estimate the cost of a completion based on token counts."""
        input_cost = input_tokens * self.input_cost_per_token
        output_cost = output_tokens * self.output_cost_per_token
        return input_cost + output_cost
