"""
Stats API routes for NeuroSync
Provides endpoints for dashboard statistics and analytics
"""

import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from models.database import get_db
from models.user_models import User
from models.project import Project
from models.document import Document
from models.ai_query import AIQuery
from middleware.auth import get_current_user

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/stats",
    tags=["stats"],
)

@router.get("/dashboard")
async def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get dashboard statistics for the current user
    Returns counts of projects, AI queries, team members, and documents
    """
    logger.info(f"Fetching dashboard stats for user: {current_user.email}")
    
    try:
        # Get total projects count and change
        total_projects = db.query(func.count(Project.id)).filter(
            Project.user_id == current_user.id
        ).scalar() or 0
        
        # Get AI queries count and change (last 24h)
        ai_queries = db.query(func.count(AIQuery.id)).filter(
            AIQuery.user_id == current_user.id
        ).scalar() or 0
        
        # For team members, we'd need a proper team/organization model
        # For now, return 1 (just the current user)
        team_members = 1
        
        # Get documents count
        documents_synced = db.query(func.count(Document.id)).filter(
            Document.user_id == current_user.id
        ).scalar() or 0
        
        # Return formatted stats
        return {
            "totalProjects": total_projects,
            "projectsChange": 0,  # Placeholder for change calculation
            "aiQueries": ai_queries,
            "queriesChange": 0,   # Placeholder for change calculation
            "teamMembers": team_members,
            "membersChange": 0,   # Placeholder for change calculation
            "documentsSynced": documents_synced,
            "documentsChange": 0  # Placeholder for change calculation
        }
    except Exception as e:
        logger.error(f"Error fetching dashboard stats: {str(e)}")
        # Return zeros instead of error to avoid breaking dashboard
        return {
            "totalProjects": 0,
            "projectsChange": 0,
            "aiQueries": 0,
            "queriesChange": 0,
            "teamMembers": 0,
            "membersChange": 0,
            "documentsSynced": 0,
            "documentsChange": 0
        }

@router.get("/recent-activity")
async def get_recent_activity(
    limit: int = 5,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get recent user activity for the dashboard"""
    logger.info(f"Fetching recent activity for user: {current_user.email}")
    
    try:
        # Get recent AI queries
        recent_queries = db.query(AIQuery).filter(
            AIQuery.user_id == current_user.id
        ).order_by(desc(AIQuery.created_at)).limit(limit).all()
        
        # Format and return the results
        return [
            {
                "id": str(query.id),
                "query": query.query_text,
                "timestamp": query.created_at.isoformat(),
                "project_id": str(query.project_id) if query.project_id else None,
                "status": query.status
            }
            for query in recent_queries
        ]
    except Exception as e:
        logger.error(f"Error fetching recent activity: {str(e)}")
        return []
