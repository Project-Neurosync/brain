"""
Authentication routes for NeuroSync API
Handles user registration, login, and profile management
"""

from datetime import datetime, timedelta
from typing import Optional
import logging

from fastapi import APIRouter, Depends, HTTPException, status, Response, Cookie
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import uuid

from models.database import get_db
from models.user_models import User
from middleware.auth import (
    get_current_user, 
    get_password_hash, 
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_token
)
from core.settings import settings
from schemas.auth import (
    UserCreate, 
    UserResponse, 
    TokenResponse, 
    LoginResponse
)

# Create logger
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate, 
    response: Response,
    db: Session = Depends(get_db)
):
    """
    Register a new user and set JWT token in HTTP-only cookie
    """
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    new_user = User(
        id=uuid.uuid4(),
        email=user_data.email,
        name=user_data.name,
        password_hash=get_password_hash(user_data.password),
    )
    
    # Save to database
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Create access token
    token_data = {"sub": str(new_user.id), "email": new_user.email}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    
    # Set cookie
    expires = datetime.utcnow() + timedelta(days=7)
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        secure=True,  # Set to True in production
        samesite="lax",
        expires=expires.strftime("%a, %d %b %Y %H:%M:%S GMT"),
    )
    
    # Return user data
    return {
        "id": str(new_user.id),
        "email": new_user.email,
        "name": new_user.name,
        "is_active": new_user.is_active,
        "is_admin": new_user.is_admin,
        "created_at": new_user.created_at,
    }

@router.post("/login", response_model=LoginResponse)
async def login_user(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Authenticate user and set JWT token in HTTP-only cookie
    """
    # Add debug logging
    logger.info(f"Login attempt for user: {form_data.username}")
    
    # Find user by email
    user = db.query(User).filter(User.email == form_data.username).first()
    
    # Add more debug logging
    if not user:
        logger.error(f"User not found: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check password
    if not verify_password(form_data.password, user.password_hash):
        logger.error(f"Invalid password for user: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active
    if not user.is_active:
        logger.error(f"Inactive user attempt to login: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    
    # Create access token
    token_data = {"sub": str(user.id), "email": user.email}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    
    # Set cookie
    expires = datetime.utcnow() + timedelta(days=7)
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        secure=True,  # Set to True in production
        samesite="lax",
        expires=expires.strftime("%a, %d %b %Y %H:%M:%S GMT"),
    )
    
    # Log response data to debug validation errors
    response_data = {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": str(user.id),
            "email": user.email,
            "name": user.name,
            "is_active": user.is_active,
            "is_admin": user.is_admin,
        }
    }
    
    logger.info(f"Login successful for user: {form_data.username}")
    logger.debug(f"Response data types: id={type(user.id)}, email={type(user.email)}, name={type(user.name)}")
    logger.debug(f"Response structure: {response_data}")
    
    # Return token data
    return response_data

@router.post("/logout")
async def logout_user(response: Response):
    """
    Logout user by clearing JWT cookie
    """
    response.delete_cookie(
        key="access_token",
        httponly=True,
        secure=True,
        samesite="lax",
    )
    return {"message": "Successfully logged out"}

@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """
    Get current user profile
    """
    return {
        "id": current_user.id,
        "email": current_user.email,
        "name": current_user.name,
        "is_active": current_user.is_active,
        "is_admin": current_user.is_admin,
        "created_at": current_user.created_at,
    }

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    response: Response,
    refresh_token: str,
    db: Session = Depends(get_db)
):
    """
    Refresh access token using refresh token
    """
    try:
        # Decode and verify the refresh token
        payload = verify_token(refresh_token)
        user_id = payload.get("sub")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
            
        # Get user from database
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
            
        # Get user session
        session = db.query(UserSession).filter(
            UserSession.user_id == user_id,
            UserSession.refresh_token == refresh_token
        ).first()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid session"
            )
        
        # Create new access token
        access_token = create_access_token({"sub": user_id, "email": user.email})
        
        # Set cookie with new token
        expires = datetime.utcnow() + timedelta(days=7)
        response.set_cookie(
            key="access_token",
            value=f"Bearer {access_token}",
            httponly=True,
            secure=True,
            samesite="lax",
            expires=expires.strftime("%a, %d %b %Y %H:%M:%S GMT"),
        )
        
        # Update session last used timestamp
        session.last_used = datetime.utcnow()
        db.commit()
        
        return {"access_token": access_token, "token_type": "bearer"}
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
