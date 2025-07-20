"""
Token Tracking Database Models
SQLAlchemy models for user token usage and quotas
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    """User model with subscription information"""
    __tablename__ = "users"
    
    id = Column(String, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    subscription_tier = Column(String, default="starter")  # starter, professional, enterprise
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    token_usage = relationship("TokenUsage", back_populates="user")
    token_quotas = relationship("TokenQuota", back_populates="user")

class TokenQuota(Base):
    """User token quotas based on subscription tier"""
    __tablename__ = "token_quotas"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    quota_limit = Column(Integer, nullable=False)  # Monthly token limit
    quota_used = Column(Integer, default=0)  # Tokens used this month
    quota_remaining = Column(Integer, nullable=False)  # Calculated field
    reset_date = Column(DateTime, nullable=False)  # When quota resets
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="token_quotas")

class TokenUsage(Base):
    """Individual token usage records"""
    __tablename__ = "token_usage"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    project_id = Column(String, nullable=True)  # Optional project association
    session_id = Column(String, nullable=True)  # Session tracking
    
    # Token details
    token_type = Column(String, nullable=False)  # input, output, embedding, search
    token_count = Column(Integer, nullable=False)
    model_name = Column(String, nullable=True)  # AI model used
    
    # Cost tracking
    cost_per_token = Column(Float, nullable=False)
    total_cost = Column(Float, nullable=False)
    
    # Query details
    query_text = Column(Text, nullable=True)  # Original query (truncated)
    response_text = Column(Text, nullable=True)  # Response (truncated)
    complexity_level = Column(String, nullable=True)  # simple, moderate, complex, critical
    
    # Metadata
    query_metadata = Column(Text, nullable=True)  # JSON metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="token_usage")

class TokenPack(Base):
    """Token pack purchases and add-ons"""
    __tablename__ = "token_packs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    
    # Pack details
    pack_size = Column(String, nullable=False)  # small, medium, large, enterprise
    tokens_purchased = Column(Integer, nullable=False)
    tokens_used = Column(Integer, default=0)
    tokens_remaining = Column(Integer, nullable=False)
    
    # Purchase details
    price_paid = Column(Float, nullable=False)
    purchase_date = Column(DateTime, default=datetime.utcnow)
    expiry_date = Column(DateTime, nullable=True)  # Optional expiry
    
    # Status
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class TokenOptimization(Base):
    """Token optimization and cost savings tracking"""
    __tablename__ = "token_optimizations"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    
    # Optimization details
    original_model = Column(String, nullable=False)  # Model that would have been used
    optimized_model = Column(String, nullable=False)  # Model actually used
    original_cost = Column(Float, nullable=False)  # Cost without optimization
    actual_cost = Column(Float, nullable=False)  # Cost with optimization
    savings = Column(Float, nullable=False)  # Money saved
    
    # Query details
    query_complexity = Column(String, nullable=False)  # simple, moderate, complex
    optimization_reason = Column(String, nullable=True)  # Why optimization was applied
    
    created_at = Column(DateTime, default=datetime.utcnow)
