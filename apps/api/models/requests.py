"""
NeuroSync AI Backend - Request Models
Pydantic models for API requests
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, Dict, List, Any, Union
from enum import Enum
from datetime import datetime

class SourceType(str, Enum):
    """Data source types."""
    GITHUB = "github"
    JIRA = "jira"
    SLACK = "slack"
    DOCUMENT = "document"
    MEETING = "meeting"
    MANUAL = "manual"

class SubscriptionTier(str, Enum):
    """Subscription tiers."""
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"

# Authentication Models
class UserRegistrationRequest(BaseModel):
    """User registration request."""
    email: EmailStr
    password: str = Field(..., min_length=8)
    subscription_tier: SubscriptionTier = SubscriptionTier.STARTER
    metadata: Optional[Dict[str, Any]] = None

class UserLoginRequest(BaseModel):
    """User login request."""
    email: EmailStr
    password: str

class RefreshTokenRequest(BaseModel):
    """Refresh token request."""
    refresh_token: str

# Data Ingestion Models
class GitHubIngestionConfig(BaseModel):
    """GitHub repository ingestion configuration."""
    repo_url: str
    branch: Optional[str] = "main"
    include_issues: bool = True
    include_prs: bool = True
    include_wiki: bool = False
    file_extensions: Optional[List[str]] = None

class JiraIngestionConfig(BaseModel):
    """Jira project ingestion configuration."""
    server_url: str
    project_key: str
    username: str
    api_token: str
    include_comments: bool = True
    max_issues: Optional[int] = 1000

class SlackIngestionConfig(BaseModel):
    """Slack channel ingestion configuration."""
    workspace_id: str
    channel_id: str
    bot_token: str
    days_back: int = 30
    include_threads: bool = True

class DocumentIngestionConfig(BaseModel):
    """Document ingestion configuration."""
    file_paths: List[str]
    file_type: Optional[str] = None
    extract_metadata: bool = True

class DataIngestionRequest(BaseModel):
    """Data ingestion request."""
    project_id: str
    source_type: SourceType
    config: Union[GitHubIngestionConfig, JiraIngestionConfig, SlackIngestionConfig, DocumentIngestionConfig]
    metadata: Optional[Dict[str, Any]] = None

# AI Query Models
class AIQueryRequest(BaseModel):
    """AI query request."""
    query: str = Field(..., min_length=1, max_length=2000)
    project_id: str
    context: Optional[Dict[str, Any]] = None
    stream: bool = False
    max_tokens: Optional[int] = None
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)

class EmbeddingRequest(BaseModel):
    """Embedding generation request."""
    texts: List[str] = Field(..., min_items=1, max_items=100)
    project_id: str

# Project Management Models
class CreateProjectRequest(BaseModel):
    """Create project request."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None

