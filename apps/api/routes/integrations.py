"""
Integration management routes for NeuroSync API
Handles third-party service integrations (GitHub, Slack, Jira, Confluence, Notion)
"""

import logging
import secrets
import httpx
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, ConfigDict

from core.settings import settings

from models.database import get_db
from models.user_models import User
from models.integration import Integration
from models.project import Project
from middleware.auth import get_current_user

# Create logger
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/integrations", tags=["integrations"])

# Define response schemas
class IntegrationBase(BaseModel):
    type: str
    status: str
    config: Optional[Dict[str, Any]] = None
    
    model_config = ConfigDict(from_attributes=True)


class IntegrationCreate(IntegrationBase):
    project_id: UUID
    name: Optional[str] = None


class IntegrationUpdate(BaseModel):
    name: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    status: Optional[str] = None
    is_active: Optional[bool] = None
    auto_sync: Optional[bool] = None


class IntegrationResponse(IntegrationBase):
    id: UUID
    project_id: Optional[UUID] = None
    name: Optional[str] = None
    error_message: Optional[str] = None
    last_sync: Optional[datetime] = None
    last_sync_status: Optional[str] = None
    next_scheduled_sync: Optional[datetime] = None
    is_active: bool
    auto_sync: bool
    created_at: datetime
    updated_at: datetime


class IntegrationType(BaseModel):
    id: str
    name: str
    description: str
    icon: str


class ConnectIntegrationRequest(BaseModel):
    project_id: UUID
    config: Dict[str, Any]
    name: Optional[str] = None


