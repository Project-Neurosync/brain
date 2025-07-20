"""
NeuroSync AI Backend - Main FastAPI Application
Agentic AI System for Developer Knowledge Transfer
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional, Dict, List, Any
import uvicorn
import asyncio
import logging
from datetime import datetime
import uuid
import os
import sys

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import our core modules
from core.ai_engine import AIEngine
from core.data_ingestion import DataIngestionEngine
from core.vector_db import VectorDatabase
from core.knowledge_graph import KnowledgeGraphBuilder
from core.token_tracker import TokenTracker, TokenType
from core.auth import AuthManager
from models.requests import *
from models.responses import *
from config.settings import get_settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="NeuroSync AI API",
    description="Agentic AI System for Developer Knowledge Transfer",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()
settings = get_settings()

# Initialize core components with proper configuration
ai_engine = AIEngine(config={"openai_api_key": settings.openai_api_key})
data_ingestion = DataIngestionEngine()
vector_db = VectorDatabase()
knowledge_graph = KnowledgeGraphBuilder()
token_tracker = TokenTracker()
auth_manager = AuthManager(config={"jwt_secret": settings.secret_key})

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Starting NeuroSync AI Backend...")
    
    # Initialize databases
    await token_tracker.initialize()
    
    logger.info("NeuroSync AI Backend started successfully!")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down NeuroSync AI Backend...")

# Authentication dependency
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Validate JWT token and return user info"""
    try:
        user = await auth_manager.validate_token(credentials.credentials)
        return user
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid authentication token")

# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="success",
        version="1.0.0",
        services={
            "ai_engine": "running",
            "vector_db": "running",
            "knowledge_graph": "running"
        }
    )

# Authentication endpoints
@app.post("/api/v1/auth/register", response_model=AuthResponse)
async def register_user(request: UserRegistrationRequest):
    """Register a new user"""
    try:
        result = await auth_manager.register_user(
            email=request.email,
            password=request.password,
            subscription_tier=request.subscription_tier,
            metadata=request.metadata
        )
        
        return AuthResponse(
            status="success",
            user_id=result["user_id"],
            email=result["email"],
            subscription_tier=result["subscription_tier"],
            access_token=result["access_token"],
            refresh_token=result["refresh_token"],
            token_type=result["token_type"]
        )
        
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/v1/auth/login", response_model=AuthResponse)
async def login_user(request: UserLoginRequest):
    """Authenticate a user"""
    try:
        result = await auth_manager.authenticate_user(
            email=request.email,
            password=request.password
        )
        
        return AuthResponse(
            status="success",
            user_id=result["user_id"],
            email=result["email"],
            subscription_tier=result["subscription_tier"],
            access_token=result["access_token"],
            refresh_token=result["refresh_token"],
            token_type=result["token_type"]
        )
        
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(status_code=401, detail=str(e))

@app.post("/api/v1/auth/refresh", response_model=RefreshTokenResponse)
async def refresh_token(request: RefreshTokenRequest):
    """Refresh access token"""
    try:
        result = await auth_manager.refresh_access_token(request.refresh_token)
        
        return RefreshTokenResponse(
            status="success",
            access_token=result["access_token"],
            token_type=result["token_type"]
        )
        
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        raise HTTPException(status_code=401, detail=str(e))

# Data ingestion endpoints
@app.post("/api/v1/ingest", response_model=IngestionResponse)
async def ingest_data(
    request: DataIngestionRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict = Depends(get_current_user)
):
    """Ingest data from various sources"""
    try:
        # Validate user has access to project
        if not await auth_manager.has_project_access(current_user["user_id"], request.project_id):
            raise HTTPException(status_code=403, detail="Access denied to project")
        
        # Generate request ID
        request_id = str(uuid.uuid4())
        
        # Start background processing
        background_tasks.add_task(
            process_data_async,
            request,
            current_user["user_id"],
            request_id
        )
        
        return IngestionResponse(
            status="processing",
            request_id=request_id,
            message="Data ingestion started successfully"
        )
        
    except Exception as e:
        logger.error(f"Data ingestion error: {str(e)}")
        raise HTTPException(status_code=500, detail="Data ingestion failed")

async def process_data_async(request: DataIngestionRequest, user_id: str, request_id: str):
    """Asynchronously process ingested data"""
    try:
        logger.info(f"Processing data for request {request_id}")
        
        # Process based on source type
        if request.source_type == SourceType.GITHUB:
            result = await data_ingestion.ingest_github_repo(request.config.repo_url)
        elif request.source_type == SourceType.JIRA:
            result = await data_ingestion.ingest_jira_project(request.config.dict())
        elif request.source_type == SourceType.SLACK:
            result = await data_ingestion.ingest_slack_channel(request.config.channel_id)
        elif request.source_type == SourceType.DOCUMENT:
            result = await data_ingestion.ingest_documents(request.config.file_paths)
        else:
            raise ValueError(f"Unsupported source type: {request.source_type}")
        
        logger.info(f"Data processing completed for request {request_id}")
        
    except Exception as e:
        logger.error(f"Data processing error for request {request_id}: {str(e)}")

