"""
LLM factory for creating LLM instances based on configuration.
"""

from app.core.config import settings, ModelProvider
from app.services.llm.base import BaseLLM
from app.services.llm.groq import GroqLLM
from app.services.llm.openai import OpenAILLM


class LLMFactory:
    """Factory for creating LLM instances."""
    
    @staticmethod
    def create_llm() -> BaseLLM:
        """
        Create an LLM instance based on the configured provider.
        
        Returns:
            BaseLLM: An instance of the configured LLM provider.
            
        Raises:
            ValueError: If the configured provider is not supported.
        """
        provider = settings.model.provider
        
        if provider == ModelProvider.GROQ:
            return GroqLLM()
        elif provider == ModelProvider.OPENAI:
            return OpenAILLM()
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")


# Create a singleton instance
llm = LLMFactory.create_llm()
