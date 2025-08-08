"""
Project management routes for NeuroSync API
Handles project creation, retrieval, and updates
"""

import logging
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from models.database import get_db
from models.user_models import User
from models.project import Project
from middleware.auth import get_current_user
from pydantic import BaseModel, Field, ConfigDict

# Create logger
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/projects", tags=["projects"])

# Define response schemas
class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None
    status: str
    progress: int


class ProjectResponse(ProjectBase):
    id: str
    user_id: str
    created_at: str
    updated_at: str
    
    model_config = {"from_attributes": True}


class ProjectCreate(ProjectBase):
    pass


# Endpoint to get all projects for current user
@router.get("/", response_model=List[ProjectResponse])
async def get_projects(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all projects for the current authenticated user
    """
    try:
        logger.info(f"Fetching projects for user: {current_user.email}")
        
        # Query projects for current user
        projects = db.query(Project).filter(Project.user_id == current_user.id).all()
        
        # Convert UUIDs to strings for proper serialization
        result = []
        for project in projects:
            result.append({
                "id": str(project.id),
                "name": project.name,
                "description": project.description,
                "status": project.status,
                "progress": project.progress,
                "user_id": str(project.user_id),
                "created_at": project.created_at.isoformat(),
                "updated_at": project.updated_at.isoformat()
            })
        
        return result
        
    except Exception as e:
        logger.error(f"Error fetching projects: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve projects: {str(e)}"
        )

# Endpoint to create a new project
@router.post("/", response_model=ProjectResponse)
async def create_project(
    project_data: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new project for the current authenticated user
    """
    try:
        logger.info(f"Creating project for user: {current_user.email}")
        logger.info(f"Project data: {project_data}")
        
        # Create new project
        new_project = Project(
            name=project_data.name,
            description=project_data.description,
            status=project_data.status or "active",
            progress=project_data.progress or 0,
            user_id=current_user.id
        )
        
        # Add to database
        db.add(new_project)
        db.commit()
        db.refresh(new_project)
        
        logger.info(f"Created project with ID: {new_project.id}")
        
        # Return project data
        return {
            "id": str(new_project.id),
            "name": new_project.name,
            "description": new_project.description,
            "status": new_project.status,
            "progress": new_project.progress,
            "user_id": str(new_project.user_id),
            "created_at": new_project.created_at.isoformat(),
            "updated_at": new_project.updated_at.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error creating project: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create project: {str(e)}"
        )
