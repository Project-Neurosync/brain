"""
Authentication Manager for NeuroSync AI Backend
Handles JWT authentication, user management, and project access control.
"""

from typing import Dict, List, Any, Optional
import logging
import jwt
from datetime import datetime, timedelta
from passlib.context import CryptContext
import secrets

class AuthManager:
    """
    Manages authentication, authorization, and user sessions.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the Auth Manager."""
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.secret_key = self.config.get("jwt_secret", "your-secret-key-change-in-production")
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 30
        self.refresh_token_expire_days = 7
        
        # In-memory storage (replace with database in production)
        self.users = {}
        self.user_projects = {}
        self.refresh_tokens = {}
    
    def hash_password(self, password: str) -> str:
        """Hash a password."""
        return self.pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def create_refresh_token(self, user_id: str) -> str:
        """Create a refresh token."""
        token_id = secrets.token_urlsafe(32)
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        
        self.refresh_tokens[token_id] = {
            "user_id": user_id,
            "expires_at": expire,
            "created_at": datetime.utcnow()
        }
        
        return token_id
    
    async def validate_token(self, token: str) -> Dict[str, Any]:
        """
        Validate a JWT token and return user info.
        
        Args:
            token: JWT token to validate
            
        Returns:
            User information from token
            
        Raises:
            Exception: If token is invalid or expired
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            user_id = payload.get("sub")
            token_type = payload.get("type")
            
            if user_id is None or token_type != "access":
                raise Exception("Invalid token")
            
            # Get user info
            user = self.users.get(user_id)
            if not user:
                raise Exception("User not found")
            
            return {
                "user_id": user_id,
                "email": user["email"],
                "subscription_tier": user.get("subscription_tier", "starter"),
                "is_active": user.get("is_active", True)
            }
            
        except jwt.ExpiredSignatureError:
            raise Exception("Token has expired")
        except jwt.JWTError:
            raise Exception("Invalid token")
    
    async def register_user(
        self,
        email: str,
        password: str,
        subscription_tier: str = "starter",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Register a new user.
        
        Args:
            email: User email
            password: User password
            subscription_tier: Subscription tier
            metadata: Additional user metadata
            
        Returns:
            User information and tokens
        """
        # Check if user already exists
        for user_id, user in self.users.items():
            if user["email"] == email:
                raise Exception("User already exists")
        
        # Create new user
        import uuid
        user_id = str(uuid.uuid4())
        hashed_password = self.hash_password(password)
        
        user_data = {
            "id": user_id,
            "email": email,
            "password_hash": hashed_password,
            "subscription_tier": subscription_tier,
            "is_active": True,
            "created_at": datetime.utcnow(),
            "metadata": metadata or {}
        }
        
        self.users[user_id] = user_data
        self.user_projects[user_id] = []
        
        # Create tokens
        access_token = self.create_access_token({"sub": user_id})
        refresh_token = self.create_refresh_token(user_id)
        
        self.logger.info(f"Registered new user: {email}")
        
        return {
            "user_id": user_id,
            "email": email,
            "subscription_tier": subscription_tier,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
    
    async def authenticate_user(self, email: str, password: str) -> Dict[str, Any]:
        """
        Authenticate a user with email and password.
        
        Args:
            email: User email
            password: User password
            
        Returns:
            User information and tokens
        """
        # Find user by email
        user = None
        user_id = None
        for uid, u in self.users.items():
            if u["email"] == email:
                user = u
                user_id = uid
                break
        
        if not user or not self.verify_password(password, user["password_hash"]):
            raise Exception("Invalid credentials")
        
        if not user.get("is_active", True):
            raise Exception("Account is disabled")
        
        # Create tokens
        access_token = self.create_access_token({"sub": user_id})
        refresh_token = self.create_refresh_token(user_id)
        
        return {
            "user_id": user_id,
            "email": user["email"],
            "subscription_tier": user.get("subscription_tier", "starter"),
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
    
    async def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh an access token using a refresh token.
        
        Args:
            refresh_token: Refresh token
            
        Returns:
            New access token
        """
        token_data = self.refresh_tokens.get(refresh_token)
        if not token_data:
            raise Exception("Invalid refresh token")
        
        if datetime.utcnow() > token_data["expires_at"]:
            del self.refresh_tokens[refresh_token]
            raise Exception("Refresh token has expired")
        
        user_id = token_data["user_id"]
        user = self.users.get(user_id)
        if not user:
            raise Exception("User not found")
        
        # Create new access token
        access_token = self.create_access_token({"sub": user_id})
        
        return {
            "access_token": access_token,
            "token_type": "bearer"
        }
    
    async def has_project_access(self, user_id: str, project_id: str) -> bool:
        """
        Check if a user has access to a project.
        
        Args:
            user_id: User ID
            project_id: Project ID
            
        Returns:
            True if user has access, False otherwise
        """
        user_projects = self.user_projects.get(user_id, [])
        return project_id in user_projects
    
    async def grant_project_access(self, user_id: str, project_id: str, role: str = "member") -> None:
        """
        Grant a user access to a project.
        
        Args:
            user_id: User ID
            project_id: Project ID
            role: User role in the project
        """
        if user_id not in self.user_projects:
            self.user_projects[user_id] = []
        
        if project_id not in self.user_projects[user_id]:
            self.user_projects[user_id].append(project_id)
            self.logger.info(f"Granted {role} access to project {project_id} for user {user_id}")
    
    async def revoke_project_access(self, user_id: str, project_id: str) -> None:
        """
        Revoke a user's access to a project.
        
        Args:
            user_id: User ID
            project_id: Project ID
        """
        if user_id in self.user_projects and project_id in self.user_projects[user_id]:
            self.user_projects[user_id].remove(project_id)
            self.logger.info(f"Revoked access to project {project_id} for user {user_id}")
    
    async def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """
        Get user profile information.
        
        Args:
            user_id: User ID
            
        Returns:
            User profile data
        """
        user = self.users.get(user_id)
        if not user:
            raise Exception("User not found")
        
        return {
            "user_id": user_id,
            "email": user["email"],
            "subscription_tier": user.get("subscription_tier", "starter"),
            "is_active": user.get("is_active", True),
            "created_at": user["created_at"],
            "projects": self.user_projects.get(user_id, []),
            "metadata": user.get("metadata", {})
        }
