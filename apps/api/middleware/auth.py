"""
NeuroSync AI Backend - Authentication Middleware
FastAPI middleware and dependencies for authentication and authorization
"""

import logging
from typing import Optional, Annotated
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from ..database.connection import get_database
from ..services.auth_service import AuthService
from ..models.database import User
from ..models.responses import ErrorResponse

logger = logging.getLogger(__name__)

# Security scheme for JWT tokens
security = HTTPBearer(auto_error=False)

# Initialize auth service
auth_service = AuthService()

class AuthenticationError(HTTPException):
    """Custom authentication error"""
    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )

class AuthorizationError(HTTPException):
    """Custom authorization error"""
    def __init__(self, detail: str = "Insufficient permissions"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
        )

async def get_current_user(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security)],
    db: Annotated[Session, Depends(get_database)]
) -> User:
    """
    FastAPI dependency to get the current authenticated user from JWT token
    """
    if not credentials:
        raise AuthenticationError("Missing authentication token")
    
    token = credentials.credentials
    user = auth_service.get_user_from_token(token, db)
    
    if not user:
        raise AuthenticationError("Invalid or expired token")
    
    if not user.is_active:
        raise AuthenticationError("User account is deactivated")
    
    return user

async def get_current_user_optional(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security)],
    db: Annotated[Session, Depends(get_database)]
) -> Optional[User]:
    """
    FastAPI dependency to optionally get the current user (for public endpoints)
    """
    if not credentials:
        return None
    
    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None

async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    """
    FastAPI dependency to get current active and verified user
    """
    if not current_user.is_active:
        raise AuthenticationError("User account is deactivated")
    
    return current_user

async def get_current_verified_user(
    current_user: Annotated[User, Depends(get_current_active_user)]
) -> User:
    """
    FastAPI dependency to get current verified user
    """
    if not current_user.is_verified:
        raise AuthenticationError("Email verification required")
    
    return current_user

async def get_api_key_user(
    request: Request,
    db: Annotated[Session, Depends(get_database)]
) -> Optional[User]:
    """
    FastAPI dependency to authenticate user via API key
    """
    # Check for API key in headers
    api_key = request.headers.get("X-API-Key")
    if not api_key:
        return None
    
    user = auth_service.verify_api_key(api_key, db)
    if not user:
        raise AuthenticationError("Invalid API key")
    
    if not user.is_active:
        raise AuthenticationError("User account is deactivated")
    
    return user

async def get_user_from_token_or_api_key(
    jwt_user: Annotated[Optional[User], Depends(get_current_user_optional)],
    api_user: Annotated[Optional[User], Depends(get_api_key_user)]
) -> User:
    """
    FastAPI dependency to get user from either JWT token or API key
    """
    user = jwt_user or api_user
    if not user:
        raise AuthenticationError("Authentication required")
    
    return user

def require_subscription_tier(required_tier: str):
    """
    Factory function to create a dependency that requires a specific subscription tier
    """
    tier_hierarchy = {
        "starter": 1,
        "professional": 2,
        "enterprise": 3
    }
    
    async def check_subscription_tier(
        current_user: Annotated[User, Depends(get_current_verified_user)]
    ) -> User:
        user_tier_level = tier_hierarchy.get(current_user.subscription_tier, 0)
        required_tier_level = tier_hierarchy.get(required_tier, 999)
        
        if user_tier_level < required_tier_level:
            raise AuthorizationError(
                f"This feature requires {required_tier} subscription or higher"
            )
        
        return current_user
    
    return check_subscription_tier

def require_project_permission(permission: str):
    """
    Factory function to create a dependency that requires specific project permission
    """
    async def check_project_permission(
        project_id: str,
        current_user: Annotated[User, Depends(get_current_verified_user)],
        db: Annotated[Session, Depends(get_database)]
    ) -> User:
        has_permission = auth_service.check_user_permissions(
            current_user, project_id, permission, db
        )
        
        if not has_permission:
            raise AuthorizationError(
                f"Insufficient permissions for project. Required: {permission}"
            )
        
        return current_user
    
    return check_project_permission

def require_api_key_scope(scope: str):
    """
    Factory function to create a dependency that requires specific API key scope
    """
    async def check_api_key_scope(
        request: Request,
        db: Annotated[Session, Depends(get_database)]
    ) -> bool:
        api_key = request.headers.get("X-API-Key")
        if not api_key:
            raise AuthenticationError("API key required for this endpoint")
        
        has_scope = auth_service.check_api_key_scope(api_key, scope, db)
        if not has_scope:
            raise AuthorizationError(f"API key missing required scope: {scope}")
        
        return True
    
    return check_api_key_scope

async def check_token_balance(
    tokens_needed: int,
    current_user: Annotated[User, Depends(get_current_verified_user)],
    db: Annotated[Session, Depends(get_database)]
) -> User:
    """
    FastAPI dependency to check if user has sufficient token balance
    """
    if not current_user.can_use_tokens(tokens_needed):
        raise AuthorizationError(
            f"Insufficient token balance. Required: {tokens_needed}, "
            f"Available: {current_user.tokens_remaining}"
        )
    
    return current_user

def create_token_usage_dependency(estimated_tokens: int):
    """
    Factory function to create a dependency that checks and reserves tokens
    """
    async def check_and_reserve_tokens(
        current_user: Annotated[User, Depends(get_current_verified_user)],
        db: Annotated[Session, Depends(get_database)]
    ) -> User:
        return await check_token_balance(estimated_tokens, current_user, db)
    
    return check_and_reserve_tokens

async def check_rate_limit(
    request: Request,
    current_user: Annotated[User, Depends(get_current_user_optional)]
) -> bool:
    """
    FastAPI dependency to check rate limits
    """
    user_id = str(current_user.id) if current_user else request.client.host
    endpoint = f"{request.method}:{request.url.path}"
    
    # Check rate limit (this would integrate with Redis in production)
    is_allowed = auth_service.check_rate_limit(user_id, endpoint)
    
    if not is_allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later."
        )
    
    return True

class ProjectAccessChecker:
    """Helper class for checking project access permissions"""
    
    def __init__(self, permission: str = "read"):
        self.permission = permission
    
    async def __call__(
        self,
        project_id: str,
        current_user: Annotated[User, Depends(get_current_verified_user)],
        db: Annotated[Session, Depends(get_database)]
    ) -> User:
        has_permission = auth_service.check_user_permissions(
            current_user, project_id, self.permission, db
        )
        
        if not has_permission:
            raise AuthorizationError(
                f"Access denied to project {project_id}. Required permission: {self.permission}"
            )
        
        return current_user

# Common permission checkers
require_project_read = ProjectAccessChecker("read")
require_project_write = ProjectAccessChecker("write")
require_project_admin = ProjectAccessChecker("admin")

# Subscription tier checkers
require_professional = require_subscription_tier("professional")
require_enterprise = require_subscription_tier("enterprise")

# Token usage checkers for common operations
require_query_tokens = create_token_usage_dependency(10)  # Estimated tokens for AI query
require_ingestion_tokens = create_token_usage_dependency(5)  # Estimated tokens for data ingestion
require_analysis_tokens = create_token_usage_dependency(15)  # Estimated tokens for analysis

async def log_api_usage(
    request: Request,
    current_user: Annotated[Optional[User], Depends(get_current_user_optional)]
):
    """
    Middleware dependency to log API usage for analytics
    """
    # Log API usage (this would integrate with your analytics system)
    logger.info(
        f"API Usage: {request.method} {request.url.path} "
        f"User: {current_user.id if current_user else 'anonymous'}"
    )
    
    return True
