"""
User management routes for NeuroSync API
Handles user profile, settings, and preferences
"""

import logging
from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from models.database import get_db
from models.user_models import User
from middleware.auth import get_current_user
from schemas.auth import UserResponse

# Create logger
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/users", tags=["users"])

def convert_uuid_to_str(user: User):
    user_dict = {
        "id": str(user.id),
        "email": user.email,
        "name": user.name,
        "is_active": user.is_active,
        "is_admin": user.is_admin,
        "created_at": user.created_at
    }
    return user_dict

@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """
    Get current authenticated user profile
    Frontend expects this endpoint to return user information
    """
    logger.info(f"User {current_user.id} requested their profile")
    return convert_uuid_to_str(current_user)

@router.get("/{user_id}", response_model=UserResponse)
async def get_user_by_id(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user by ID (only for admin users or self)
    """
    # Convert string ID to UUID for lookup
    try:
        # Only allow users to view themselves or admins to view anyone
        if str(current_user.id) != user_id and not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this user profile"
            )
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return convert_uuid_to_str(user)
    except Exception as e:
        logger.error(f"Error retrieving user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving user profile"
        )
