"""
NeuroSync AI Backend - Response Models
Pydantic models for API responses
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any, Union
from datetime import datetime

class BaseResponse(BaseModel):
    """Base response model with common fields"""
    success: bool = Field(..., description="Whether the request was successful")
    message: str = Field(..., description="Response message")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")

class ErrorResponse(BaseResponse):
    """Error response model"""
    success: bool = Field(default=False, description="Always false for errors")
    error_code: str = Field(..., description="Error code")
    details: Optional[Dict[str, Any]] = Field(default={}, description="Additional error details")
    
    class Config:
        schema_extra = {
            "example": {
                "success": False,
                "message": "Invalid project ID",
                "error_code": "INVALID_PROJECT_ID",
                "details": {"project_id": "proj_invalid"},
                "timestamp": "2024-01-15T10:00:00Z"
            }
        }

class DataIngestionResponse(BaseResponse):
    """Response model for data ingestion"""
    ingestion_id: str = Field(..., description="Unique ingestion ID")
    items_processed: int = Field(..., description="Number of items processed")
    items_failed: int = Field(default=0, description="Number of items that failed")
    processing_time: float = Field(..., description="Processing time in seconds")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "Data ingestion completed successfully",
                "ingestion_id": "ing_123456",
                "items_processed": 150,
                "items_failed": 2,
                "processing_time": 45.6,
                "timestamp": "2024-01-15T10:00:00Z"
            }
        }

class QueryResponse(BaseResponse):
    """Response model for AI queries"""
    answer: str = Field(..., description="AI-generated answer")
    sources: List[Dict[str, Any]] = Field(default=[], description="Source documents used")
    confidence: float = Field(..., description="Confidence score (0-1)")
    tokens_used: int = Field(..., description="Number of tokens consumed")
    response_time: float = Field(..., description="Response time in seconds")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "Query processed successfully",
                "answer": "The authentication system uses JWT tokens with OAuth2 flow...",
                "sources": [
                    {
                        "type": "github",
                        "file_path": "src/auth.py",
                        "line_numbers": [45, 67],
                        "relevance_score": 0.95
                    }
                ],
                "confidence": 0.92,
                "tokens_used": 245,
                "response_time": 1.2,
                "timestamp": "2024-01-15T10:00:00Z"
            }
        }

class StreamingQueryResponse(BaseModel):
    """Response model for streaming AI queries"""
    chunk: str = Field(..., description="Response chunk")
    is_final: bool = Field(default=False, description="Whether this is the final chunk")
    tokens_used: Optional[int] = Field(default=None, description="Tokens used (only in final chunk)")
    sources: Optional[List[Dict[str, Any]]] = Field(default=None, description="Sources (only in final chunk)")

class ProjectResponse(BaseResponse):
    """Response model for project operations"""
    project: Dict[str, Any] = Field(..., description="Project data")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "Project retrieved successfully",
                "project": {
                    "id": "proj_123",
                    "name": "My Awesome Project",
                    "description": "A revolutionary web application",
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-15T10:00:00Z",
                    "team_members": 5,
                    "integrations": ["github", "jira"],
                    "settings": {
                        "ai_model": "gpt-4",
                        "max_context_length": 4000
                    }
                },
                "timestamp": "2024-01-15T10:00:00Z"
            }
        }

class ProjectListResponse(BaseResponse):
    """Response model for listing projects"""
    projects: List[Dict[str, Any]] = Field(..., description="List of projects")
    total_count: int = Field(..., description="Total number of projects")
    page: int = Field(default=1, description="Current page number")
    page_size: int = Field(default=10, description="Items per page")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "Projects retrieved successfully",
                "projects": [
                    {
                        "id": "proj_123",
                        "name": "Project Alpha",
                        "description": "First project",
                        "created_at": "2024-01-01T00:00:00Z",
                        "team_members": 3
                    }
                ],
                "total_count": 1,
                "page": 1,
                "page_size": 10,
                "timestamp": "2024-01-15T10:00:00Z"
            }
        }

class IntegrationResponse(BaseResponse):
    """Response model for integration operations"""
    integration: Dict[str, Any] = Field(..., description="Integration data")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "GitHub integration configured successfully",
                "integration": {
                    "type": "github",
                    "repository_url": "https://github.com/user/repo",
                    "status": "active",
                    "last_sync": "2024-01-15T09:30:00Z",
                    "sync_frequency": "hourly",
                    "items_synced": 1250
                },
                "timestamp": "2024-01-15T10:00:00Z"
            }
        }

class MeetingResponse(BaseResponse):
    """Response model for meeting operations"""
    meeting: Dict[str, Any] = Field(..., description="Meeting data")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "Meeting processed successfully",
                "meeting": {
                    "id": "meet_123",
                    "title": "Sprint Planning Meeting",
                    "date": "2024-01-15T10:00:00Z",
                    "participants": ["john@company.com", "jane@company.com"],
                    "duration": 3600,
                    "transcript_available": True,
                    "key_points": ["Sprint goals defined", "Tasks assigned"],
                    "action_items": ["Update documentation", "Review code"]
                },
                "timestamp": "2024-01-15T10:00:00Z"
            }
        }

class DocumentResponse(BaseResponse):
    """Response model for document operations"""
    document: Dict[str, Any] = Field(..., description="Document data")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "Document uploaded successfully",
                "document": {
                    "id": "doc_123",
                    "title": "API Documentation",
                    "type": "specification",
                    "size": 15420,
                    "created_at": "2024-01-15T10:00:00Z",
                    "tags": ["api", "documentation", "backend"],
                    "processed": True
                },
                "timestamp": "2024-01-15T10:00:00Z"
            }
        }

class SearchResponse(BaseResponse):
    """Response model for search operations"""
    results: List[Dict[str, Any]] = Field(..., description="Search results")
    total_count: int = Field(..., description="Total number of results")
    query_time: float = Field(..., description="Query execution time in seconds")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "Search completed successfully",
                "results": [
                    {
                        "id": "result_1",
                        "title": "Authentication Implementation",
                        "content": "The authentication system uses JWT tokens...",
                        "source_type": "github",
                        "file_path": "src/auth.py",
                        "relevance_score": 0.95,
                        "created_at": "2024-01-10T15:30:00Z"
                    }
                ],
                "total_count": 15,
                "query_time": 0.45,
                "timestamp": "2024-01-15T10:00:00Z"
            }
        }

class UserResponse(BaseResponse):
    """Response model for user operations"""
    user: Dict[str, Any] = Field(..., description="User data")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "User profile retrieved successfully",
                "user": {
                    "id": "user_123",
                    "email": "user@company.com",
                    "name": "John Doe",
                    "subscription_tier": "professional",
                    "tokens_remaining": 150,
                    "projects": ["proj_123", "proj_456"],
                    "created_at": "2024-01-01T00:00:00Z",
                    "last_active": "2024-01-15T09:45:00Z"
                },
                "timestamp": "2024-01-15T10:00:00Z"
            }
        }

class TokenUsageResponse(BaseResponse):
    """Response model for token usage operations"""
    usage: Dict[str, Any] = Field(..., description="Token usage data")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "Token usage retrieved successfully",
                "usage": {
                    "tokens_remaining": 150,
                    "tokens_used_today": 25,
                    "tokens_used_this_month": 380,
                    "subscription_tokens": 220,
                    "addon_tokens": 100,
                    "next_reset": "2024-02-01T00:00:00Z",
                    "usage_by_feature": {
                        "ai_query": 200,
                        "document_processing": 80,
                        "meeting_transcription": 100
                    }
                },
                "timestamp": "2024-01-15T10:00:00Z"
            }
        }

class TokenPurchaseResponse(BaseResponse):
    """Response model for token purchase operations"""
    purchase: Dict[str, Any] = Field(..., description="Purchase data")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "Token pack purchased successfully",
                "purchase": {
                    "transaction_id": "txn_123456",
                    "pack_type": "medium",
                    "tokens_added": 500,
                    "amount_paid": 89.00,
                    "currency": "USD",
                    "payment_method": "card_ending_4242",
                    "purchased_at": "2024-01-15T10:00:00Z"
                },
                "timestamp": "2024-01-15T10:00:00Z"
            }
        }

class AnalyticsResponse(BaseResponse):
    """Response model for analytics operations"""
    analytics: Dict[str, Any] = Field(..., description="Analytics data")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "Analytics retrieved successfully",
                "analytics": {
                    "metric_type": "usage",
                    "time_range": "month",
                    "data": {
                        "total_queries": 1250,
                        "total_tokens": 45000,
                        "active_users": 25,
                        "avg_response_time": 1.8,
                        "top_features": [
                            {"feature": "ai_query", "usage": 800},
                            {"feature": "search", "usage": 300},
                            {"feature": "document_upload", "usage": 150}
                        ]
                    },
                    "generated_at": "2024-01-15T10:00:00Z"
                },
                "timestamp": "2024-01-15T10:00:00Z"
            }
        }

class HealthResponse(BaseModel):
    """Response model for health check"""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Health check timestamp")
    services: Dict[str, str] = Field(..., description="Status of dependent services")
    
    class Config:
        schema_extra = {
            "example": {
                "status": "healthy",
                "version": "1.0.0",
                "timestamp": "2024-01-15T10:00:00Z",
                "services": {
                    "database": "healthy",
                    "vector_store": "healthy",
                    "ai_service": "healthy",
                    "cache": "healthy"
                }
            }
        }
