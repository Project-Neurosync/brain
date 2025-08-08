"""
Main FastAPI application for NeuroSync API
Initializes app, routers, and middleware
"""

import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.exceptions import RequestValidationError, ResponseValidationError
from fastapi.responses import JSONResponse
import json

# Import routers
from routes.auth import router as auth_router
from routes.marketing import router as marketing_router
from routes.stats import router as stats_router
from routes.users import router as users_router
from routes.projects import router as projects_router
from routes.integrations import router as integrations_router
from routes.ai import router as ai_router
from routes.chat import router as chat_router
from routes.files import router as files_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="NeuroSync API",
    description="Backend API for NeuroSync - AI-powered code intelligence platform",
    version="1.0.0",
)

# Add custom exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Log detailed request validation errors"""
    error_detail = exc.errors()
    logger.error(f"Request validation error: {error_detail}")
    return JSONResponse(
        status_code=422,
        content={"detail": error_detail}
    )

@app.exception_handler(ResponseValidationError)
async def response_validation_exception_handler(request: Request, exc: ResponseValidationError):
    """Log detailed response validation errors"""
    error_msg = str(exc)
    logger.error(f"Response validation error: {error_msg}")
    # Log the request details for debugging
    body = await request.body()
    logger.debug(f"Request body: {body.decode()}")
    logger.debug(f"Request URL: {request.url}")
    logger.debug(f"Request method: {request.method}")
    return JSONResponse(
        status_code=422,
        content={"detail": f"Response validation error: {error_msg}"}
    )

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add GZip compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Include routers
app.include_router(auth_router)
app.include_router(marketing_router)
app.include_router(stats_router)
app.include_router(users_router)
app.include_router(projects_router)
app.include_router(integrations_router)
app.include_router(ai_router)
app.include_router(chat_router)
app.include_router(files_router)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {"status": "healthy", "version": "1.0.0"}

# Root endpoint
@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "message": "Welcome to NeuroSync API",
        "documentation": "/docs",
        "health": "/health",
    }

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting NeuroSync API server")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
