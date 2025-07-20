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

# Import our core modules
from core.ai_engine import AIEngine
from core.data_ingestion import DataIngestionEngine
from core.vector_db import VectorDatabase
from core.knowledge_graph import KnowledgeGraphBuilder
from core.token_tracker import TokenTracker
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

# Initialize core components
ai_engine = AIEngine()
data_ingestion = DataIngestionEngine()
vector_db = VectorDatabase()
knowledge_graph = KnowledgeGraphBuilder()
token_tracker = TokenTracker()
auth_manager = AuthManager()

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Starting NeuroSync AI Backend...")
    
    # Initialize databases
    await vector_db.initialize()
    await knowledge_graph.initialize()
    await token_tracker.initialize()
    
    logger.info("NeuroSync AI Backend started successfully!")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down NeuroSync AI Backend...")
    await vector_db.close()
    await knowledge_graph.close()

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
        status="healthy",
        timestamp=datetime.utcnow(),
        version="1.0.0",
        services={
            "ai_engine": "running",
            "vector_db": "running",
            "knowledge_graph": "running"
        }
    )

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
        
        # Step 1: Validate and clean data
        cleaned_data = await data_ingestion.clean_data(request.data, request.source_type)
        
        # Step 2: Extract entities and relationships
        entities = await data_ingestion.extract_entities(cleaned_data)
        
        # Step 3: Generate embeddings
        embeddings = await ai_engine.generate_embeddings(entities, request.project_id)
        
        # Step 4: Update vector database
        await vector_db.add_documents(
            project_id=request.project_id,
            documents=entities,
            embeddings=embeddings,
            metadata={"source": request.source_type, "user_id": user_id}
        )
        
        # Step 5: Update knowledge graph
        await knowledge_graph.update_graph(entities, request.project_id)
        
        # Step 6: Update processing status
        await update_processing_status(request_id, "completed")
        
        logger.info(f"Data processing completed for request {request_id}")
        
    except Exception as e:
        logger.error(f"Data processing error for request {request_id}: {str(e)}")
        await update_processing_status(request_id, "failed", str(e))

