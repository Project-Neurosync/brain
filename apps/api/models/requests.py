"""
NeuroSync AI Backend - Request Models
Pydantic models for API requests
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
from datetime import datetime

class DataIngestionRequest(BaseModel):
    """Request model for data ingestion"""
    source_type: str = Field(..., description="Type of data source (github, jira, slack, etc.)")
    data: Dict[str, Any] = Field(..., description="Raw data to be processed")
    project_id: str = Field(..., description="Project ID to associate data with")
    metadata: Optional[Dict[str, Any]] = Field(default={}, description="Additional metadata")
    
    class Config:
        schema_extra = {
            "example": {
                "source_type": "github",
                "data": {
                    "repository_url": "https://github.com/user/repo",
                    "commits": [],
                    "issues": [],
                    "pull_requests": []
                },
                "project_id": "proj_123",
                "metadata": {
                    "branch": "main",
                    "last_sync": "2024-01-01T00:00:00Z"
                }
            }
        }

class QueryRequest(BaseModel):
    """Request model for AI queries"""
    query: str = Field(..., description="User's question or query")
    project_id: str = Field(..., description="Project context for the query")
    context: Optional[Dict[str, Any]] = Field(default={}, description="Additional context")
    max_tokens: Optional[int] = Field(default=1000, description="Maximum tokens for response")
    temperature: Optional[float] = Field(default=0.7, description="AI temperature setting")
    
    class Config:
        schema_extra = {
            "example": {
                "query": "How does the authentication system work in this project?",
                "project_id": "proj_123",
                "context": {
                    "file_path": "src/auth.py",
                    "line_number": 45
                },
                "max_tokens": 1000,
                "temperature": 0.7
            }
        }

class CreateProjectRequest(BaseModel):
    """Request model for creating a new project"""
    name: str = Field(..., description="Project name")
    description: Optional[str] = Field(default="", description="Project description")
    settings: Optional[Dict[str, Any]] = Field(default={}, description="Project settings")
    integrations: Optional[List[str]] = Field(default=[], description="Enabled integrations")
    
    class Config:
        schema_extra = {
            "example": {
                "name": "My Awesome Project",
                "description": "A revolutionary web application",
                "settings": {
                    "ai_model": "gpt-4",
                    "embedding_model": "text-embedding-ada-002",
                    "max_context_length": 4000
                },
                "integrations": ["github", "jira", "slack"]
            }
        }

class UpdateProjectRequest(BaseModel):
    """Request model for updating a project"""
    name: Optional[str] = Field(default=None, description="Updated project name")
    description: Optional[str] = Field(default=None, description="Updated description")
    settings: Optional[Dict[str, Any]] = Field(default=None, description="Updated settings")
    integrations: Optional[List[str]] = Field(default=None, description="Updated integrations")

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
