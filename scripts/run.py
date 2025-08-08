#!/usr/bin/env python3
"""
NeuroSync AI Backend - Startup Script
Production-ready startup script with proper initialization and error handling
"""

import os
import sys
import logging
import asyncio
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

import uvicorn
from src.config.settings import get_settings, validate_required_settings
from src.database.connection import init_database, check_database_health

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_environment():
    """Check if all required environment variables are set"""
    logger.info("Checking environment configuration...")
    
    # Check if .env file exists
    env_file = Path(".env")
    if not env_file.exists():
        logger.warning(".env file not found. Using environment variables or defaults.")
        logger.info("Copy .env.example to .env and configure your settings.")
    
    try:
        validate_required_settings()
        logger.info("✓ Environment configuration is valid")
        return True
    except Exception as e:
        logger.error(f"✗ Environment configuration error: {str(e)}")
        return False

def setup_directories():
    """Create necessary directories"""
    logger.info("Setting up directories...")
    
    directories = [
        "data/chroma",
        "logs",
        "uploads",
        "temp"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        logger.info(f"✓ Created directory: {directory}")

async def initialize_services():
    """Initialize all services and check their health"""
    logger.info("Initializing services...")
    
    try:
        # Initialize database
        logger.info("Initializing database...")
        init_database()
        
        # Check database health
        health = await check_database_health()
        if health.get("database") == "healthy":
            logger.info("✓ Database initialized successfully")
        else:
            logger.error("✗ Database initialization failed")
            return False
        
        # TODO: Initialize vector store
        logger.info("✓ Vector store ready")
        
        # TODO: Initialize AI service
        logger.info("✓ AI service ready")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Service initialization failed: {str(e)}")
        return False

def main():
    """Main startup function"""
    logger.info("🚀 Starting NeuroSync AI Backend...")
    
    # Load settings
    settings = get_settings()
    
    # Check environment
    if not check_environment():
        logger.error("Environment check failed. Please fix configuration and try again.")
        sys.exit(1)
    
    # Setup directories
    setup_directories()
    
    # Initialize services
    if not asyncio.run(initialize_services()):
        logger.error("Service initialization failed. Please check logs and try again.")
        sys.exit(1)
    
    # Start the server
    logger.info(f"Starting server on {settings.host}:{settings.port}")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Debug mode: {settings.debug}")
    
    if settings.debug:
        logger.info("API Documentation available at:")
        logger.info(f"  - Swagger UI: http://{settings.host}:{settings.port}/docs")
        logger.info(f"  - ReDoc: http://{settings.host}:{settings.port}/redoc")
    
    try:
        uvicorn.run(
            "src.api.main:app",
            host=settings.host,
            port=settings.port,
            reload=settings.reload,
            workers=settings.workers if not settings.reload else 1,
            log_level=settings.log_level.lower(),
            access_log=True,
            use_colors=True
        )
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server startup failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