# AI query endpoints
@app.post("/api/v1/query", response_model=QueryResponse)
async def query_ai(
    request: QueryRequest,
    current_user: Dict = Depends(get_current_user)
):
    """Query the AI system for knowledge"""
    try:
        # Validate project access
        if not await auth_manager.has_project_access(current_user["user_id"], request.project_id):
            raise HTTPException(status_code=403, detail="Access denied to project")
        
        # Check token limits
        user_tokens = await token_tracker.get_user_tokens(current_user["user_id"])
        if user_tokens <= 0:
            raise HTTPException(status_code=429, detail="Token limit exceeded")
        
        # Generate AI response
        response = await ai_engine.generate_response(
            query=request.query,
            project_id=request.project_id,
            context=request.context,
            user_id=current_user["user_id"]
        )
        
        # Track token usage
        await token_tracker.consume_token(current_user["user_id"], request.project_id)
        
        return QueryResponse(
            response=response["answer"],
            sources=response["sources"],
            confidence=response["confidence"],
            tokens_used=1,
            tokens_remaining=user_tokens - 1
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
        # Create project in database
        project = await auth_manager.create_project(
            name=request.name,
            description=request.description,
            owner_id=current_user["user_id"],
            settings=request.settings
        )
        
        # Initialize project-specific vector collection
        await vector_db.create_project_collection(project["project_id"])
        
        # Initialize project knowledge graph
        await knowledge_graph.create_project_graph(project["project_id"])
        
        return ProjectResponse(
            project_id=project["project_id"],
            name=project["name"],
            status="created",
            message="Project created successfully"
        )
        
    except Exception as e:
        logger.error(f"Project creation error: {str(e)}")
        raise HTTPException(status_code=500, detail="Project creation failed")

@app.get("/api/v1/projects", response_model=List[ProjectInfo])
async def list_projects(current_user: Dict = Depends(get_current_user)):
    """List user's accessible projects"""
    try:
        projects = await auth_manager.get_user_projects(current_user["user_id"])
        return [
            ProjectInfo(
                project_id=p["project_id"],
                name=p["name"],
                description=p["description"],
                role=p["role"],
                created_at=p["created_at"],
                updated_at=p["updated_at"]
            )
            for p in projects
        ]
    except Exception as e:
        logger.error(f"Project listing error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list projects")

# Token management endpoints
@app.get("/api/v1/tokens", response_model=TokenInfo)
async def get_token_info(current_user: Dict = Depends(get_current_user)):
    """Get user's token information"""
    try:
        token_info = await token_tracker.get_token_info(current_user["user_id"])
        return TokenInfo(
            user_id=current_user["user_id"],
            tokens_remaining=token_info["remaining"],
            tokens_used_today=token_info["used_today"],
            tokens_used_month=token_info["used_month"],
            subscription_tier=token_info["tier"],
            next_refill=token_info["next_refill"]
        )
    except Exception as e:
        logger.error(f"Token info error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get token information")

# Analytics endpoints
@app.get("/api/v1/analytics/usage", response_model=UsageAnalytics)
async def get_usage_analytics(
    project_id: Optional[str] = None,
    current_user: Dict = Depends(get_current_user)
):
    """Get usage analytics for user or project"""
    try:
        if project_id:
            # Validate project access
            if not await auth_manager.has_project_access(current_user["user_id"], project_id):
                raise HTTPException(status_code=403, detail="Access denied to project")
            
            analytics = await token_tracker.get_project_analytics(project_id)
        else:
            analytics = await token_tracker.get_user_analytics(current_user["user_id"])
        
        return UsageAnalytics(**analytics)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analytics error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get analytics")

# Cost Optimization endpoints
from services.optimization_service import optimization_service

@app.post("/api/v1/optimization/analyze")
async def analyze_query_complexity(
    request: dict,
    current_user: Dict = Depends(get_current_user)
):
    """Analyze query complexity for optimal model selection"""
    try:
        query = request.get("query", "")
        context = request.get("context", "")
        
        if not query:
            raise HTTPException(status_code=400, detail="Query is required")
        
        complexity = optimization_service.analyze_query_complexity(query, context)
        user_tier = current_user.get("subscription_tier", "starter")
        recommended_model = optimization_service.select_optimal_model(complexity, user_tier)
        
        return {
            "query": query,
            "complexity": complexity.value,
            "recommended_model": recommended_model,
            "analysis_timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Query analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to analyze query")

@app.get("/api/v1/optimization/report")
async def get_optimization_report(
    current_user: Dict = Depends(get_current_user)
):
    """Get comprehensive optimization metrics and cost savings report"""
    try:
        metrics = optimization_service.get_optimization_report()
        
        return {
            "total_queries": metrics.total_queries,
            "total_cost_saved": round(metrics.total_cost_saved, 4),
            "savings_percentage": round(metrics.savings_percentage, 2),
            "average_response_time": round(metrics.average_response_time, 3),
            "cache_hit_rate": round(metrics.cache_hit_rate, 2),
            "model_distribution": metrics.model_distribution,
            "report_timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Optimization report error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate optimization report")

@app.get("/api/v1/optimization/models")
async def get_model_recommendations(
    current_user: Dict = Depends(get_current_user)
):
    """Get AI model recommendations based on user tier"""
    try:
        user_tier = current_user.get("subscription_tier", "starter")
        recommendations = optimization_service.get_model_recommendations(user_tier)
        
        return {
            "user_tier": user_tier,
            "models": recommendations,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Model recommendations error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get model recommendations")

@app.post("/api/v1/optimization/process")
async def process_optimized_query(
    request: dict,
    current_user: Dict = Depends(get_current_user)
):
    """Process a query with cost optimization"""
    try:
        query = request.get("query", "")
        context = request.get("context", "")
        
        if not query:
            raise HTTPException(status_code=400, detail="Query is required")
        
        user_tier = current_user.get("subscription_tier", "starter")
        result = optimization_service.process_optimized_query(query, context, user_tier)
        
        return {
            "query": query,
            "optimization_result": result,
            "user_tier": user_tier,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Optimized query processing error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process optimized query")

@app.delete("/api/v1/optimization/cache")
async def clear_optimization_cache(
    current_user: Dict = Depends(get_current_user)
):
    """Clear the optimization query cache"""
    try:
        result = optimization_service.clear_cache()
        return result
        
    except Exception as e:
        logger.error(f"Cache clear error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to clear cache")

@app.get("/api/v1/optimization/stats")
async def get_optimization_stats(
    current_user: Dict = Depends(get_current_user)
):
    """Get general optimization statistics"""
    try:
        metrics = optimization_service.get_optimization_report()
        
        return {
            "total_queries_processed": metrics.total_queries,
            "total_cost_savings": round(metrics.total_cost_saved, 4),
            "average_savings_per_query": round(metrics.total_cost_saved / max(metrics.total_queries, 1), 4),
            "cache_efficiency": round(metrics.cache_hit_rate, 2),
            "most_used_model": max(metrics.model_distribution.items(), key=lambda x: x[1])[0] if metrics.model_distribution else "none",
            "optimization_active": True,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Optimization stats error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get optimization stats")

# Utility functions
async def update_processing_status(request_id: str, status: str, error: Optional[str] = None):
    """Update processing status in database"""
    # Implementation would update status in database
    pass

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