# Endpoint to get all integrations for current user
@router.get("/", response_model=List[IntegrationResponse])
async def get_integrations(
    project_id: Optional[UUID] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all integrations for the current authenticated user
    If project_id is specified, only return integrations for that project
    """
    try:
        logger.info(f"Fetching integrations for user: {current_user.email}")
        
        query = db.query(Integration).join(Project).filter(Project.user_id == current_user.id)
        
        # Filter by project if specified
        if project_id:
            query = query.filter(Integration.project_id == project_id)
        
        integrations = query.all()
        return integrations
        
    except Exception as e:
        logger.error(f"Error fetching integrations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve integrations: {str(e)}"
        )


# Endpoint to get all user integrations (including projectless ones)
@router.get("/user", response_model=List[IntegrationResponse])
async def get_user_integrations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all integrations for the current user, including projectless integrations
    """
    
    try:
        # Get all integrations for this user
        integrations = db.query(Integration).filter(
            Integration.user_id == current_user.id
        ).all()
        
        logger.info(f"Found {len(integrations)} integrations for user {current_user.id}")
        return integrations
    except Exception as e:
        logger.error(f"Error fetching user integrations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch integrations: {str(e)}"
        )


@router.get("/types", response_model=List[IntegrationType])
async def get_integration_types(
    current_user: User = Depends(get_current_user)
):
    """
    Get all available integration types
    """
    try:
        # Define standard integration types
        # Check if GitHub OAuth is properly configured
        logger.info(f"Checking GitHub OAuth configuration...")
        logger.info(f"GITHUB_CLIENT_ID present: {bool(settings.GITHUB_CLIENT_ID)}")
        logger.info(f"GITHUB_CLIENT_SECRET present: {bool(settings.GITHUB_CLIENT_SECRET)}")
        
        # Debug the actual values (be careful with secrets in logs)
        if settings.GITHUB_CLIENT_ID:
            logger.info(f"GITHUB_CLIENT_ID: {settings.GITHUB_CLIENT_ID[:4]}...{settings.GITHUB_CLIENT_ID[-4:] if len(settings.GITHUB_CLIENT_ID) > 8 else ''}")
        else:
            logger.warning("GITHUB_CLIENT_ID is not set")
            
        if settings.GITHUB_CLIENT_SECRET:
            logger.info(f"GITHUB_CLIENT_SECRET length: {len(settings.GITHUB_CLIENT_SECRET)}")
        else:
            logger.warning("GITHUB_CLIENT_SECRET is not set")
            
        github_oauth_configured = bool(settings.GITHUB_CLIENT_ID and settings.GITHUB_CLIENT_SECRET)
        logger.info(f"GitHub OAuth configured: {github_oauth_configured}")
        
        # This is configuration data that doesn't need to be in the database
        integration_types = [
            {
                "id": "github",
                "name": "GitHub",
                "description": "Connect your GitHub repositories to analyze code and track development activity.",
                "icon": "github",
                "oauth_supported": github_oauth_configured
            },
            
            {
                "id": "slack",
                "name": "Slack",
                "description": "Connect your Slack workspace to analyze team communication and knowledge sharing.",
                "icon": "slack"
            },
            {
                "id": "jira",
                "name": "Jira",
                "description": "Connect your Jira projects to track issues, tasks, and project progress.",
                "icon": "jira"
            },
            {
                "id": "confluence",
                "name": "Confluence",
                "description": "Connect your Confluence workspace to extract documentation and knowledge base content.",
                "icon": "confluence"
            },
            {
                "id": "notion",
                "name": "Notion",
                "description": "Connect your Notion workspace to extract notes, documents, and team knowledge.",
                "icon": "notion"
            }
        ]
        
        # Final logging to trace what's being sent to frontend
        github_type = next((t for t in integration_types if t["id"] == "github"), None)
        logger.info(f"Final GitHub integration configuration: {github_type}")
        
        return integration_types
    except Exception as e:
        logger.error(f"Error fetching integration types: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve integration types: {str(e)}"
        )


# GitHub OAuth endpoints

# Project-specific OAuth flow
@router.post("/projects/{project_id}/integrations/oauth/start", response_model=dict)
async def start_oauth_flow(
    project_id: UUID,
    oauth_data: dict = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Start OAuth flow for GitHub integration with project context
    """
    try:
        # Verify project ownership
        project = db.query(Project).filter(
            Project.id == project_id,
            Project.user_id == current_user.id
        ).first()
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project not found or you don't have access"
            )
        
        integration_type = oauth_data.get("type")
        redirect_url = oauth_data.get("redirect_url")
        
        if integration_type != "github":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"OAuth not supported for {integration_type}"
            )
        
        if not redirect_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="redirect_url is required"
            )
        
        # GitHub OAuth configuration from settings
        client_id = settings.GITHUB_CLIENT_ID
        
        if not client_id:
            logger.error("GitHub OAuth client ID not configured")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="GitHub OAuth is not properly configured"
            )
        
        # Generate a secure state parameter to prevent CSRF
        state = secrets.token_hex(16)
        
        # Store state in database or cache for validation later
        # For now we'll just use a simple in-memory approach
        # In production, use Redis or database to store state with expiry
        
        # Build GitHub authorization URL
        auth_url = f"https://github.com/login/oauth/authorize?client_id={client_id}&redirect_uri={redirect_url}&state={state}&scope=repo"
        
        return {
            "auth_url": auth_url,
            "state": state
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting OAuth flow: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start OAuth flow: {str(e)}"
        )


# Projectless OAuth flow (for new project creation)
@router.post("/oauth/start", response_model=dict)
async def start_projectless_oauth_flow(
    oauth_data: dict = Body(...),
    current_user: User = Depends(get_current_user)
):
    """
    Start OAuth flow without requiring a project ID (for project creation flow)
    """
    try:
        integration_type = oauth_data.get("integration_type")
        redirect_url = oauth_data.get("redirect_url")
        
        if integration_type != "github":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"OAuth not supported for {integration_type}"
            )
        
        if not redirect_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="redirect_url is required"
            )
        
        # GitHub OAuth configuration from settings
        client_id = settings.GITHUB_CLIENT_ID
        
        if not client_id:
            logger.error("GitHub OAuth client ID not configured")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="GitHub OAuth is not properly configured"
            )
        
        # Generate a secure state parameter to prevent CSRF
        state = secrets.token_hex(16)
        
        # Store state with user ID for validation later
        # In production, use Redis or database with expiry
        # Here we'd store: state -> {user_id: current_user.id, integration_type: integration_type}
        
        # Build GitHub authorization URL
        auth_url = f"https://github.com/login/oauth/authorize?client_id={client_id}&redirect_uri={redirect_url}&state={state}&scope=repo"
        
        return {
            "auth_url": auth_url,
            "state": state
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting projectless OAuth flow: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start OAuth flow: {str(e)}"
        )


@router.post("/projects/{project_id}/integrations/oauth/complete", response_model=dict)
async def complete_oauth_flow(
    project_id: UUID,
    completion_data: dict = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Complete OAuth flow for GitHub integration with project context
    """
    try:
        # Verify project ownership
        project = db.query(Project).filter(
            Project.id == project_id,
            Project.user_id == current_user.id
        ).first()
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project not found or you don't have access"
            )
        
        code = completion_data.get("code")
        state = completion_data.get("state")
        
        if not code or not state:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="code and state parameters are required"
            )
        
        # Verify state parameter matches what we sent (anti-CSRF)
        # In production, verify against Redis/database stored state
        
        # Exchange code for access token using settings
        client_id = settings.GITHUB_CLIENT_ID
        client_secret = settings.GITHUB_CLIENT_SECRET
        
        if not client_id or not client_secret:
            logger.error("GitHub OAuth client ID or secret not configured")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="GitHub OAuth is not properly configured"
            )
        
        token_url = "https://github.com/login/oauth/access_token"
        payload = {
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code,
            "redirect_uri": settings.GITHUB_REDIRECT_URI,  # Should match the redirect URL used in start
        }
        headers = {"Accept": "application/json"}
        
        # Make request to GitHub for access token
        async with httpx.AsyncClient() as client:
            response = await client.post(token_url, json=payload, headers=headers)
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Failed to exchange code for access token: {response.text}"
                )
            
            token_data = response.json()
            access_token = token_data.get("access_token")
            
            if not access_token:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No access token received from GitHub"
                )
            
            # Test the token by getting user info
            user_response = await client.get(
                "https://api.github.com/user",
                headers={
                    "Authorization": f"token {access_token}",
                    "Accept": "application/vnd.github.v3+json"
                }
            )
            
            if user_response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid GitHub token: {user_response.text}"
                )
            
            user_data = user_response.json()
            
            # Create or update GitHub integration
            existing_integration = db.query(Integration).filter(
                Integration.project_id == project_id,
                Integration.type == "github"
            ).first()
            
            integration_config = {
                "github_token": access_token,
                "username": user_data.get("login"),
                "include_issues": True,
                "include_prs": True
            }
            
            if existing_integration:
                # Update existing integration
                existing_integration.status = "connected"
                existing_integration.config = integration_config
                existing_integration.name = f"GitHub ({user_data.get('login')})"
                existing_integration.updated_at = datetime.utcnow()
                db.commit()
                db.refresh(existing_integration)
                
                return {
                    "access_token": access_token,
                    "integration_config": integration_config
                }
            
            # Create new integration
            new_integration = Integration(
                user_id=current_user.id,  # Add user_id from current_user
                project_id=project_id,
                type="github",
                status="connected",
                name=f"GitHub ({user_data.get('login')})",
                config=integration_config
            )
            
            db.add(new_integration)
            db.commit()
            db.refresh(new_integration)
            
            return {
                "access_token": access_token,
                "integration_config": integration_config
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error completing OAuth flow: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to complete OAuth flow: {str(e)}"
        )


