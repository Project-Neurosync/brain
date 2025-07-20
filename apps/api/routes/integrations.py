"""
Integration API Routes for NeuroSync
Handles GitHub, Jira, Slack, and Confluence integrations
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime
import uuid
import logging
import asyncio

from core.github_integration import GitHubIntegrationService
from core.jira_integration import JiraIntegrationService
from core.slack_integration import SlackIntegrationService
from core.confluence_integration import ConfluenceIntegrationService
from core.project_management import ProjectManagementService
from middleware.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/integrations", tags=["integrations"])

# Pydantic models for API requests/responses
class IntegrationConfig(BaseModel):
    # GitHub specific
    repository_url: Optional[str] = None
    github_token: Optional[str] = None
    branches: Optional[List[str]] = None
    include_issues: Optional[bool] = True
    include_prs: Optional[bool] = True
    include_wiki: Optional[bool] = False
    
    # Jira specific
    jira_url: Optional[str] = None
    jira_email: Optional[str] = None
    jira_token: Optional[str] = None
    project_key: Optional[str] = None
    include_comments: Optional[bool] = True
    status_filters: Optional[List[str]] = None
    
    # Slack specific
    slack_token: Optional[str] = None
    workspace_id: Optional[str] = None
    channels: Optional[List[str]] = None
    include_threads: Optional[bool] = True
    date_range: Optional[Dict[str, str]] = None
    
    # Confluence specific
    confluence_url: Optional[str] = None
    confluence_email: Optional[str] = None
    confluence_token: Optional[str] = None
    space_keys: Optional[List[str]] = None
    include_attachments: Optional[bool] = False

class IntegrationStats(BaseModel):
    total_documents: int = 0
    last_sync_documents: int = 0
    total_size_mb: float = 0.0
    sync_duration_seconds: Optional[int] = None
    error_count: int = 0
    success_rate: float = 100.0

class Integration(BaseModel):
    id: str
    project_id: str
    type: str  # github, jira, slack, confluence
    name: str
    status: str  # connected, disconnected, error, syncing
    config: IntegrationConfig
    last_sync: Optional[datetime] = None
    sync_status: str = "idle"  # idle, syncing, completed, failed
    sync_progress: Optional[int] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    stats: IntegrationStats

class ConnectIntegrationRequest(BaseModel):
    type: str  # github, jira, slack, confluence
    name: str
    config: IntegrationConfig

class UpdateIntegrationRequest(BaseModel):
    name: Optional[str] = None
    config: Optional[IntegrationConfig] = None
    status: Optional[str] = None

class SyncResult(BaseModel):
    integration_id: str
    sync_id: str
    status: str  # started, completed, failed
    documents_processed: int = 0
    documents_added: int = 0
    documents_updated: int = 0
    documents_deleted: int = 0
    duration_seconds: int = 0
    error_message: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None

class DataSource(BaseModel):
    id: str
    integration_id: str
    type: str  # file, issue, pr, message, page
    title: str
    url: Optional[str] = None
    content_preview: str
    last_updated: datetime
    size_bytes: int
    metadata: Dict[str, Any]

class IntegrationType(BaseModel):
    type: str
    name: str
    description: str
    icon: str
    required_fields: List[str]
    optional_fields: List[str]
    oauth_supported: bool = False

# In-memory storage for demo (replace with database in production)
integrations_db: Dict[str, Integration] = {}
sync_history_db: Dict[str, List[SyncResult]] = {}
data_sources_db: Dict[str, List[DataSource]] = {}

# Initialize services
github_service = GitHubIntegrationService()
jira_service = JiraIntegrationService()
slack_service = SlackIntegrationService()
confluence_service = ConfluenceIntegrationService()
project_service = ProjectManagementService()

@router.get("/types", response_model=List[IntegrationType])
async def get_integration_types():
    """Get available integration types and their requirements"""
    return [
        IntegrationType(
            type="github",
            name="GitHub",
            description="Sync repositories, pull requests, issues, and commit history",
            icon="GitBranchIcon",
            required_fields=["github_token", "repository_url"],
            optional_fields=["branches", "include_issues", "include_prs", "include_wiki"]
        ),
        IntegrationType(
            type="jira",
            name="Jira",
            description="Connect tickets, sprints, and project management data",
            icon="TicketIcon",
            required_fields=["jira_url", "jira_email", "jira_token"],
            optional_fields=["project_key", "include_comments", "status_filters"]
        ),
        IntegrationType(
            type="slack",
            name="Slack",
            description="Import conversations, threads, and team communications",
            icon="MessageSquareIcon",
            required_fields=["slack_token"],
            optional_fields=["workspace_id", "channels", "include_threads", "date_range"]
        ),
        IntegrationType(
            type="confluence",
            name="Confluence",
            description="Import documentation, wikis, and knowledge base articles",
            icon="FileTextIcon",
            required_fields=["confluence_url", "confluence_email", "confluence_token"],
            optional_fields=["space_keys", "include_attachments"]
        )
    ]

@router.get("/{project_id}", response_model=List[Integration])
async def get_integrations(
    project_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """Get all integrations for a project"""
    # Check project access
    has_access = await project_service.check_user_permission(
        project_id, current_user["user_id"], "viewer"
    )
    if not has_access:
        raise HTTPException(status_code=403, detail="Access denied to project")
    
    # Filter integrations by project
    project_integrations = [
        integration for integration in integrations_db.values()
        if integration.project_id == project_id
    ]
    
    return project_integrations

@router.get("/{project_id}/{integration_id}", response_model=Integration)
async def get_integration(
    project_id: str,
    integration_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """Get a specific integration"""
    # Check project access
    has_access = await project_service.check_user_permission(
        project_id, current_user["user_id"], "viewer"
    )
    if not has_access:
        raise HTTPException(status_code=403, detail="Access denied to project")
    
    if integration_id not in integrations_db:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    integration = integrations_db[integration_id]
    if integration.project_id != project_id:
        raise HTTPException(status_code=404, detail="Integration not found in project")
    
    return integration

@router.post("/{project_id}", response_model=Integration)
async def connect_integration(
    project_id: str,
    request: ConnectIntegrationRequest,
    current_user: Dict = Depends(get_current_user)
):
    """Connect a new integration"""
    # Check project access
    has_access = await project_service.check_user_permission(
        project_id, current_user["user_id"], "admin"
    )
    if not has_access:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Validate integration type
    if request.type not in ["github", "jira", "slack", "confluence"]:
        raise HTTPException(status_code=400, detail="Invalid integration type")
    
    # Test connection before creating integration
    try:
        if request.type == "github":
            await github_service.test_connection(
                request.config.github_token,
                request.config.repository_url
            )
        elif request.type == "jira":
            await jira_service.test_connection(
                request.config.jira_url,
                request.config.jira_email,
                request.config.jira_token
            )
        elif request.type == "slack":
            await slack_service.test_connection(request.config.slack_token)
        elif request.type == "confluence":
            await confluence_service.test_connection(
                request.config.confluence_url,
                request.config.confluence_email,
                request.config.confluence_token
            )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Connection test failed: {str(e)}")
    
    # Create integration
    integration_id = str(uuid.uuid4())
    now = datetime.utcnow()
    
    integration = Integration(
        id=integration_id,
        project_id=project_id,
        type=request.type,
        name=request.name,
        status="connected",
        config=request.config,
        created_at=now,
        updated_at=now,
        stats=IntegrationStats()
    )
    
    integrations_db[integration_id] = integration
    sync_history_db[integration_id] = []
    data_sources_db[integration_id] = []
    
    logger.info(f"Created {request.type} integration {integration_id} for project {project_id}")
    
    return integration

@router.put("/{project_id}/{integration_id}", response_model=Integration)
async def update_integration(
    project_id: str,
    integration_id: str,
    request: UpdateIntegrationRequest,
    current_user: Dict = Depends(get_current_user)
):
    """Update an existing integration"""
    # Check project access
    has_access = await project_service.check_user_permission(
        project_id, current_user["user_id"], "admin"
    )
    if not has_access:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    if integration_id not in integrations_db:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    integration = integrations_db[integration_id]
    if integration.project_id != project_id:
        raise HTTPException(status_code=404, detail="Integration not found in project")
    
    # Update fields
    if request.name:
        integration.name = request.name
    if request.config:
        # Merge config updates
        current_config = integration.config.dict()
        update_config = request.config.dict(exclude_unset=True)
        current_config.update(update_config)
        integration.config = IntegrationConfig(**current_config)
    if request.status:
        integration.status = request.status
    
    integration.updated_at = datetime.utcnow()
    
    logger.info(f"Updated integration {integration_id} for project {project_id}")
    
    return integration

@router.delete("/{project_id}/{integration_id}")
async def delete_integration(
    project_id: str,
    integration_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """Delete an integration"""
    # Check project access
    has_access = await project_service.check_user_permission(
        project_id, current_user["user_id"], "admin"
    )
    if not has_access:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    if integration_id not in integrations_db:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    integration = integrations_db[integration_id]
    if integration.project_id != project_id:
        raise HTTPException(status_code=404, detail="Integration not found in project")
    
    # Delete integration and related data
    del integrations_db[integration_id]
    if integration_id in sync_history_db:
        del sync_history_db[integration_id]
    if integration_id in data_sources_db:
        del data_sources_db[integration_id]
    
    logger.info(f"Deleted integration {integration_id} from project {project_id}")
    
    return {"message": "Integration deleted successfully"}

@router.post("/{project_id}/{integration_id}/sync", response_model=SyncResult)
async def sync_integration(
    project_id: str,
    integration_id: str,
    background_tasks: BackgroundTasks,
    current_user: Dict = Depends(get_current_user)
):
    """Trigger manual sync for an integration"""
    # Check project access
    has_access = await project_service.check_user_permission(
        project_id, current_user["user_id"], "member"
    )
    if not has_access:
        raise HTTPException(status_code=403, detail="Member access required")
    
    if integration_id not in integrations_db:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    integration = integrations_db[integration_id]
    if integration.project_id != project_id:
        raise HTTPException(status_code=404, detail="Integration not found in project")
    
    if integration.sync_status == "syncing":
        raise HTTPException(status_code=400, detail="Sync already in progress")
    
    # Create sync result
    sync_id = str(uuid.uuid4())
    sync_result = SyncResult(
        integration_id=integration_id,
        sync_id=sync_id,
        status="started",
        started_at=datetime.utcnow()
    )
    
    # Update integration status
    integration.sync_status = "syncing"
    integration.sync_progress = 0
    integration.updated_at = datetime.utcnow()
    
    # Add to sync history
    if integration_id not in sync_history_db:
        sync_history_db[integration_id] = []
    sync_history_db[integration_id].append(sync_result)
    
    # Start background sync
    background_tasks.add_task(
        perform_integration_sync,
        integration_id,
        sync_id,
        project_id
    )
    
    logger.info(f"Started sync {sync_id} for integration {integration_id}")
    
    return sync_result

@router.get("/{project_id}/{integration_id}/sync-history", response_model=List[SyncResult])
async def get_sync_history(
    project_id: str,
    integration_id: str,
    limit: int = 10,
    offset: int = 0,
    current_user: Dict = Depends(get_current_user)
):
    """Get sync history for an integration"""
    # Check project access
    has_access = await project_service.check_user_permission(
        project_id, current_user["user_id"], "viewer"
    )
    if not has_access:
        raise HTTPException(status_code=403, detail="Access denied to project")
    
    if integration_id not in integrations_db:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    integration = integrations_db[integration_id]
    if integration.project_id != project_id:
        raise HTTPException(status_code=404, detail="Integration not found in project")
    
    history = sync_history_db.get(integration_id, [])
    # Sort by started_at descending
    history.sort(key=lambda x: x.started_at, reverse=True)
    
    return history[offset:offset + limit]

@router.get("/{project_id}/{integration_id}/test")
async def test_integration(
    project_id: str,
    integration_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """Test integration connection"""
    # Check project access
    has_access = await project_service.check_user_permission(
        project_id, current_user["user_id"], "member"
    )
    if not has_access:
        raise HTTPException(status_code=403, detail="Member access required")
    
    if integration_id not in integrations_db:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    integration = integrations_db[integration_id]
    if integration.project_id != project_id:
        raise HTTPException(status_code=404, detail="Integration not found in project")
    
    try:
        if integration.type == "github":
            result = await github_service.test_connection(
                integration.config.github_token,
                integration.config.repository_url
            )
        elif integration.type == "jira":
            result = await jira_service.test_connection(
                integration.config.jira_url,
                integration.config.jira_email,
                integration.config.jira_token
            )
        elif integration.type == "slack":
            result = await slack_service.test_connection(integration.config.slack_token)
        elif integration.type == "confluence":
            result = await confluence_service.test_connection(
                integration.config.confluence_url,
                integration.config.confluence_email,
                integration.config.confluence_token
            )
        else:
            raise HTTPException(status_code=400, detail="Integration type not supported")
        
        return {
            "status": "success",
            "message": "Connection test successful",
            "details": result
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Connection test failed: {str(e)}"
        }

@router.get("/{project_id}/{integration_id}/data-sources")
async def get_data_sources(
    project_id: str,
    integration_id: str,
    limit: int = 50,
    offset: int = 0,
    type: Optional[str] = None,
    search: Optional[str] = None,
    current_user: Dict = Depends(get_current_user)
):
    """Get data sources from an integration"""
    # Check project access
    has_access = await project_service.check_user_permission(
        project_id, current_user["user_id"], "viewer"
    )
    if not has_access:
        raise HTTPException(status_code=403, detail="Access denied to project")
    
    if integration_id not in integrations_db:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    integration = integrations_db[integration_id]
    if integration.project_id != project_id:
        raise HTTPException(status_code=404, detail="Integration not found in project")
    
    sources = data_sources_db.get(integration_id, [])
    
    # Apply filters
    if type:
        sources = [s for s in sources if s.type == type]
    if search:
        search_lower = search.lower()
        sources = [s for s in sources if search_lower in s.title.lower() or search_lower in s.content_preview.lower()]
    
    total = len(sources)
    sources = sources[offset:offset + limit]
    
    return {
        "sources": sources,
        "total": total
    }

async def perform_integration_sync(integration_id: str, sync_id: str, project_id: str):
    """Background task to perform integration sync"""
    try:
        integration = integrations_db[integration_id]
        sync_result = None
        
        # Find sync result
        for sync in sync_history_db[integration_id]:
            if sync.sync_id == sync_id:
                sync_result = sync
                break
        
        if not sync_result:
            logger.error(f"Sync result not found for sync {sync_id}")
            return
        
        logger.info(f"Starting sync for {integration.type} integration {integration_id}")
        
        start_time = datetime.utcnow()
        documents_processed = 0
        
        # Perform sync based on integration type
        if integration.type == "github":
            # GitHub sync
            integration.sync_progress = 25
            repos = await github_service.get_user_repositories(integration.config.github_token)
            
            integration.sync_progress = 50
            for repo in repos[:5]:  # Limit for demo
                await github_service.scan_repository(
                    integration.config.github_token,
                    repo["full_name"],
                    project_id
                )
                documents_processed += 1
            
        elif integration.type == "jira":
            # Jira sync
            integration.sync_progress = 25
            projects = await jira_service.get_projects(
                integration.config.jira_url,
                integration.config.jira_email,
                integration.config.jira_token
            )
            
            integration.sync_progress = 50
            for project in projects[:3]:  # Limit for demo
                await jira_service.sync_project_data(
                    integration.config.jira_url,
                    integration.config.jira_email,
                    integration.config.jira_token,
                    project["key"],
                    project_id
                )
                documents_processed += 10
            
        elif integration.type == "slack":
            # Slack sync
            integration.sync_progress = 25
            channels = await slack_service.get_channels(integration.config.slack_token)
            
            integration.sync_progress = 50
            for channel in channels[:5]:  # Limit for demo
                await slack_service.get_channel_messages(
                    integration.config.slack_token,
                    channel["id"],
                    project_id
                )
                documents_processed += 20
        
        elif integration.type == "confluence":
            # Confluence sync
            integration.sync_progress = 25
            spaces = await confluence_service.get_spaces(
                integration.config.confluence_url,
                integration.config.confluence_email,
                integration.config.confluence_token,
                integration.config.space_keys
            )
            
            integration.sync_progress = 50
            for space in spaces[:3]:  # Limit for demo
                pages = await confluence_service.get_space_pages(
                    integration.config.confluence_url,
                    integration.config.confluence_email,
                    integration.config.confluence_token,
                    space["key"],
                    project_id,
                    integration.config.include_attachments or False
                )
                documents_processed += len(pages)
        
        # Complete sync
        end_time = datetime.utcnow()
        duration = int((end_time - start_time).total_seconds())
        
        sync_result.status = "completed"
        sync_result.documents_processed = documents_processed
        sync_result.documents_added = documents_processed
        sync_result.duration_seconds = duration
        sync_result.completed_at = end_time
        
        integration.sync_status = "completed"
        integration.sync_progress = 100
        integration.last_sync = end_time
        integration.stats.last_sync_documents = documents_processed
        integration.stats.total_documents += documents_processed
        integration.updated_at = end_time
        
        logger.info(f"Completed sync {sync_id} for integration {integration_id}")
        
    except Exception as e:
        logger.error(f"Sync failed for integration {integration_id}: {str(e)}")
        
        if sync_result:
            sync_result.status = "failed"
            sync_result.error_message = str(e)
            sync_result.completed_at = datetime.utcnow()
        
        integration.sync_status = "failed"
        integration.error_message = str(e)
        integration.updated_at = datetime.utcnow()
