"""
Application settings for NeuroSync API
Handles environment variable loading and validation
"""

import os
from typing import List, Union, Optional
from pydantic import BaseModel, Field, AnyHttpUrl, PostgresDsn, validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    """Application settings"""
    
    # Application settings
    APP_NAME: str = "NeuroSync"
    APP_ENVIRONMENT: str = "development"
    DEBUG: bool = True
    PORT: int = 8000
    HOST: str = "0.0.0.0"
    
    # Database settings
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql://postgres.lahkhtewrqlqcfhpytqo:[YOUR-PASSWORD]@aws-0-ap-south-1.pooler.supabase.com:5432/postgres"
    )
    
    # Authentication settings
    JWT_SECRET: str = Field(default="temporary_secret_key_replace_in_production", min_length=32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS settings
    CORS_ORIGINS: str = "http://localhost:3000,https://neurosync.ai"
    
    # Rate limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_MAX_REQUESTS: int = 100
    RATE_LIMIT_TIMEFRAME: int = 60  # in seconds
    
    # Email settings
    EMAIL_ENABLED: bool = False
    EMAIL_HOST: str = "smtp.example.com"
    EMAIL_PORT: int = 587
    EMAIL_USERNAME: str = "your_email@example.com"
    EMAIL_PASSWORD: str = "your_email_password"
    EMAIL_FROM: str = "noreply@neurosync.ai"
    EMAIL_SSL: bool = False
    EMAIL_TLS: bool = True
    
    # Payment gateway
    RAZORPAY_KEY_ID: str = "rzp_test_your_key_id"
    RAZORPAY_KEY_SECRET: str = "your_secret_key"
    PAYMENT_WEBHOOK_SECRET: str = "your_webhook_secret"
    
    # Admin settings
    ADMIN_EMAIL: str = "admin@neurosync.ai"
    ADMIN_PASSWORD: str = "change_this_in_production"
    
    # AI Integration
    OPENAI_API_KEY: Optional[str] = None
    
    # Groq AI Integration
    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL: str = "llama3-8b-8192"
    
    # GitHub OAuth Integration
    GITHUB_CLIENT_ID: Optional[str] = None
    GITHUB_CLIENT_SECRET: Optional[str] = None
    GITHUB_REDIRECT_URI: Optional[str] = None
    
    # Helper properties and methods
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS_ORIGINS string into list"""
        return self.CORS_ORIGINS.split(",")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

# Create global settings object
settings = Settings()

# Export as instance for importing in other modules
def get_settings() -> Settings:
    """Get application settings"""
    return settings