# AI query endpoints
@app.post("/api/v1/query", response_model=AIQueryResponse)
async def query_ai(
    request: AIQueryRequest,
    current_user: Dict = Depends(get_current_user)
):
    """Query the AI system for knowledge"""
    try:
        # Validate project access
        if not await auth_manager.has_project_access(current_user["user_id"], request.project_id):
            raise HTTPException(status_code=403, detail="Access denied to project")
        
        # Check token quota
        quota_check = await token_tracker.check_quota(current_user["user_id"], 1000)
        if not quota_check["can_proceed"]:
            raise HTTPException(status_code=429, detail="Token quota exceeded")
        
        # Process query with AI engine
        response = await ai_engine.process_query(
            query=request.query,
            context=request.context,
            user_tier=current_user["subscription_tier"],
            stream=request.stream,
            max_tokens=request.max_tokens,
            temperature=request.temperature
        )
        
        # Track token usage
        await token_tracker.track_usage(
            user_id=current_user["user_id"],
            project_id=request.project_id,
            token_type=TokenType.INPUT,
            token_count=response["tokens_used"],
            model_name=response["model_used"]
        )
        
        return AIQueryResponse(
            status="success",
            query=request.query,
            response=response["response"],
            sources=response["sources"],
            confidence=response["confidence"],
            tokens_used=response["tokens_used"],
            cost=response["cost"],
            model_used=response["model_used"],
            processing_time=response["processing_time"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Query processing error: {str(e)}")
        raise HTTPException(status_code=500, detail="Query processing failed")

# Project management endpoints
@app.post("/api/v1/projects", response_model=ProjectResponse)
async def create_project(
    request: CreateProjectRequest,
    current_user: Dict = Depends(get_current_user)
):
    """Create a new project"""
    try:
        project_id = str(uuid.uuid4())
        
        # Grant user access to the project
        await auth_manager.grant_project_access(current_user["user_id"], project_id, "owner")
        
        return ProjectResponse(
            status="success",
            project_id=project_id,
            name=request.name,
            description=request.description,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            owner_id=current_user["user_id"],
            team_members=[],
            settings=request.settings or {},
            stats={}
        )
        
    except Exception as e:
        logger.error(f"Project creation error: {str(e)}")
        raise HTTPException(status_code=500, detail="Project creation failed")

@app.get("/api/v1/projects", response_model=ProjectListResponse)
async def list_projects(current_user: Dict = Depends(get_current_user)):
    """List user's accessible projects"""
    try:
        # Get user profile to access projects
        profile = await auth_manager.get_user_profile(current_user["user_id"])
        
        # For now, return empty list - would be populated from database
        return ProjectListResponse(
            status="success",
            projects=[],
            total=0,
            page=1,
            page_size=10
        )
        
    except Exception as e:
        logger.error(f"Project listing error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list projects")

# Token management endpoints
@app.get("/api/v1/tokens/usage", response_model=TokenUsageResponse)
async def get_token_usage(current_user: Dict = Depends(get_current_user)):
    """Get user's token usage information"""
    try:
        usage_summary = await token_tracker.get_usage_summary(current_user["user_id"])
        quota_check = await token_tracker.check_quota(current_user["user_id"], 0)
        
        return TokenUsageResponse(
            status="success",
            user_id=current_user["user_id"],
            total_tokens=usage_summary["total_tokens"],
            total_cost=usage_summary["total_cost"],
            quota_limit=quota_check["quota_limit"],
            quota_remaining=quota_check["quota_remaining"],
            breakdown=usage_summary["breakdown"],
            recent_usage=usage_summary["records"]
        )
        
    except Exception as e:
        logger.error(f"Token usage error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get token usage")

# Cost optimization endpoints
@app.post("/api/v1/optimize/analyze", response_model=OptimizationAnalysisResponse)
async def analyze_cost_optimization(
    request: OptimizationAnalysisRequest,
    current_user: Dict = Depends(get_current_user)
):
    """Analyze cost optimization opportunities"""
    try:
        user_id = request.user_id or current_user["user_id"]
        usage_summary = await token_tracker.get_usage_summary(user_id)
        suggestions = await token_tracker.get_cost_optimization_suggestions(user_id)
        
        return OptimizationAnalysisResponse(
            status="success",
            current_costs=CostBreakdown(
                input_tokens=usage_summary["breakdown"].get("input", {}).get("cost", 0.0),
                output_tokens=usage_summary["breakdown"].get("output", {}).get("cost", 0.0),
                embeddings=usage_summary["breakdown"].get("embedding", {}).get("cost", 0.0),
                searches=usage_summary["breakdown"].get("search", {}).get("cost", 0.0),
                total=usage_summary["total_cost"]
            ),
            projected_savings=usage_summary["total_cost"] * 0.3,  # 30% potential savings
            optimization_score=75.0,
            suggestions=[
                OptimizationSuggestion(
                    type=s["type"],
                    message=s["message"],
                    potential_savings=s["potential_savings"],
                    implementation_effort="Low"
                ) for s in suggestions
            ]
        )
        
    except Exception as e:
        logger.error(f"Cost optimization analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail="Cost optimization analysis failed")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
