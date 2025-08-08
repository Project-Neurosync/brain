"""
Authentication schemas for NeuroSync API
Defines Pydantic models for request validation and response serialization
"""

from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserCreate(BaseModel):
    """Schema for user registration request"""
    email: EmailStr
    password: str = Field(..., min_length=8)
    name: str
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "user@example.com",
                "password": "securepassword123",
                "name": "John Doe"
            }
        }
    }


class UserLogin(BaseModel):
    """Schema for user login request"""
    email: EmailStr
    password: str
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "user@example.com",
                "password": "securepassword123"
            }
        }
    }


class TokenResponse(BaseModel):
    """Schema for token response"""
    access_token: str
    token_type: str = "bearer"


class UserBase(BaseModel):
    """Base schema for user data"""
    email: EmailStr
    name: str
    is_active: bool
    is_admin: bool


class UserResponse(UserBase):
    """Schema for user response"""
    id: str
    created_at: datetime
    
    model_config = {"from_attributes": True}


class UserInDB(UserBase):
    """Schema for user in database"""
    id: str
    password_hash: str
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


class UserProfile(UserBase):
    """Schema for user profile"""
    id: str
    
    model_config = {"from_attributes": True}


class LoginResponse(BaseModel):
    """Schema for login response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserProfile
