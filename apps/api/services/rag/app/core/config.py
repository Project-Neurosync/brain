"""
Configuration management for the advanced RAG system.
Supports environment variables and model provider switching.
"""

import os
from enum import Enum
from typing import Dict, Any, Optional, List
from pydantic import BaseSettings, Field, validator


class ModelProvider(str, Enum):
    """Supported model providers."""
    GROQ = "groq"
    OPENAI = "openai"
    OLLAMA = "ollama"
    ANTHROPIC = "anthropic"


class ModelConfig(BaseSettings):
    """Model configuration settings."""
    provider: ModelProvider = Field(
        default=ModelProvider.GROQ,
        description="The LLM provider to use (groq, openai, ollama, anthropic)"
    )
    
    # Groq settings
    groq_api_key: Optional[str] = Field(None, env="GROQ_API_KEY")
    groq_model_name: str = Field("llama3-70b-8192", env="GROQ_MODEL_NAME")
    
    # OpenAI settings
    openai_api_key: Optional[str] = Field(None, env="OPENAI_API_KEY")
    openai_model_name: str = Field("gpt-4", env="OPENAI_MODEL_NAME")
    
    # Ollama settings
    ollama_base_url: str = Field("http://localhost:11434", env="OLLAMA_BASE_URL")
    ollama_model_name: str = Field("llama3:8b-instruct-q4_K_M", env="OLLAMA_MODEL_NAME")
    
    # Anthropic settings
    anthropic_api_key: Optional[str] = Field(None, env="ANTHROPIC_API_KEY")
    anthropic_model_name: str = Field("claude-3-opus-20240229", env="ANTHROPIC_MODEL_NAME")
    
    # Common model settings
    temperature: float = Field(0.2, env="MODEL_TEMPERATURE")
    max_tokens: int = Field(4000, env="MODEL_MAX_TOKENS")
    streaming: bool = Field(True, env="MODEL_STREAMING")
    
    @validator('provider')
    def validate_provider_api_key(cls, v, values):
        """Validate that the API key is set for the selected provider."""
        if v == ModelProvider.GROQ and not values.get('groq_api_key'):
            raise ValueError("GROQ_API_KEY must be set when using Groq provider")
        if v == ModelProvider.OPENAI and not values.get('openai_api_key'):
            raise ValueError("OPENAI_API_KEY must be set when using OpenAI provider")
        if v == ModelProvider.ANTHROPIC and not values.get('anthropic_api_key'):
            raise ValueError("ANTHROPIC_API_KEY must be set when using Anthropic provider")
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = False


class VectorStoreConfig(BaseSettings):
    """Vector store configuration settings."""
    provider: str = Field("chroma", env="VECTOR_PROVIDER")  # chroma, pinecone
    
    # ChromaDB settings
    chroma_persist_directory: str = Field("./chroma_db", env="CHROMA_PERSIST_DIRECTORY")
    
    # Pinecone settings
    pinecone_api_key: Optional[str] = Field(None, env="PINECONE_API_KEY")
    pinecone_environment: Optional[str] = Field(None, env="PINECONE_ENVIRONMENT")
    pinecone_index_name: Optional[str] = Field(None, env="PINECONE_INDEX_NAME")
    
    # Embedding model settings
    embedding_model_name: str = Field(
        "sentence-transformers/all-MiniLM-L6-v2", 
        env="EMBEDDING_MODEL_NAME"
    )

    class Config:
        env_file = ".env"
        case_sensitive = False


class MCPConfig(BaseSettings):
    """Model Control Protocol configuration."""
    enabled: bool = Field(False, env="MCP_ENABLED")
    server_url: Optional[str] = Field(None, env="MCP_SERVER_URL")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


class Settings(BaseSettings):
    """Main application settings."""
    app_name: str = Field("Advanced RAG System", env="APP_NAME")
    debug: bool = Field(False, env="DEBUG")
    
    # API settings
    api_prefix: str = Field("/api/v1", env="API_PREFIX")
    api_host: str = Field("0.0.0.0", env="API_HOST")
    api_port: int = Field(8000, env="API_PORT")
    
    # Document processing
    chunk_size: int = Field(1000, env="CHUNK_SIZE")
    chunk_overlap: int = Field(200, env="CHUNK_OVERLAP")
    
    # Model settings
    model: ModelConfig = ModelConfig()
    
    # Vector store settings
    vector_store: VectorStoreConfig = VectorStoreConfig()
    
    # MCP settings
    mcp: MCPConfig = MCPConfig()
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Create settings instance
settings = Settings()
