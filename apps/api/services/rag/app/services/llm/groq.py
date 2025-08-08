"""
Groq LLM implementation.
"""

import asyncio
import tiktoken
from typing import Dict, List, Any, Optional, AsyncGenerator, Callable

from groq import AsyncGroq, AsyncGroqError
from groq.types.chat import ChatCompletionChunk

from app.core.config import settings
from app.services.llm.base import BaseLLM, ChatMessage, CompletionResponse


class GroqLLM(BaseLLM):
    """Groq LLM implementation."""
    
    def __init__(self):
        """Initialize the Groq client."""
        self.api_key = settings.model.groq_api_key
        if not self.api_key:
            raise ValueError("GROQ_API_KEY environment variable is required for Groq LLM")
            
        self.model_name = settings.model.groq_model_name
        self.client = AsyncGroq(api_key=self.api_key)
        self.encoder = tiktoken.encoding_for_model("gpt-4")  # Use GPT-4 encoding as fallback
        
    async def complete(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        streaming: Optional[bool] = False,
        callback: Optional[Callable[[str], None]] = None,
        **kwargs
    ) -> CompletionResponse:
        """Complete a prompt with Groq."""
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
        
        # Convert to chat format since Groq primarily uses chat completions
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
        except AsyncGroqError as e:
            # Handle API errors
            error_msg = f"Groq API error: {str(e)}"
            return CompletionResponse(text=error_msg, model=self.model_name)
        except Exception as e:
            # Handle other errors
            error_msg = f"Error completing prompt with Groq: {str(e)}"
            return CompletionResponse(text=error_msg, model=self.model_name)
            
    async def stream_complete(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Stream a completion from Groq."""
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
                    
        except AsyncGroqError as e:
            # Handle API errors
            yield f"Groq API error: {str(e)}"
        except Exception as e:
            # Handle other errors
            yield f"Error streaming completion from Groq: {str(e)}"
    
    async def chat_complete(
        self,
        messages: List[ChatMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        streaming: Optional[bool] = False,
        callback: Optional[Callable[[str], None]] = None,
        **kwargs
    ) -> CompletionResponse:
        """Complete a chat conversation with Groq."""
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
        
        # Convert messages to Groq format
        groq_messages = [{"role": m.role, "content": m.content} for m in messages]
        
        temp = temperature if temperature is not None else settings.model.temperature
        max_tok = max_tokens if max_tokens is not None else settings.model.max_tokens
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=groq_messages,
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
        except AsyncGroqError as e:
            # Handle API errors
            error_msg = f"Groq API error: {str(e)}"
            return CompletionResponse(text=error_msg, model=self.model_name)
        except Exception as e:
            # Handle other errors
            error_msg = f"Error completing chat with Groq: {str(e)}"
            return CompletionResponse(text=error_msg, model=self.model_name)
    
    async def stream_chat_complete(
        self,
        messages: List[ChatMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Stream a chat completion from Groq."""
        # Convert messages to Groq format
        groq_messages = [{"role": m.role, "content": m.content} for m in messages]
        
        temp = temperature if temperature is not None else settings.model.temperature
        max_tok = max_tokens if max_tokens is not None else settings.model.max_tokens
        
        try:
            stream = await self.client.chat.completions.create(
                model=self.model_name,
                messages=groq_messages,
                temperature=temp,
                max_tokens=max_tok,
                stream=True,
                **kwargs
            )
            
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except AsyncGroqError as e:
            # Handle API errors
            yield f"Groq API error: {str(e)}"
        except Exception as e:
            # Handle other errors
            yield f"Error streaming chat completion from Groq: {str(e)}"
    
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
