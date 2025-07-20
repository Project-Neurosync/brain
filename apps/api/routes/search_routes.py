"""
Semantic Search API Routes for NeuroSync
Exposes semantic code search, cross-source search, and contextual search features
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime

from core.semantic_search import SemanticSearchEngine, SearchType, SearchScope, ContentType
from models.requests import *
from models.responses import *
from core.auth import AuthManager

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/api/v1/search", tags=["Semantic Search"])

# Initialize services
search_engine = SemanticSearchEngine()
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

@router.post("/semantic-code")
async def semantic_code_search(
    request: Dict[str, Any],
    current_user: Dict = Depends(get_current_user)
):
    """
    Perform semantic search specifically for code
    
    Request format:
    {
        "query": "function to authenticate users with JWT tokens",
        "project_id": "string",
        "language": "python" (optional),
        "file_types": ["py", "js"] (optional),
        "importance_threshold": 0.0,
        "limit": 20
    }
    """
    try:
        query = request.get("query")
        project_id = request.get("project_id")
        
        if not query or not project_id:
            raise HTTPException(status_code=400, detail="query and project_id are required")
        
        # Extract optional parameters
        language = request.get("language")
        file_types = request.get("file_types")
        importance_threshold = request.get("importance_threshold", 0.0)
        limit = min(request.get("limit", 20), 100)  # Cap at 100 results
        
        # Perform semantic code search
        search_response = await search_engine.semantic_code_search(
            query=query,
            project_id=project_id,
            language=language,
            file_types=file_types,
            importance_threshold=importance_threshold,
            limit=limit
        )
        
        # Convert to API response format
        return {
            "success": True,
            "search_id": search_response.search_id,
            "query": search_response.query,
            "search_type": search_response.search_type.value,
            "total_results": search_response.total_results,
            "search_time_ms": search_response.search_time_ms,
            "results": [
                {
                    "id": result.id,
                    "content_type": result.content_type.value,
                    "title": result.title,
                    "content": result.content,
                    "relevance_score": result.relevance_score,
                    "importance_score": result.importance_score,
                    "importance_level": result.importance_level.value,
                    "timeline_category": result.timeline_category.value,
                    "source_info": result.source_info,
                    "metadata": result.metadata,
                    "highlights": result.highlights,
                    "related_items": result.related_items,
                    "context_path": result.context_path,
                    "found_at": result.found_at.isoformat()
                }
                for result in search_response.results
            ],
            "suggestions": search_response.suggestions,
            "related_queries": search_response.related_queries,
            "facets": search_response.facets,
            "context_insights": search_response.context_insights
        }
        
    except Exception as e:
        logger.error(f"Error in semantic code search: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.post("/cross-source")
async def cross_source_search(
    request: Dict[str, Any],
    current_user: Dict = Depends(get_current_user)
):
    """
    Perform cross-source search across all data types
    
    Request format:
    {
        "query": "authentication security issues",
        "project_id": "string",
        "content_types": ["code", "documentation", "meeting", "issue"] (optional),
        "timeline_filter": "recent" (optional),
        "importance_threshold": 0.0,
        "limit": 30
    }
    """
    try:
        query = request.get("query")
        project_id = request.get("project_id")
        
        if not query or not project_id:
            raise HTTPException(status_code=400, detail="query and project_id are required")
        
        # Parse content types
        content_types = None
        if request.get("content_types"):
            try:
                content_types = [ContentType(ct) for ct in request["content_types"]]
            except ValueError as e:
                raise HTTPException(status_code=400, detail=f"Invalid content type: {e}")
        
        # Parse timeline filter
        timeline_filter = None
        if request.get("timeline_filter"):
            try:
                from core.data_importance_scoring import TimelineCategory
                timeline_filter = TimelineCategory(request["timeline_filter"])
            except ValueError as e:
                raise HTTPException(status_code=400, detail=f"Invalid timeline filter: {e}")
        
        importance_threshold = request.get("importance_threshold", 0.0)
        limit = min(request.get("limit", 30), 100)  # Cap at 100 results
        
        # Perform cross-source search
        search_response = await search_engine.cross_source_search(
            query=query,
            project_id=project_id,
            content_types=content_types,
            timeline_filter=timeline_filter,
            importance_threshold=importance_threshold,
            limit=limit
        )
        
        # Convert to API response format
        return {
            "success": True,
            "search_id": search_response.search_id,
            "query": search_response.query,
            "search_type": search_response.search_type.value,
            "total_results": search_response.total_results,
            "search_time_ms": search_response.search_time_ms,
            "results": [
                {
                    "id": result.id,
                    "content_type": result.content_type.value,
                    "title": result.title,
                    "content": result.content,
                    "relevance_score": result.relevance_score,
                    "importance_score": result.importance_score,
                    "importance_level": result.importance_level.value,
                    "timeline_category": result.timeline_category.value,
                    "source_info": result.source_info,
                    "metadata": result.metadata,
                    "highlights": result.highlights,
                    "related_items": result.related_items,
                    "context_path": result.context_path,
                    "found_at": result.found_at.isoformat()
                }
                for result in search_response.results
            ],
            "suggestions": search_response.suggestions,
            "related_queries": search_response.related_queries,
            "facets": search_response.facets,
            "context_insights": search_response.context_insights
        }
        
    except Exception as e:
        logger.error(f"Error in cross-source search: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.post("/contextual")
async def contextual_search(
    request: Dict[str, Any],
    current_user: Dict = Depends(get_current_user)
):
    """
    Perform context-aware search with proactive suggestions
    
    Request format:
    {
        "query": "how to implement caching",
        "project_id": "string",
        "user_context": {
            "role": "developer",
            "preferences": {...}
        },
        "current_file": "/path/to/current/file.py" (optional),
        "recent_activity": [...] (optional),
        "limit": 20
    }
    """
    try:
        query = request.get("query")
        project_id = request.get("project_id")
        user_context = request.get("user_context", {})
        
        if not query or not project_id:
            raise HTTPException(status_code=400, detail="query and project_id are required")
        
        current_file = request.get("current_file")
        recent_activity = request.get("recent_activity")
        limit = min(request.get("limit", 20), 100)  # Cap at 100 results
        
        # Perform contextual search
        search_response = await search_engine.contextual_search_with_suggestions(
            query=query,
            project_id=project_id,
            user_context=user_context,
            current_file=current_file,
            recent_activity=recent_activity,
            limit=limit
        )
        
        # Convert to API response format
        return {
            "success": True,
            "search_id": search_response.search_id,
            "query": search_response.query,
            "search_type": search_response.search_type.value,
            "total_results": search_response.total_results,
            "search_time_ms": search_response.search_time_ms,
            "results": [
                {
                    "id": result.id,
                    "content_type": result.content_type.value,
                    "title": result.title,
                    "content": result.content,
                    "relevance_score": result.relevance_score,
                    "importance_score": result.importance_score,
                    "importance_level": result.importance_level.value,
                    "timeline_category": result.timeline_category.value,
                    "source_info": result.source_info,
                    "metadata": result.metadata,
                    "highlights": result.highlights,
                    "related_items": result.related_items,
                    "context_path": result.context_path,
                    "found_at": result.found_at.isoformat()
                }
                for result in search_response.results
            ],
            "suggestions": search_response.suggestions,
            "related_queries": search_response.related_queries,
            "facets": search_response.facets,
            "context_insights": search_response.context_insights
        }
        
    except Exception as e:
        logger.error(f"Error in contextual search: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.get("/suggestions/{project_id}")
async def get_search_suggestions(
    project_id: str,
    query: str = Query(..., description="Partial query for suggestions"),
    limit: int = Query(10, description="Maximum number of suggestions"),
    current_user: Dict = Depends(get_current_user)
):
    """
    Get search suggestions based on partial query and project context
    """
    try:
        # This would typically use search history and project context
        # For now, return basic suggestions
        suggestions = [
            f"Find {query} functions",
            f"Search for {query} in documentation",
            f"Look for {query} examples",
            f"Find tests for {query}",
            f"Search meetings about {query}"
        ]
        
        return {
            "success": True,
            "query": query,
            "project_id": project_id,
            "suggestions": suggestions[:limit]
        }
        
    except Exception as e:
        logger.error(f"Error getting search suggestions: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get suggestions: {str(e)}")

@router.get("/history/{project_id}")
async def get_search_history(
    project_id: str,
    limit: int = Query(20, description="Maximum number of history entries"),
    current_user: Dict = Depends(get_current_user)
):
    """
    Get recent search history for a project
    """
    try:
        # Get search history from the search engine
        history = search_engine.search_history.get(project_id, [])
        
        # Return recent history
        recent_history = history[-limit:] if len(history) > limit else history
        
        return {
            "success": True,
            "project_id": project_id,
            "history": recent_history,
            "total_searches": len(history)
        }
        
    except Exception as e:
        logger.error(f"Error getting search history: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get search history: {str(e)}")

@router.post("/similar-code")
async def find_similar_code(
    request: Dict[str, Any],
    current_user: Dict = Depends(get_current_user)
):
    """
    Find similar code patterns to a given code snippet
    
    Request format:
    {
        "code_snippet": "def authenticate_user(token):\n    ...",
        "project_id": "string",
        "language": "python" (optional),
        "similarity_threshold": 0.7,
        "limit": 10
    }
    """
    try:
        code_snippet = request.get("code_snippet")
        project_id = request.get("project_id")
        
        if not code_snippet or not project_id:
            raise HTTPException(status_code=400, detail="code_snippet and project_id are required")
        
        language = request.get("language")
        similarity_threshold = request.get("similarity_threshold", 0.7)
        limit = min(request.get("limit", 10), 50)  # Cap at 50 results
        
        # For now, perform a semantic search using the code snippet as query
        search_response = await search_engine.semantic_code_search(
            query=code_snippet,
            project_id=project_id,
            language=language,
            importance_threshold=0.0,
            limit=limit
        )
        
        # Filter results by similarity threshold
        similar_results = [
            result for result in search_response.results
            if result.relevance_score >= similarity_threshold
        ]
        
        return {
            "success": True,
            "code_snippet": code_snippet,
            "project_id": project_id,
            "similarity_threshold": similarity_threshold,
            "similar_code_found": len(similar_results),
            "results": [
                {
                    "id": result.id,
                    "content": result.content,
                    "similarity_score": result.relevance_score,
                    "file_path": result.source_info.get("file_path", ""),
                    "language": result.metadata.get("language", ""),
                    "highlights": result.highlights
                }
                for result in similar_results
            ]
        }
        
    except Exception as e:
        logger.error(f"Error finding similar code: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to find similar code: {str(e)}")

@router.get("/analytics/{project_id}")
async def get_search_analytics(
    project_id: str,
    days_back: int = Query(30, description="Number of days to analyze"),
    current_user: Dict = Depends(get_current_user)
):
    """
    Get search analytics for a project
    """
    try:
        history = search_engine.search_history.get(project_id, [])
        
        # Filter by date range
        from datetime import datetime, timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        
        recent_searches = [
            search for search in history
            if datetime.fromisoformat(search["timestamp"]) >= cutoff_date
        ]
        
        # Generate analytics
        search_types = {}
        popular_queries = {}
        
        for search in recent_searches:
            search_type = search["search_type"]
            search_types[search_type] = search_types.get(search_type, 0) + 1
            
            query = search["query"]
            popular_queries[query] = popular_queries.get(query, 0) + 1
        
        # Sort popular queries
        popular_queries_sorted = sorted(
            popular_queries.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:10]
        
        return {
            "success": True,
            "project_id": project_id,
            "analysis_period_days": days_back,
            "analytics": {
                "total_searches": len(recent_searches),
                "search_types": search_types,
                "popular_queries": dict(popular_queries_sorted),
                "average_searches_per_day": len(recent_searches) / max(days_back, 1)
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting search analytics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get analytics: {str(e)}")

@router.get("/health")
async def health_check():
    """Health check for search services"""
    try:
        health_status = {
            "semantic_search_engine": "healthy",
            "vector_database": "healthy",
            "knowledge_graph": "healthy",
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
