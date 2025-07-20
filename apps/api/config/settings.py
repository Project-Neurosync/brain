"""
NeuroSync AI Backend - Configuration Settings
Centralized configuration management using Pydantic settings
"""

import os
from typing import Optional, List
from pydantic import Field
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Application settings
    app_name: str = Field(default="NeuroSync AI Backend", description="Application name")
    app_version: str = Field(default="1.0.0", description="Application version")
    debug: bool = Field(default=False, description="Debug mode")
    environment: str = Field(default="development", description="Environment (development, staging, production)")
    
    # Server settings
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")
    reload: bool = Field(default=True, description="Auto-reload on code changes")
    workers: int = Field(default=1, description="Number of worker processes")
    
    # Security settings
    secret_key: str = Field(default="dev-secret-key-change-in-production", description="Secret key for JWT and encryption")
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    jwt_expiration_hours: int = Field(default=24, description="JWT token expiration in hours")
    cors_origins: List[str] = Field(default=["*"], description="CORS allowed origins")
    
    # Database settings
    database_url: str = Field(default="sqlite:///./neurosync.db", description="Database connection URL")
    database_echo: bool = Field(default=False, description="Echo SQL queries")
    database_pool_size: int = Field(default=10, description="Database connection pool size")
    database_max_overflow: int = Field(default=20, description="Database max overflow connections")
    
    # Vector database settings
    vector_db_path: str = Field(default="./data/chroma", description="ChromaDB storage path")
    embedding_model: str = Field(default="all-MiniLM-L6-v2", description="Sentence transformer model")
    vector_db_reset: bool = Field(default=False, description="Reset vector database on startup")
    
    # AI service settings
    openai_api_key: str = Field(default="sk-test-key-replace-with-real-key", description="OpenAI API key")
    ai_model: str = Field(default="gpt-4", description="OpenAI model to use")
    ai_temperature: float = Field(default=0.7, description="Default AI temperature")
    ai_max_tokens: int = Field(default=1000, description="Default max tokens")
    ai_timeout: int = Field(default=60, description="AI request timeout in seconds")
    
    # Redis settings (for caching and sessions)
    redis_url: str = Field(default="redis://localhost:6379", description="Redis connection URL")
    redis_password: Optional[str] = Field(default=None, description="Redis password")
    redis_db: int = Field(default=0, description="Redis database number")
    cache_ttl: int = Field(default=3600, description="Default cache TTL in seconds")
    
    # Authentication settings
    auth_provider: str = Field(default="auth0", description="Authentication provider (auth0, firebase, custom)")
    auth0_domain: Optional[str] = Field(default=None, description="Auth0 domain")
    auth0_client_id: Optional[str] = Field(default=None, description="Auth0 client ID")
    auth0_client_secret: Optional[str] = Field(default=None, description="Auth0 client secret")
    auth0_audience: Optional[str] = Field(default=None, description="Auth0 API audience")
    
    # File storage settings
    storage_provider: str = Field(default="local", description="Storage provider (local, s3, gcs)")
    storage_bucket: Optional[str] = Field(default=None, description="Storage bucket name")
    storage_region: Optional[str] = Field(default=None, description="Storage region")
    storage_access_key: Optional[str] = Field(default=None, description="Storage access key")
    storage_secret_key: Optional[str] = Field(default=None, description="Storage secret key")
    upload_max_size: int = Field(default=100 * 1024 * 1024, description="Max upload size in bytes (100MB)")
    
    # Integration settings
    github_app_id: Optional[str] = Field(default=None, description="GitHub App ID")
    github_private_key: Optional[str] = Field(default=None, description="GitHub App private key")
    github_webhook_secret: Optional[str] = Field(default=None, description="GitHub webhook secret")
    
    jira_base_url: Optional[str] = Field(default=None, description="Jira base URL")
    jira_username: Optional[str] = Field(default=None, description="Jira username")
    jira_api_token: Optional[str] = Field(default=None, description="Jira API token")
    
    slack_bot_token: Optional[str] = Field(default=None, description="Slack bot token")
    slack_signing_secret: Optional[str] = Field(default=None, description="Slack signing secret")
    
    # Monitoring and logging settings
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(default="json", description="Log format (json, text)")
    sentry_dsn: Optional[str] = Field(default=None, description="Sentry DSN for error tracking")
    
    datadog_api_key: Optional[str] = Field(default=None, description="Datadog API key")
    datadog_app_key: Optional[str] = Field(default=None, description="Datadog App key")
    
    # Rate limiting settings
    rate_limit_enabled: bool = Field(default=True, description="Enable rate limiting")
    rate_limit_requests: int = Field(default=100, description="Requests per minute")
    rate_limit_window: int = Field(default=60, description="Rate limit window in seconds")
    
    # Token usage settings
    token_tracking_enabled: bool = Field(default=True, description="Enable token usage tracking")
    token_cost_per_1k: float = Field(default=0.002, description="Cost per 1000 tokens")
    
    # Subscription tiers and token allocations
    starter_monthly_tokens: int = Field(default=100, description="Starter tier monthly tokens")
    professional_monthly_tokens: int = Field(default=220, description="Professional tier monthly tokens")
    enterprise_monthly_tokens: int = Field(default=380, description="Enterprise tier monthly tokens")
    
    # Email settings
    email_provider: str = Field(default="sendgrid", description="Email provider (sendgrid, ses, smtp)")
    sendgrid_api_key: Optional[str] = Field(default=None, description="SendGrid API key")
    from_email: str = Field(default="noreply@neurosync.ai", description="From email address")
    
    # Webhook settings
    webhook_secret: str = Field(default="", description="Webhook verification secret")
    webhook_timeout: int = Field(default=30, description="Webhook timeout in seconds")
    
    # Background task settings
    celery_broker_url: str = Field(default="redis://localhost:6379/1", description="Celery broker URL")
    celery_result_backend: str = Field(default="redis://localhost:6379/1", description="Celery result backend")
    
    # Feature flags
    enable_meeting_transcription: bool = Field(default=True, description="Enable meeting transcription")
    enable_code_analysis: bool = Field(default=True, description="Enable AI code analysis")
    enable_auto_documentation: bool = Field(default=False, description="Enable auto documentation generation")
    enable_analytics: bool = Field(default=True, description="Enable usage analytics")
    
    # Performance settings
    max_concurrent_requests: int = Field(default=100, description="Max concurrent requests")
    request_timeout: int = Field(default=300, description="Request timeout in seconds")
    embedding_batch_size: int = Field(default=50, description="Batch size for embedding generation")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        
        # Environment variable prefixes
        env_prefix = "NEUROSYNC_"
        
        # Field aliases for common environment variables
        fields = {
            "database_url": {"env": ["DATABASE_URL", "NEUROSYNC_DATABASE_URL"]},
            "openai_api_key": {"env": ["OPENAI_API_KEY", "NEUROSYNC_OPENAI_API_KEY"]},
            "secret_key": {"env": ["SECRET_KEY", "NEUROSYNC_SECRET_KEY"]},
            "redis_url": {"env": ["REDIS_URL", "NEUROSYNC_REDIS_URL"]},
            "sentry_dsn": {"env": ["SENTRY_DSN", "NEUROSYNC_SENTRY_DSN"]},
        }

    def get_database_url(self) -> str:
        """Get database URL with proper formatting"""
        return self.database_url
    
    def get_redis_url(self) -> str:
        """Get Redis URL with authentication if needed"""
        if self.redis_password:
            # Insert password into Redis URL
            if "://" in self.redis_url:
                protocol, rest = self.redis_url.split("://", 1)
                return f"{protocol}://:{self.redis_password}@{rest}"
        return self.redis_url
    
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.environment.lower() == "production"
    
    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.environment.lower() == "development"
    
    def get_cors_origins(self) -> List[str]:
        """Get CORS origins as a list"""
        if isinstance(self.cors_origins, str):
            return [origin.strip() for origin in self.cors_origins.split(",")]
        return self.cors_origins
    
    def get_log_config(self) -> dict:
        """Get logging configuration"""
        return {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                },
                "json": {
                    "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
                    "format": "%(asctime)s %(name)s %(levelname)s %(message)s"
                }
            },
            "handlers": {
                "default": {
                    "formatter": self.log_format,
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stdout",
                },
            },
            "root": {
                "level": self.log_level,
                "handlers": ["default"],
            },
            "loggers": {
                "uvicorn": {
                    "level": "INFO",
                    "handlers": ["default"],
                    "propagate": False,
                },
                "uvicorn.error": {
                    "level": "INFO",
                    "handlers": ["default"],
                    "propagate": False,
                },
                "uvicorn.access": {
                    "level": "INFO",
                    "handlers": ["default"],
                    "propagate": False,
                },
            },
        }

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()

