"""
Response Models for NeuroSync AI Backend
Pydantic models for API response validation.
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from enum import Enum

class StatusType(str, Enum):
    """Status types for responses."""
    SUCCESS = "success"
    ERROR = "error"
    PROCESSING = "processing"
    PENDING = "pending"

# Base Response Models
class BaseResponse(BaseModel):
    """Base response model."""
    status: StatusType
    message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class HealthResponse(BaseResponse):
    """Health check response."""
    version: str
    services: Dict[str, str]

# Authentication Responses
class AuthResponse(BaseResponse):
    """Authentication response."""
    user_id: str
    email: str
    subscription_tier: str
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 1800  # 30 minutes

class RefreshTokenResponse(BaseResponse):
    """Refresh token response."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 1800

class UserProfileResponse(BaseResponse):
    """User profile response."""
    user_id: str
    email: str
    subscription_tier: str
    is_active: bool
    created_at: datetime
    projects: List[str]
    metadata: Dict[str, Any]

# Data Ingestion Responses
class IngestionResponse(BaseResponse):
    """Data ingestion response."""
    request_id: str
    estimated_completion: Optional[datetime] = None

class IngestionStatusResponse(BaseResponse):
    """Ingestion status response."""
    request_id: str
    progress: float = Field(..., ge=0.0, le=100.0)
    processed_items: int
    total_items: int
    errors: List[str] = []

# AI Query Responses
class AIQueryResponse(BaseResponse):
    """AI query response."""
    query: str
    response: str
    sources: List[Dict[str, Any]] = []
    confidence: float = Field(..., ge=0.0, le=1.0)
    tokens_used: int
    cost: float
    model_used: str
    processing_time: float

class StreamingResponse(BaseModel):
    """Streaming response chunk."""
    chunk: str
    is_complete: bool = False
    metadata: Optional[Dict[str, Any]] = None

class EmbeddingResponse(BaseResponse):
    """Embedding generation response."""
    embeddings: List[List[float]]
    model_used: str
    tokens_used: int
    cost: float

# Project Management Responses
class ProjectResponse(BaseResponse):
    """Project response."""
    project_id: str
    name: str
    description: Optional[str]
    created_at: datetime
    updated_at: datetime
    owner_id: str
    team_members: List[Dict[str, Any]]
    settings: Dict[str, Any]
    stats: Dict[str, Any]

class ProjectListResponse(BaseResponse):
    """Project list response."""
    projects: List[ProjectResponse]
    total: int
    page: int
    page_size: int

class TeamMemberResponse(BaseModel):
    """Team member response."""
    user_id: str
    email: str
    role: str
    joined_at: datetime
    is_active: bool

# Vector Search Responses
class VectorSearchResult(BaseModel):
    """Vector search result."""
    id: str
    content: str
    metadata: Dict[str, Any]
    score: float

class VectorSearchResponse(BaseResponse):
    """Vector search response."""
    results: List[VectorSearchResult]
    query: str
    total_results: int
    processing_time: float

class VectorUpsertResponse(BaseResponse):
    """Vector upsert response."""
    document_ids: List[str]
    processed_count: int
    failed_count: int
    errors: List[str] = []

# Analytics Responses
class UsageStats(BaseModel):
    """Usage statistics."""
    total_queries: int
    total_tokens: int
    total_cost: float
    avg_response_time: float
    success_rate: float

class ProjectStats(BaseModel):
    """Project statistics."""
    documents_count: int
    embeddings_count: int
    team_members_count: int
    last_activity: Optional[datetime]
    storage_used: int  # in bytes

class AnalyticsResponse(BaseResponse):
    """Analytics response."""
    usage_stats: UsageStats
    project_stats: Optional[ProjectStats] = None
    time_series: List[Dict[str, Any]] = []
    breakdown: Dict[str, Any] = {}

# Cost Optimization Responses
class CostBreakdown(BaseModel):
    """Cost breakdown."""
    input_tokens: float
    output_tokens: float
    embeddings: float
    searches: float
    total: float

class OptimizationSuggestion(BaseModel):
    """Optimization suggestion."""
    type: str
    message: str
    potential_savings: str
    implementation_effort: str

class OptimizationAnalysisResponse(BaseResponse):
    """Cost optimization analysis response."""
    current_costs: CostBreakdown
    projected_savings: float
    optimization_score: float = Field(..., ge=0.0, le=100.0)
    suggestions: List[OptimizationSuggestion]

class ModelRecommendationResponse(BaseResponse):
    """Model recommendation response."""
    recommended_model: str
    confidence: float
    reasoning: str
    cost_comparison: Dict[str, float]

# Knowledge Graph Responses
class EntityResponse(BaseModel):
    """Entity response."""
    id: str
    type: str
    properties: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

class RelationshipResponse(BaseModel):
    """Relationship response."""
    id: str
    source_id: str
    target_id: str
    type: str
    properties: Dict[str, Any]
    created_at: datetime

class GraphQueryResponse(BaseResponse):
    """Knowledge graph query response."""
    entities: List[EntityResponse]
    relationships: List[RelationshipResponse]
    total_nodes: int
    total_edges: int

class GraphStatsResponse(BaseResponse):
    """Graph statistics response."""
    total_nodes: int
    total_edges: int
    entity_types: Dict[str, int]
    avg_connections: float

# File Upload Responses
class FileUploadResponse(BaseResponse):
    """File upload response."""
    file_id: str
    file_name: str
    file_size: int
    upload_url: Optional[str] = None
    processing_status: str

# Integration Responses
class IntegrationResponse(BaseModel):
    """Integration response."""
    integration_id: str
    type: str
    status: str
    last_sync: Optional[datetime]
    sync_status: str
    error_message: Optional[str] = None

class IntegrationListResponse(BaseResponse):
    """Integration list response."""
    integrations: List[IntegrationResponse]
    available_types: List[str]

class SyncResponse(BaseResponse):
    """Sync response."""
    sync_id: str
    integration_id: str
    started_at: datetime
    estimated_completion: Optional[datetime] = None

# Token Usage Responses
class TokenUsageResponse(BaseResponse):
    """Token usage response."""
    user_id: str
    total_tokens: int
    total_cost: float
    quota_limit: int
    quota_remaining: int
    breakdown: Dict[str, Any]
    recent_usage: List[Dict[str, Any]]

class QuotaCheckResponse(BaseResponse):
    """Quota check response."""
    can_proceed: bool
    quota_limit: int
    quota_used: int
    quota_remaining: int
    requested_tokens: int

# Error Responses
class ErrorDetail(BaseModel):
    """Error detail."""
    code: str
    message: str
    field: Optional[str] = None

class ErrorResponse(BaseResponse):
    """Error response."""
    error_code: str
    errors: List[ErrorDetail] = []
    request_id: Optional[str] = None
