"""
AI query routes for NeuroSync API
Handles AI query execution, history, and related operations
"""

import logging
from typing import List, Optional, Dict
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

from models.database import get_db
from models.user_models import User
from models.ai_query import AIQuery
from models.project import Project
from middleware.auth import get_current_user

# Create logger
logger = logging.getLogger(__name__)

# Create router for AI operations
router = APIRouter(prefix="/api/v1/ai", tags=["ai"])

# Define response schemas
class AIQueryResponse(BaseModel):
    id: str
    query: str
    confidence: float
    project_id: Optional[str] = None
    project_name: Optional[str] = None
    timestamp: str
    
    model_config = {"from_attributes": True}


# Endpoint to get recent AI queries for current user
@router.get("/queries/recent", response_model=List[AIQueryResponse])
async def get_recent_queries(
    limit: int = Query(5, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get recent AI queries for the current authenticated user
    """
    try:
        logger.info(f"Fetching recent AI queries for user: {current_user.email}")
        
        # Query recent AI queries for current user
        queries = db.query(AIQuery).filter(
            AIQuery.user_id == current_user.id
        ).order_by(desc(AIQuery.created_at)).limit(limit).all()
        
        # Convert to response format with project names
        result = []
        for query in queries:
            project_name = None
            if query.project_id:
                project = db.query(Project).filter(Project.id == query.project_id).first()
                project_name = project.name if project else None
                
            result.append({
                "id": str(query.id),
                "query": query.query_text,
                "confidence": 0.8,
                "project_id": str(query.project_id) if query.project_id else None,
                "project_name": project_name,
                "timestamp": query.created_at.isoformat()
            })
        
        return result
        
    except Exception as e:
        logger.error(f"Error fetching recent AI queries: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve recent AI queries: {str(e)}"
        )
