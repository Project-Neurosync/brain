"""
ML Data Intelligence API Routes for NeuroSync
Exposes data importance scoring, timeline storage, and duplicate detection features
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime

from core.data_importance_scoring import AdvancedDataImportanceScoring, DataType, ImportanceLevel, TimelineCategory
from core.timeline_storage import TimelineBasedStorage, StorageTier, RetentionPolicy
from models.requests import *
from models.responses import *
from core.auth import AuthManager

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/api/v1/ml-intelligence", tags=["ML Intelligence"])

# Initialize services
importance_scorer = AdvancedDataImportanceScoring()
timeline_storage = TimelineBasedStorage()
auth_manager = AuthManager()

# Authentication dependency
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())):
    """Validate JWT token and return user info"""
    try:
        user = await auth_manager.verify_token(credentials.credentials)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(status_code=401, detail="Authentication failed")

@router.post("/score-data-importance")
async def score_data_importance(
    request: Dict[str, Any],
    current_user: Dict = Depends(get_current_user)
):
    """
    Score the importance of data items using ML-based analysis
    
    Request format:
    {
        "project_id": "string",
        "data_items": [
            {
                "id": "string",
                "type": "code|meeting|issue|document|comment|commit|slack_message|email|confluence_page|decision",
                "content": "string",
                "metadata": {...},
                "created_at": "ISO datetime",
                "author": "string"
            }
        ]
    }
    """
    try:
        project_id = request.get("project_id")
        data_items = request.get("data_items", [])
        
        if not project_id or not data_items:
            raise HTTPException(status_code=400, detail="project_id and data_items are required")
        
        # Score data items in batch
        scores = await importance_scorer.score_batch(project_id, data_items)
        
        # Convert scores to response format
        scored_items = []
        for score in scores:
            scored_items.append({
                "data_id": score.data_id,
                "data_type": score.data_type.value,
                "overall_score": score.overall_score,
                "importance_level": score.importance_level.value,
                "timeline_category": score.timeline_category.value,
                "scoring_factors": score.scoring_factors,
                "confidence": score.confidence,
                "reasoning": score.reasoning,
                "metadata": score.metadata,
                "scored_at": score.scored_at.isoformat()
            })
        
        return {
            "success": True,
            "project_id": project_id,
            "scored_items": scored_items,
            "total_items": len(scored_items),
            "summary": {
                "critical": len([s for s in scores if s.importance_level == ImportanceLevel.CRITICAL]),
                "high": len([s for s in scores if s.importance_level == ImportanceLevel.HIGH]),
                "medium": len([s for s in scores if s.importance_level == ImportanceLevel.MEDIUM]),
                "low": len([s for s in scores if s.importance_level == ImportanceLevel.LOW]),
                "noise": len([s for s in scores if s.importance_level == ImportanceLevel.NOISE])
            }
        }
        
    except Exception as e:
        logger.error(f"Error scoring data importance: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to score data importance: {str(e)}")

@router.post("/detect-duplicates")
async def detect_duplicates(
    request: Dict[str, Any],
    current_user: Dict = Depends(get_current_user)
):
    """
    Detect duplicate or near-duplicate content in data items
    """
    try:
        project_id = request.get("project_id")
        data_items = request.get("data_items", [])
        
        if not project_id or not data_items:
            raise HTTPException(status_code=400, detail="project_id and data_items are required")
        
        # Detect duplicates
        duplicates = await importance_scorer.detect_duplicates(project_id, data_items)
        
        return {
            "success": True,
            "project_id": project_id,
            "duplicate_groups": duplicates,
            "total_duplicates": sum(len(group) for group in duplicates.values()),
            "unique_items": len(data_items) - sum(len(group) - 1 for group in duplicates.values())
        }
        
    except Exception as e:
        logger.error(f"Error detecting duplicates: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to detect duplicates: {str(e)}")

@router.post("/store-timeline-data")
async def store_timeline_data(
    request: Dict[str, Any],
    background_tasks: BackgroundTasks,
    current_user: Dict = Depends(get_current_user)
):
    """
    Store data items in timeline-based storage with intelligent organization
    """
    try:
        project_id = request.get("project_id")
        data_items = request.get("data_items", [])
        
        if not project_id or not data_items:
            raise HTTPException(status_code=400, detail="project_id and data_items are required")
        
        # Store data in timeline storage (async background task)
        background_tasks.add_task(
            timeline_storage.store_timeline_data,
            project_id,
            data_items
        )
        
        return {
            "success": True,
            "message": f"Storing {len(data_items)} items in timeline storage",
            "project_id": project_id,
            "items_count": len(data_items)
        }
        
    except Exception as e:
        logger.error(f"Error storing timeline data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to store timeline data: {str(e)}")

@router.get("/timeline-data/{project_id}")
async def get_timeline_data(
    project_id: str,
    timeline_category: Optional[str] = None,
    importance_threshold: float = 0.0,
    limit: int = 100,
    include_archived: bool = False,
    current_user: Dict = Depends(get_current_user)
):
    """
    Retrieve timeline data with filtering options
    """
    try:
        # Convert string to enum if provided
        category_filter = None
        if timeline_category:
            try:
                category_filter = TimelineCategory(timeline_category)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid timeline_category: {timeline_category}")
        
        # Retrieve timeline data
        timeline_data = await timeline_storage.retrieve_timeline_data(
            project_id=project_id,
            timeline_category=category_filter,
            importance_threshold=importance_threshold,
            limit=limit,
            include_archived=include_archived
        )
        
        # Convert to response format
        formatted_data = []
        for entry in timeline_data:
            formatted_data.append({
                "entry_id": entry.entry_id,
                "project_id": entry.project_id,
                "data_type": entry.data_type,
                "importance_score": entry.importance_score,
                "importance_level": entry.importance_level.value,
                "timeline_category": entry.timeline_category.value,
                "storage_tier": entry.storage_tier.value,
                "retention_policy": entry.retention_policy.value,
                "created_at": entry.created_at.isoformat(),
                "last_accessed": entry.last_accessed.isoformat() if entry.last_accessed else None,
                "access_count": entry.access_count,
                "tags": entry.tags,
                "relationships": entry.relationships,
                "metadata": entry.metadata
            })
        
        return {
            "success": True,
            "project_id": project_id,
            "timeline_data": formatted_data,
            "total_items": len(formatted_data),
            "filters_applied": {
                "timeline_category": timeline_category,
                "importance_threshold": importance_threshold,
                "include_archived": include_archived
            }
        }
        
    except Exception as e:
        logger.error(f"Error retrieving timeline data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve timeline data: {str(e)}")

@router.get("/timeline-analytics/{project_id}")
async def get_timeline_analytics(
    project_id: str,
    days_back: int = 90,
    current_user: Dict = Depends(get_current_user)
):
    """
    Get analytics on timeline data distribution and patterns
    """
    try:
        analytics = await timeline_storage.get_timeline_analytics(project_id, days_back)
        
        return {
            "success": True,
            "project_id": project_id,
            "analytics_period_days": days_back,
            "analytics": analytics
        }
        
    except Exception as e:
        logger.error(f"Error getting timeline analytics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get timeline analytics: {str(e)}")

@router.post("/learn-from-feedback")
async def learn_from_feedback(
    request: Dict[str, Any],
    current_user: Dict = Depends(get_current_user)
):
    """
    Provide feedback on importance scoring to improve ML model accuracy
    
    Request format:
    {
        "project_id": "string",
        "data_id": "string",
        "feedback_score": 0.0-1.0,
        "user_feedback": "optional text feedback"
    }
    """
    try:
        project_id = request.get("project_id")
        data_id = request.get("data_id")
        feedback_score = request.get("feedback_score")
        
        if not all([project_id, data_id, feedback_score is not None]):
            raise HTTPException(status_code=400, detail="project_id, data_id, and feedback_score are required")
        
        if not 0.0 <= feedback_score <= 1.0:
            raise HTTPException(status_code=400, detail="feedback_score must be between 0.0 and 1.0")
        
        # Learn from feedback
        await importance_scorer.learn_from_feedback(
            project_id=project_id,
            data_id=data_id,
            feedback_score=feedback_score,
            user_id=current_user["user_id"]
        )
        
        return {
            "success": True,
            "message": "Feedback recorded successfully",
            "project_id": project_id,
            "data_id": data_id,
            "feedback_score": feedback_score
        }
        
    except Exception as e:
        logger.error(f"Error learning from feedback: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process feedback: {str(e)}")

@router.post("/cleanup-expired-data")
async def cleanup_expired_data(
    request: Dict[str, Any],
    background_tasks: BackgroundTasks,
    current_user: Dict = Depends(get_current_user)
):
    """
    Clean up expired data based on retention policies
    """
    try:
        project_id = request.get("project_id")  # Optional - if not provided, cleans all projects
        
        # Run cleanup as background task
        background_tasks.add_task(
            timeline_storage.cleanup_expired_data,
            project_id
        )
        
        return {
            "success": True,
            "message": "Data cleanup initiated",
            "scope": f"project {project_id}" if project_id else "all projects"
        }
        
    except Exception as e:
        logger.error(f"Error initiating data cleanup: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to initiate cleanup: {str(e)}")

@router.get("/health")
async def health_check():
    """Health check for ML Intelligence services"""
    try:
        # Basic health checks
        health_status = {
            "ml_intelligence_service": "healthy",
            "importance_scorer": "healthy",
            "timeline_storage": "healthy",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return {
            "success": True,
            "status": "healthy",
            "services": health_status
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "success": False,
            "status": "unhealthy",
            "error": str(e)
        }