# Environment-specific configurations
class DevelopmentSettings(Settings):
    """Development environment settings"""
    debug: bool = True
    log_level: str = "DEBUG"
    database_echo: bool = True
    reload: bool = True

class ProductionSettings(Settings):
    """Production environment settings"""
    debug: bool = False
    log_level: str = "INFO"
    database_echo: bool = False
    reload: bool = False
    workers: int = 4

class TestingSettings(Settings):
    """Testing environment settings"""
    debug: bool = True
    log_level: str = "DEBUG"
    database_url: str = "sqlite:///./test.db"
    vector_db_path: str = "./test_data/chroma"
    vector_db_reset: bool = True

def get_settings_for_environment(env: str) -> Settings:
    """Get settings for specific environment"""
    env = env.lower()
    
    if env == "development":
        return DevelopmentSettings()
    elif env == "production":
        return ProductionSettings()
    elif env == "testing":
        return TestingSettings()
    else:
        return Settings()

# Validation functions
def validate_required_settings():
    """Validate that all required settings are present"""
    settings = get_settings()
    
    required_fields = [
        "secret_key",
        "database_url", 
        "openai_api_key"
    ]
    
    missing_fields = []
    for field in required_fields:
        if not getattr(settings, field, None):
            missing_fields.append(field)
    
    if missing_fields:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_fields)}")
    
    return True
