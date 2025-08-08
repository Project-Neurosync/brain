"""
LLM factory for creating and managing LLM instances.
"""

import os
import logging
from typing import Optional

from .base import BaseLLM
from .groq import GroqLLM

logger = logging.getLogger(__name__)


class LLMFactory:
    """Factory for creating LLM instances."""
    
    _instance: Optional[BaseLLM] = None
    
    @classmethod
    def get_llm(cls, provider: str = "groq") -> BaseLLM:
        """Get an LLM instance."""
        if cls._instance is None:
            cls._instance = cls.create_llm(provider)
        return cls._instance
    
    @classmethod
    def create_llm(cls, provider: str = "groq") -> BaseLLM:
        """Create a new LLM instance."""
        if provider.lower() == "groq":
            api_key = os.getenv("GROQ_API_KEY")
            if not api_key:
                raise ValueError("GROQ_API_KEY environment variable not set")
            model_name = os.getenv("GROQ_MODEL", "llama3-8b-8192")
            
            logger.info(f"Creating Groq LLM with model: {model_name}")
            return GroqLLM(api_key=api_key, model_name=model_name)
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")


# Global LLM instance
llm = LLMFactory.get_llm()
