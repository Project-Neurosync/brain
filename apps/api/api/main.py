"""
NeuroSync AI Backend - Main FastAPI Application
Core API routes and application setup
"""

import logging
from contextlib import asynccontextmanager
from typing import Annotated, List, Optional
from fastapi import FastAPI, Depends, HTTPException, status, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import json

from ..config.settings import get_settings, validate_required_settings
from ..database.connection import get_database, init_database, check_database_health
from ..services.ai_service import AIService
from ..services.vector_service import VectorService
from ..services.ingestion_service import DataIngestionService
from ..services.auth_service import AuthService
from ..middleware.auth import (
    get_current_verified_user, require_project_read, require_project_write,
    require_query_tokens, require_ingestion_tokens, log_api_usage
)
from ..models.database import User, Project, Query, UsageLog
from ..models.requests import (
    QueryRequest, DataIngestionRequest, CreateProjectRequest, 
    UpdateProjectRequest, SearchRequest, DocumentUploadRequest
)
from ..models.responses import (
    QueryResponse, StreamingQueryResponse, DataIngestionResponse,
    ProjectResponse, ProjectListResponse, SearchResponse, 
    DocumentResponse, HealthResponse, ErrorResponse
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize settings
settings = get_settings()

# Initialize services
ai_service = AIService()
vector_service = VectorService()
ingestion_service = DataIngestionService(vector_service, ai_service)
auth_service = AuthService()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting NeuroSync AI Backend...")
    
    try:
        # Validate required settings
        validate_required_settings()
        
        # Initialize database
        init_database()
        
        logger.info("NeuroSync AI Backend started successfully")
        yield
        
    except Exception as e:
        logger.error(f"Failed to start application: {str(e)}")
        raise
    
    # Shutdown
    logger.info("Shutting down NeuroSync AI Backend...")

# Create FastAPI app
app = FastAPI(
    title="NeuroSync AI Backend",
    description="AI-powered developer knowledge transfer and project understanding platform",
    version="1.0.0",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if settings.is_production():
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["neurosync.ai", "*.neurosync.ai", "localhost"]
    )

# Health check endpoint
@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Check application health status"""
    try:
        # Check database health
        db_health = await check_database_health()
        
        # Check vector store health
        vector_health = "healthy"  # Add actual vector store health check
        
        # Check AI service health
        ai_health = "healthy"  # Add actual AI service health check
        
        services = {
            **db_health,
            "vector_store": vector_health,
            "ai_service": ai_health,
            "cache": "healthy"  # Add Redis health check when implemented
        }
        
        overall_status = "healthy" if all(
            status == "healthy" for status in services.values()
        ) else "degraded"
        
        return HealthResponse(
            status=overall_status,
            version=settings.app_version,
            services=services
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return HealthResponse(
            status="unhealthy",
            version=settings.app_version,
            services={"error": str(e)}
        )

# AI Query endpoints
@app.post("/api/v1/query", response_model=QueryResponse, tags=["AI"])
async def process_query(
    request: QueryRequest,
    current_user: Annotated[User, Depends(require_query_tokens)],
    db: Annotated[Session, Depends(get_database)],
    background_tasks: BackgroundTasks,
    _: Annotated[bool, Depends(log_api_usage)]
):
    """Process an AI query with context from project knowledge"""
    try:
        # Get relevant context documents
        context_documents = await vector_service.search_documents(
            request.project_id,
            request.query,
            limit=10
        )
        
        # Process query with AI service
        response = await ai_service.process_query(request, context_documents)
        
        # Deduct tokens from user balance
        if response.success and response.tokens_used > 0:
            current_user.use_tokens(response.tokens_used)
            db.commit()
            
            # Log usage for analytics
            background_tasks.add_task(
                log_token_usage,
                current_user.id,
                request.project_id,
                "ai_query",
                response.tokens_used,
                db
            )
        
        # Save query to database
        query_record = Query(
            query_text=request.query,
            response_text=response.answer,
            context=request.context,
            sources_used=[doc.get("id") for doc in context_documents],
            model_used=settings.ai_model,
            tokens_used=response.tokens_used,
            confidence_score=response.confidence,
            response_time_ms=int(response.response_time * 1000),
            user_id=current_user.id,
            project_id=request.project_id,
            status="completed" if response.success else "failed"
        )
        db.add(query_record)
        db.commit()
        
        return response
        
    except Exception as e:
        logger.error(f"Query processing failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query processing failed: {str(e)}"
        )

@app.post("/api/v1/query/stream", tags=["AI"])
async def stream_query(
    request: QueryRequest,
    current_user: Annotated[User, Depends(require_query_tokens)],
    db: Annotated[Session, Depends(get_database)],
    _: Annotated[bool, Depends(log_api_usage)]
):
    """Stream an AI query response"""
    try:
        # Get relevant context documents
        context_documents = await vector_service.search_documents(
            request.project_id,
            request.query,
            limit=10
        )
        
        async def generate_stream():
            total_tokens = 0
            response_chunks = []
            
            async for chunk in ai_service.stream_query(request, context_documents):
                chunk_data = chunk.dict()
                response_chunks.append(chunk_data["chunk"])
                
                if chunk.is_final and chunk.tokens_used:
                    total_tokens = chunk.tokens_used
                    
                    # Deduct tokens from user balance
                    current_user.use_tokens(total_tokens)
                    db.commit()
                
                yield f"data: {json.dumps(chunk_data)}\n\n"
            
            # Save query to database
            query_record = Query(
                query_text=request.query,
                response_text="".join(response_chunks),
                context=request.context,
                sources_used=[doc.get("id") for doc in context_documents],
                model_used=settings.ai_model,
                tokens_used=total_tokens,
                user_id=current_user.id,
                project_id=request.project_id,
                status="completed"
            )
            db.add(query_record)
            db.commit()
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/plain",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
        )
        
    except Exception as e:
        logger.error(f"Streaming query failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Streaming query failed: {str(e)}"
        )

# Data ingestion endpoints
@app.post("/api/v1/ingest", response_model=DataIngestionResponse, tags=["Data"])
async def ingest_data(
    request: DataIngestionRequest,
    current_user: Annotated[User, Depends(require_ingestion_tokens)],
    db: Annotated[Session, Depends(get_database)],
    background_tasks: BackgroundTasks,
    _: Annotated[bool, Depends(log_api_usage)]
):
    """Ingest data from various sources into the knowledge base"""
    try:
        # Check project access
        project = db.query(Project).filter(Project.id == request.project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Process ingestion
        response = await ingestion_service.process_ingestion(request)
        
        # Update project stats
        if response.success:
            project.document_count += response.items_processed
            project.last_sync_at = response.timestamp
            db.commit()
            
            # Log usage
            background_tasks.add_task(
                log_token_usage,
                current_user.id,
                request.project_id,
                "data_ingestion",
                5,  # Estimated tokens for ingestion
                db
            )
        
        return response
        
    except Exception as e:
        logger.error(f"Data ingestion failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Data ingestion failed: {str(e)}"
        )

# Project management endpoints
@app.post("/api/v1/projects", response_model=ProjectResponse, tags=["Projects"])
async def create_project(
    request: CreateProjectRequest,
    current_user: Annotated[User, Depends(get_current_verified_user)],
    db: Annotated[Session, Depends(get_database)],
    _: Annotated[bool, Depends(log_api_usage)]
):
    """Create a new project"""
    try:
        # Check subscription limits
        user_limits = auth_service.get_user_subscription_limits(current_user)
        current_project_count = db.query(Project).filter(
            Project.owner_id == current_user.id,
            Project.is_active == True
        ).count()
        
        if not auth_service.check_subscription_limit(
            current_user, "max_projects", current_project_count
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Project limit reached for {current_user.subscription_tier} tier"
            )
        
        # Create project
        project = Project(
            name=request.name,
            description=request.description,
            settings=request.settings,
            owner_id=current_user.id,
            max_members=user_limits.get("max_members_per_project", 5)
        )
        
        db.add(project)
        db.commit()
        db.refresh(project)
        
        return ProjectResponse(
            success=True,
            message="Project created successfully",
            project={
                "id": str(project.id),
                "name": project.name,
                "description": project.description,
                "created_at": project.created_at.isoformat(),
                "owner_id": str(project.owner_id),
                "settings": project.settings,
                "document_count": project.document_count,
                "is_active": project.is_active
            }
        )
        
    except Exception as e:
        logger.error(f"Project creation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Project creation failed: {str(e)}"
        )

@app.get("/api/v1/projects", response_model=ProjectListResponse, tags=["Projects"])
async def list_projects(
    current_user: Annotated[User, Depends(get_current_verified_user)],
    db: Annotated[Session, Depends(get_database)],
    _: Annotated[bool, Depends(log_api_usage)],
    page: int = 1,
    page_size: int = 10
):
    """List user's projects"""
    try:
        # Get projects where user is owner or member
        offset = (page - 1) * page_size
        
        projects_query = db.query(Project).filter(
            Project.owner_id == current_user.id,
            Project.is_active == True
        ).offset(offset).limit(page_size)
        
        projects = projects_query.all()
        total_count = db.query(Project).filter(
            Project.owner_id == current_user.id,
            Project.is_active == True
        ).count()
        
        project_list = []
        for project in projects:
            project_list.append({
                "id": str(project.id),
                "name": project.name,
                "description": project.description,
                "created_at": project.created_at.isoformat(),
                "document_count": project.document_count,
                "last_sync_at": project.last_sync_at.isoformat() if project.last_sync_at else None
            })
        
        return ProjectListResponse(
            success=True,
            message="Projects retrieved successfully",
            projects=project_list,
            total_count=total_count,
            page=page,
            page_size=page_size
        )
        
    except Exception as e:
        logger.error(f"Project listing failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Project listing failed: {str(e)}"
        )

# Search endpoints
@app.post("/api/v1/search", response_model=SearchResponse, tags=["Search"])
async def search_documents(
    request: SearchRequest,
    current_user: Annotated[User, Depends(get_current_verified_user)],
    db: Annotated[Session, Depends(get_database)],
    _: Annotated[bool, Depends(log_api_usage)]
):
    """Search documents using semantic similarity"""
    try:
        project_id = request.project_id
        if not project_id:
            raise HTTPException(status_code=400, detail="Project ID is required")
        
        # Search documents
        results = await vector_service.search_documents(
            project_id,
            request.query,
            limit=request.limit,
            filters=request.filters
        )
        
        return SearchResponse(
            success=True,
            message="Search completed successfully",
            results=results,
            total_count=len(results),
            query_time=0.5  # This would be actual query time
        )
        
    except Exception as e:
        logger.error(f"Search failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )

# Utility functions
async def log_token_usage(
    user_id: str,
    project_id: str,
    feature: str,
    tokens_used: int,
    db: Session
):
    """Background task to log token usage"""
    try:
        usage_log = UsageLog(
            user_id=user_id,
            project_id=project_id,
            feature=feature,
            tokens_used=tokens_used,
            operation_type="api_call"
        )
        db.add(usage_log)
        db.commit()
    except Exception as e:
        logger.error(f"Failed to log token usage: {str(e)}")

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    return ErrorResponse(
        success=False,
        message=exc.detail,
        error_code=f"HTTP_{exc.status_code}",
        details={"status_code": exc.status_code}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {str(exc)}")
    return ErrorResponse(
        success=False,
        message="Internal server error",
        error_code="INTERNAL_ERROR",
        details={"error": str(exc)} if settings.debug else {}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.api.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        workers=settings.workers if not settings.reload else 1
    )