@router.post("/oauth/complete", response_model=dict)
async def complete_projectless_oauth_flow(
    completion_data: dict = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Complete OAuth flow without requiring a project ID (for project creation flow)
    """
    try:
        code = completion_data.get("code")
        state = completion_data.get("state")
        integration_type = completion_data.get("integration_type", "github")
        
        if not code or not state:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="code and state parameters are required"
            )
        
        if integration_type != "github":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"OAuth not supported for {integration_type}"
            )
            
        # Verify state parameter matches what we sent (anti-CSRF)
        # In production, verify against Redis/database stored state
        
        # Exchange code for access token using settings
        client_id = settings.GITHUB_CLIENT_ID
        client_secret = settings.GITHUB_CLIENT_SECRET
        
        if not client_id or not client_secret:
            logger.error("GitHub OAuth client ID or secret not configured")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="GitHub OAuth is not properly configured"
            )
        
        token_url = "https://github.com/login/oauth/access_token"
        payload = {
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code,
        }
        headers = {"Accept": "application/json"}
        
        # Make request to GitHub for access token
        async with httpx.AsyncClient() as client:
            response = await client.post(token_url, json=payload, headers=headers)
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Failed to exchange code for access token: {response.text}"
                )
            
            token_data = response.json()
            access_token = token_data.get("access_token")
            
            if not access_token:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No access token received from GitHub"
                )
            
            # Test the token by getting user info
            user_response = await client.get(
                "https://api.github.com/user",
                headers={
                    "Authorization": f"token {access_token}",
                    "Accept": "application/vnd.github.v3+json"
                }
            )
            
            if user_response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid GitHub token: {user_response.text}"
                )
            
            user_data = user_response.json()
            
            # Create config and save integration to database immediately (without project ID)
            integration_config = {
                "github_token": access_token,
                "username": user_data.get("login"),
                "include_issues": True,
                "include_prs": True
            }
            
            # Create and save the integration to the database
            new_integration = Integration(
                user_id=current_user.id,  # Add user_id from current_user
                type="github",  # hardcoded for now
                name=f"GitHub ({user_data.get('login')})",
                config=integration_config,
                status="connected"
            )
            
            db.add(new_integration)
            db.commit()
            db.refresh(new_integration)
            
            logger.info(f"Created projectless integration for user {current_user.id}: {new_integration.id}")
            
            # Return the token, config, and integration ID
            return {
                "access_token": access_token,
                "integration_config": integration_config,
                "integration_id": new_integration.id,
                "user_data": {
                    "username": user_data.get("login"),
                    "name": user_data.get("name"),
                    "avatar_url": user_data.get("avatar_url")
                }
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error completing projectless OAuth flow: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to complete OAuth flow: {str(e)}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error completing OAuth flow: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to complete OAuth flow: {str(e)}"
        )



@router.post("/{integration_type}/connect", response_model=IntegrationResponse)
async def connect_integration(
    integration_type: str,
    connect_data: ConnectIntegrationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Connect an integration for a project
    """
    try:
        logger.info(f"Connecting {integration_type} for user: {current_user.email}, project: {connect_data.project_id}")
        
        # Check if integration type is valid
        valid_types = ["github", "slack", "jira", "confluence", "notion"]
        if integration_type not in valid_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid integration type: {integration_type}"
            )
        
        # Verify project exists and belongs to user
        project = db.query(Project).filter(
            Project.id == connect_data.project_id,
            Project.user_id == current_user.id
        ).first()
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project not found or you don't have access"
            )
        
        # Check if integration already exists for this project
        existing_integration = db.query(Integration).filter(
            Integration.project_id == connect_data.project_id,
            Integration.type == integration_type
        ).first()
        
        if existing_integration:
            # Update existing integration
            existing_integration.status = "connected"
            existing_integration.config = connect_data.config
            existing_integration.name = connect_data.name
            existing_integration.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(existing_integration)
            
            return existing_integration
        
        # Create new integration
        new_integration = Integration(
            user_id=current_user.id,  # Add user_id from current_user
            project_id=connect_data.project_id,
            type=integration_type,
            status="connected",
            name=connect_data.name,
            config=connect_data.config
        )
        
        db.add(new_integration)
        db.commit()
        db.refresh(new_integration)
        
        return new_integration
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error connecting {integration_type}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to connect {integration_type}: {str(e)}"
        )


@router.get("/{integration_id}", response_model=IntegrationResponse)
async def get_integration(
    integration_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get integration details by ID
    """
    try:
        # Query for integration and verify ownership
        integration = db.query(Integration).join(Project).filter(
            Integration.id == integration_id,
            Project.user_id == current_user.id
        ).first()
        
        if not integration:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Integration not found or you don't have access"
            )
        
        return integration
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching integration {integration_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve integration: {str(e)}"
        )
