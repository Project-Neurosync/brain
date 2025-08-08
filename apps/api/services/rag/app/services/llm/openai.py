"""
OpenAI LLM implementation.
"""

import asyncio
import tiktoken
from typing import Dict, List, Any, Optional, AsyncGenerator, Callable, Union

from openai import AsyncOpenAI, AsyncOpenAIError
from openai.types.chat import ChatCompletionChunk

from app.core.config import settings
from app.services.llm.base import BaseLLM, ChatMessage, CompletionResponse


class OpenAILLM(BaseLLM):
    """OpenAI LLM implementation."""
    
    def __init__(self):
        """Initialize the OpenAI client."""
        self.api_key = settings.model.openai_api_key
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required for OpenAI LLM")
            
        self.model_name = settings.model.openai_model_name
        self.client = AsyncOpenAI(api_key=self.api_key)
        
        # Get appropriate tokenizer for the model
        try:
            self.encoder = tiktoken.encoding_for_model(self.model_name)
        except:
            # Fall back to cl100k_base for newer models or unknown models
            self.encoder = tiktoken.get_encoding("cl100k_base")
        
    async def complete(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        streaming: Optional[bool] = False,
        callback: Optional[Callable[[str], None]] = None,
        **kwargs
    ) -> CompletionResponse:
        """Complete a prompt with OpenAI."""
        if streaming and callback:
            # Handle streaming with callback
            response_text = ""
            async for chunk in self.stream_complete(
                prompt, 
                temperature=temperature, 
                max_tokens=max_tokens, 
                **kwargs
            ):
                response_text += chunk
                callback(chunk)
                
            return CompletionResponse(
                text=response_text,
                model=self.model_name,
                usage={"prompt_tokens": self.count_tokens(prompt)}
            )
        
        # Convert to chat format since newer OpenAI models primarily use chat completions
        messages = [{"role": "user", "content": prompt}]
        
        # Use the chat completion API
        temp = temperature if temperature is not None else settings.model.temperature
        max_tok = max_tokens if max_tokens is not None else settings.model.max_tokens
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=temp,
                max_tokens=max_tok,
                **kwargs
            )
            
            return CompletionResponse(
                text=response.choices[0].message.content,
                model=response.model,
                usage=response.usage.model_dump(),
                finish_reason=response.choices[0].finish_reason
            )
        except Exception as e:
            # Handle API errors
            error_msg = f"OpenAI API error: {str(e)}"
            return CompletionResponse(text=error_msg, model=self.model_name)
            
    async def stream_complete(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Stream a completion from OpenAI."""
        # Convert to chat format
        messages = [{"role": "user", "content": prompt}]
        
        temp = temperature if temperature is not None else settings.model.temperature
        max_tok = max_tokens if max_tokens is not None else settings.model.max_tokens
        
        try:
            stream = await self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=temp,
                max_tokens=max_tok,
                stream=True,
                **kwargs
            )
            
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            # Handle API errors
            yield f"OpenAI API error: {str(e)}"
    
    async def chat_complete(
        self,
        messages: List[ChatMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        streaming: Optional[bool] = False,
        callback: Optional[Callable[[str], None]] = None,
        **kwargs
    ) -> CompletionResponse:
        """Complete a chat conversation with OpenAI."""
        if streaming and callback:
            # Handle streaming with callback
            response_text = ""
            async for chunk in self.stream_chat_complete(
                messages, 
                temperature=temperature, 
                max_tokens=max_tokens, 
                **kwargs
            ):
                response_text += chunk
                callback(chunk)
                
            prompt_tokens = sum(self.count_tokens(m.content) for m in messages)
            return CompletionResponse(
                text=response_text,
                model=self.model_name,
                usage={"prompt_tokens": prompt_tokens}
            )
        
        # Convert messages to OpenAI format
        openai_messages = [{"role": m.role, "content": m.content} for m in messages]
        
        temp = temperature if temperature is not None else settings.model.temperature
        max_tok = max_tokens if max_tokens is not None else settings.model.max_tokens
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=openai_messages,
                temperature=temp,
                max_tokens=max_tok,
                **kwargs
            )
            
            return CompletionResponse(
                text=response.choices[0].message.content,
                model=response.model,
                usage=response.usage.model_dump(),
                finish_reason=response.choices[0].finish_reason
            )
        except Exception as e:
            # Handle API errors
            error_msg = f"OpenAI API error: {str(e)}"
            return CompletionResponse(text=error_msg, model=self.model_name)
    
    async def stream_chat_complete(
        self,
        messages: List[ChatMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Stream a chat completion from OpenAI."""
        # Convert messages to OpenAI format
        openai_messages = [{"role": m.role, "content": m.content} for m in messages]
        
        temp = temperature if temperature is not None else settings.model.temperature
        max_tok = max_tokens if max_tokens is not None else settings.model.max_tokens
        
        try:
            stream = await self.client.chat.completions.create(
                model=self.model_name,
                messages=openai_messages,
                temperature=temp,
                max_tokens=max_tok,
                stream=True,
                **kwargs
            )
            
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            # Handle API errors
            yield f"OpenAI API error: {str(e)}"
    
    def get_model_name(self) -> str:
        """Get the name of the model being used."""
        return self.model_name
    
    def count_tokens(self, text: str) -> int:
        """Count the number of tokens in the given text."""
        try:
            return len(self.encoder.encode(text))
        except Exception:
            # Fallback to rough estimate if tokenization fails
            return len(text) // 4  # Rough estimate of tokens per character
