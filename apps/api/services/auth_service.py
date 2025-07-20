"""
NeuroSync AI Backend - Authentication Service
Handles JWT tokens, user authentication, and authorization
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List
import jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
import secrets
import hashlib

from ..models.database import User, APIKey
from ..config.settings import get_settings

logger = logging.getLogger(__name__)

class AuthService:
    """Service for handling authentication and authorization"""
    
    def __init__(self):
        self.settings = get_settings()
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
    def create_access_token(self, user_id: str, expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token for a user"""
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(hours=self.settings.jwt_expiration_hours)
        
        to_encode = {
            "sub": str(user_id),
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "access_token"
        }
        
        encoded_jwt = jwt.encode(
            to_encode, 
            self.settings.secret_key, 
            algorithm=self.settings.jwt_algorithm
        )
        return encoded_jwt
    
    def create_refresh_token(self, user_id: str) -> str:
        """Create a refresh token for a user"""
        expire = datetime.now(timezone.utc) + timedelta(days=30)  # Refresh tokens last 30 days
        
        to_encode = {
            "sub": str(user_id),
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "refresh_token"
        }
        
        encoded_jwt = jwt.encode(
            to_encode, 
            self.settings.secret_key, 
            algorithm=self.settings.jwt_algorithm
        )
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode a JWT token"""
        try:
            payload = jwt.decode(
                token, 
                self.settings.secret_key, 
                algorithms=[self.settings.jwt_algorithm]
            )
            
            # Check if token is expired
            exp = payload.get("exp")
            if exp and datetime.fromtimestamp(exp, tz=timezone.utc) < datetime.now(timezone.utc):
                logger.warning("Token has expired")
                return None
            
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            return None
        except jwt.JWTError as e:
            logger.warning(f"JWT decode error: {str(e)}")
            return None
    
    def get_user_from_token(self, token: str, db: Session) -> Optional[User]:
        """Get user from JWT token"""
        payload = self.verify_token(token)
        if not payload:
            return None
        
        user_id = payload.get("sub")
        if not user_id:
            return None
        
        user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
        if user:
            # Update last active timestamp
            user.last_active_at = datetime.now(timezone.utc)
            db.commit()
        
        return user
    
    def authenticate_user(self, email: str, password: str, db: Session) -> Optional[User]:
        """Authenticate user with email and password (for custom auth)"""
        # This would be used if implementing custom authentication
        # For Auth0/external providers, this might not be needed
        user = db.query(User).filter(User.email == email, User.is_active == True).first()
        if not user:
            return None
        
        # For external auth providers, we might store a hash of the provider ID
        # instead of a password
        return user
    
    def create_or_update_user_from_auth0(
        self, 
        auth0_user_data: Dict[str, Any], 
        db: Session
    ) -> User:
        """Create or update user from Auth0 user data"""
        auth0_id = auth0_user_data.get("sub")
        email = auth0_user_data.get("email")
        name = auth0_user_data.get("name", "")
        avatar_url = auth0_user_data.get("picture")
        is_verified = auth0_user_data.get("email_verified", False)
        
        # Check if user already exists
        user = db.query(User).filter(User.auth_provider_id == auth0_id).first()
        
        if user:
            # Update existing user
            user.email = email
            user.name = name
            user.avatar_url = avatar_url
            user.is_verified = is_verified
            user.last_active_at = datetime.now(timezone.utc)
        else:
            # Create new user
            user = User(
                email=email,
                name=name,
                avatar_url=avatar_url,
                auth_provider="auth0",
                auth_provider_id=auth0_id,
                is_verified=is_verified,
                subscription_tier="starter",  # Default tier
                tokens_remaining=100,  # Default starter allocation
                last_active_at=datetime.now(timezone.utc)
            )
            db.add(user)
        
        db.commit()
        db.refresh(user)
        return user
    
    def check_user_permissions(
        self, 
        user: User, 
        project_id: str, 
        required_permission: str,
        db: Session
    ) -> bool:
        """Check if user has required permission for a project"""
        from ..models.database import Project, project_members
        
        # Check if user is project owner
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return False
        
        if str(project.owner_id) == str(user.id):
            return True  # Owner has all permissions
        
        # Check if user is a member with required permissions
        member_query = db.query(project_members).filter(
            project_members.c.project_id == project_id,
            project_members.c.user_id == user.id
        ).first()
        
        if not member_query:
            return False  # User is not a member
        
        # Check role-based permissions
        role = member_query.role
        permissions = member_query.permissions or []
        
        # Define role permissions
        role_permissions = {
            "viewer": ["read"],
            "editor": ["read", "write", "comment"],
            "admin": ["read", "write", "comment", "manage", "invite"]
        }
        
        allowed_permissions = role_permissions.get(role, []) + permissions
        return required_permission in allowed_permissions
    
    def generate_api_key(self, user_id: str, name: str, scopes: List[str], db: Session) -> Dict[str, str]:
        """Generate a new API key for a user"""
        # Generate a secure random key
        key = f"ns_{secrets.token_urlsafe(32)}"
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        key_prefix = key[:12]  # First 12 characters for identification
        
        # Create API key record
        api_key = APIKey(
            user_id=user_id,
            name=name,
            key_hash=key_hash,
            key_prefix=key_prefix,
            scopes=scopes
        )
        
        db.add(api_key)
        db.commit()
        db.refresh(api_key)
        
        return {
            "key": key,
            "key_id": str(api_key.id),
            "prefix": key_prefix
        }
    
    def verify_api_key(self, api_key: str, db: Session) -> Optional[User]:
        """Verify an API key and return the associated user"""
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        api_key_record = db.query(APIKey).filter(
            APIKey.key_hash == key_hash,
            APIKey.is_active == True
        ).first()
        
        if not api_key_record:
            return None
        
        # Check if key is expired
        if api_key_record.expires_at and api_key_record.expires_at < datetime.now(timezone.utc):
            return None
        
        # Update usage tracking
        api_key_record.last_used_at = datetime.now(timezone.utc)
        api_key_record.usage_count += 1
        db.commit()
        
        # Get the user
        user = db.query(User).filter(
            User.id == api_key_record.user_id,
            User.is_active == True
        ).first()
        
        return user
    
    def check_api_key_scope(self, api_key: str, required_scope: str, db: Session) -> bool:
        """Check if an API key has the required scope"""
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        api_key_record = db.query(APIKey).filter(
            APIKey.key_hash == key_hash,
            APIKey.is_active == True
        ).first()
        
        if not api_key_record:
            return False
        
        return required_scope in (api_key_record.scopes or [])
    
    def revoke_api_key(self, key_id: str, user_id: str, db: Session) -> bool:
        """Revoke an API key"""
        api_key = db.query(APIKey).filter(
            APIKey.id == key_id,
            APIKey.user_id == user_id
        ).first()
        
        if not api_key:
            return False
        
        api_key.is_active = False
        db.commit()
        return True
    
    def check_rate_limit(self, user_id: str, endpoint: str) -> bool:
        """Check if user has exceeded rate limits"""
        # This would integrate with Redis to track rate limits
        # For now, return True (no rate limiting)
        # In production, implement proper rate limiting logic
        return True
    
    def get_user_subscription_limits(self, user: User) -> Dict[str, int]:
        """Get subscription limits for a user"""
        limits = {
            "starter": {
                "max_projects": 3,
                "max_members_per_project": 5,
                "max_documents_per_project": 1000,
                "max_queries_per_month": 500,
                "max_storage_gb": 1
            },
            "professional": {
                "max_projects": 10,
                "max_members_per_project": 15,
                "max_documents_per_project": 5000,
                "max_queries_per_month": 2000,
                "max_storage_gb": 10
            },
            "enterprise": {
                "max_projects": -1,  # Unlimited
                "max_members_per_project": -1,  # Unlimited
                "max_documents_per_project": -1,  # Unlimited
                "max_queries_per_month": -1,  # Unlimited
                "max_storage_gb": -1  # Unlimited
            }
        }
        
        return limits.get(user.subscription_tier, limits["starter"])
    
    def check_subscription_limit(
        self, 
        user: User, 
        limit_type: str, 
        current_count: int
    ) -> bool:
        """Check if user has exceeded a subscription limit"""
        limits = self.get_user_subscription_limits(user)
        limit_value = limits.get(limit_type, 0)
        
        # -1 means unlimited
        if limit_value == -1:
            return True
        
        return current_count < limit_value
    
    def hash_password(self, password: str) -> str:
        """Hash a password for storage"""
        return self.pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def create_password_reset_token(self, user_id: str) -> str:
        """Create a password reset token"""
        expire = datetime.now(timezone.utc) + timedelta(hours=1)  # Reset tokens expire in 1 hour
        
        to_encode = {
            "sub": str(user_id),
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "password_reset"
        }
        
        encoded_jwt = jwt.encode(
            to_encode, 
            self.settings.secret_key, 
            algorithm=self.settings.jwt_algorithm
        )
        return encoded_jwt
    
    def verify_password_reset_token(self, token: str) -> Optional[str]:
        """Verify a password reset token and return user ID"""
        payload = self.verify_token(token)
        if not payload:
            return None
        
        if payload.get("type") != "password_reset":
            return None
        
        return payload.get("sub")
    
    def create_email_verification_token(self, user_id: str) -> str:
        """Create an email verification token"""
        expire = datetime.now(timezone.utc) + timedelta(days=7)  # Verification tokens expire in 7 days
        
        to_encode = {
            "sub": str(user_id),
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "email_verification"
        }
        
        encoded_jwt = jwt.encode(
            to_encode, 
            self.settings.secret_key, 
            algorithm=self.settings.jwt_algorithm
        )
        return encoded_jwt
    
    def verify_email_verification_token(self, token: str, db: Session) -> bool:
        """Verify an email verification token and mark user as verified"""
        payload = self.verify_token(token)
        if not payload:
            return False
        
        if payload.get("type") != "email_verification":
            return False
        
        user_id = payload.get("sub")
        if not user_id:
            return False
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        
        user.is_verified = True
        db.commit()
        return True