class UpdateProjectRequest(BaseModel):
    """Update project request."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None

class InviteUserRequest(BaseModel):
    """Invite user to project request."""
    email: EmailStr
    role: str = "member"

# Vector Search Models
class VectorSearchRequest(BaseModel):
    """Vector search request."""
    query: str = Field(..., min_length=1)
    project_id: str
    limit: int = Field(10, ge=1, le=100)
    filters: Optional[Dict[str, Any]] = None

class VectorUpsertRequest(BaseModel):
    """Vector upsert request."""
    project_id: str
    documents: List[Dict[str, Any]]
    metadata: Optional[Dict[str, Any]] = None

# Analytics Models
class AnalyticsRequest(BaseModel):
    """Analytics request."""
    project_id: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    metrics: Optional[List[str]] = None

# Cost Optimization Models
class OptimizationAnalysisRequest(BaseModel):
    """Cost optimization analysis request."""
    user_id: Optional[str] = None
    project_id: Optional[str] = None
    time_period_days: int = Field(30, ge=1, le=365)

class ModelRecommendationRequest(BaseModel):
    """Model recommendation request."""
    query: str
    context_size: Optional[int] = None
    user_tier: Optional[SubscriptionTier] = None

# Knowledge Graph Models
class EntityCreationRequest(BaseModel):
    """Entity creation request."""
    project_id: str
    entity_type: str
    properties: Dict[str, Any]
    relationships: Optional[List[Dict[str, Any]]] = None

class RelationshipCreationRequest(BaseModel):
    """Relationship creation request."""
    source_id: str
    target_id: str
    relationship_type: str
    properties: Optional[Dict[str, Any]] = None

class GraphQueryRequest(BaseModel):
    """Knowledge graph query request."""
    project_id: str
    entity_id: Optional[str] = None
    relationship_types: Optional[List[str]] = None
    max_depth: int = Field(2, ge=1, le=5)

# File Upload Models
class FileUploadRequest(BaseModel):
    """File upload request."""
    project_id: str
    file_name: str
    file_type: str
    file_size: int
    metadata: Optional[Dict[str, Any]] = None

# Integration Models
class IntegrationConnectionRequest(BaseModel):
    """Integration connection request."""
    project_id: str
    integration_type: str
    config: Dict[str, Any]
    enabled: bool = True

class IntegrationSyncRequest(BaseModel):
    """Integration sync request."""
    project_id: str
    integration_id: str
    full_sync: bool = False

class AddTeamMemberRequest(BaseModel):
    """Request model for adding team members to a project"""
    email: str = Field(..., description="Team member's email")
    role: str = Field(..., description="Team member's role (viewer, editor, admin)")
    permissions: Optional[List[str]] = Field(default=[], description="Specific permissions")
    
    class Config:
        schema_extra = {
            "example": {
                "email": "developer@company.com",
                "role": "editor",
                "permissions": ["read", "write", "comment"]
            }
        }

class GitHubIntegrationRequest(BaseModel):
    """Request model for GitHub integration"""
    repository_url: str = Field(..., description="GitHub repository URL")
    access_token: str = Field(..., description="GitHub access token")
    webhook_url: Optional[str] = Field(default=None, description="Webhook URL for real-time updates")
    sync_frequency: Optional[str] = Field(default="daily", description="Sync frequency")
    
    class Config:
        schema_extra = {
            "example": {
                "repository_url": "https://github.com/user/repo",
                "access_token": "ghp_xxxxxxxxxxxx",
                "webhook_url": "https://api.neurosync.com/webhooks/github",
                "sync_frequency": "hourly"
            }
        }

class JiraIntegrationRequest(BaseModel):
    """Request model for Jira integration"""
    jira_url: str = Field(..., description="Jira instance URL")
    username: str = Field(..., description="Jira username")
    api_token: str = Field(..., description="Jira API token")
    project_key: str = Field(..., description="Jira project key")
    
    class Config:
        schema_extra = {
            "example": {
                "jira_url": "https://company.atlassian.net",
                "username": "user@company.com",
                "api_token": "xxxxxxxxxxxx",
                "project_key": "PROJ"
            }
        }

class SlackIntegrationRequest(BaseModel):
    """Request model for Slack integration"""
    bot_token: str = Field(..., description="Slack bot token")
    channels: List[str] = Field(..., description="Slack channels to monitor")
    webhook_url: Optional[str] = Field(default=None, description="Slack webhook URL")
    
    class Config:
        schema_extra = {
            "example": {
                "bot_token": "xoxb-xxxxxxxxxxxx",
                "channels": ["#development", "#general"],
                "webhook_url": "https://hooks.slack.com/services/xxx/xxx/xxx"
            }
        }

class MeetingUploadRequest(BaseModel):
    """Request model for meeting audio upload"""
    project_id: str = Field(..., description="Project ID")
    meeting_title: str = Field(..., description="Meeting title")
    participants: List[str] = Field(..., description="Meeting participants")
    meeting_date: datetime = Field(..., description="Meeting date and time")
    audio_url: Optional[str] = Field(default=None, description="URL to audio file")
    transcript: Optional[str] = Field(default=None, description="Pre-existing transcript")
    
    class Config:
        schema_extra = {
            "example": {
                "project_id": "proj_123",
                "meeting_title": "Sprint Planning Meeting",
                "participants": ["john@company.com", "jane@company.com"],
                "meeting_date": "2024-01-15T10:00:00Z",
                "audio_url": "https://storage.com/meeting_audio.mp3",
                "transcript": "Optional pre-existing transcript"
            }
        }

class DocumentUploadRequest(BaseModel):
    """Request model for document upload"""
    project_id: str = Field(..., description="Project ID")
    document_type: str = Field(..., description="Type of document (readme, spec, wiki, etc.)")
    title: str = Field(..., description="Document title")
    content: str = Field(..., description="Document content")
    tags: Optional[List[str]] = Field(default=[], description="Document tags")
    
    class Config:
        schema_extra = {
            "example": {
                "project_id": "proj_123",
                "document_type": "specification",
                "title": "API Documentation",
                "content": "# API Documentation\n\nThis document describes...",
                "tags": ["api", "documentation", "backend"]
            }
        }

class SearchRequest(BaseModel):
    """Request model for semantic search"""
    query: str = Field(..., description="Search query")
    project_id: Optional[str] = Field(default=None, description="Project to search within")
    filters: Optional[Dict[str, Any]] = Field(default={}, description="Search filters")
    limit: Optional[int] = Field(default=10, description="Maximum number of results")
    include_sources: Optional[bool] = Field(default=True, description="Include source information")
    
    class Config:
        schema_extra = {
            "example": {
                "query": "authentication implementation",
                "project_id": "proj_123",
                "filters": {
                    "source_type": ["github", "documentation"],
                    "date_range": {
                        "start": "2024-01-01",
                        "end": "2024-12-31"
                    }
                },
                "limit": 10,
                "include_sources": True
            }
        }

class TokenPurchaseRequest(BaseModel):
    """Request model for purchasing token packs"""
    pack_type: str = Field(..., description="Type of token pack (small, medium, large, enterprise)")
    payment_method: str = Field(..., description="Payment method")
    billing_address: Optional[Dict[str, str]] = Field(default={}, description="Billing address")
    
    class Config:
        schema_extra = {
            "example": {
                "pack_type": "medium",
                "payment_method": "stripe_card_xxx",
                "billing_address": {
                    "street": "123 Main St",
                    "city": "San Francisco",
                    "state": "CA",
                    "zip": "94105",
                    "country": "US"
                }
            }
        }

class AnalyticsRequest(BaseModel):
    """Request model for analytics queries"""
    metric_type: str = Field(..., description="Type of metric (usage, performance, engagement)")
    time_range: str = Field(..., description="Time range (day, week, month, year)")
    project_id: Optional[str] = Field(default=None, description="Project ID for project-specific analytics")
    filters: Optional[Dict[str, Any]] = Field(default={}, description="Additional filters")
    
    class Config:
        schema_extra = {
            "example": {
                "metric_type": "usage",
                "time_range": "month",
                "project_id": "proj_123",
                "filters": {
                    "user_type": "active",
                    "feature": "ai_query"
                }
            }
        }
