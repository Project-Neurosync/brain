"""
NeuroSync AI Backend - Database Models
SQLAlchemy models for the NeuroSync application
"""

from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, Float, JSON,
    ForeignKey, Table, UniqueConstraint, Index
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, Session
from sqlalchemy.dialects.postgresql import UUID
import uuid

Base = declarative_base()

# Association tables for many-to-many relationships
project_members = Table(
    'project_members',
    Base.metadata,
    Column('project_id', UUID(as_uuid=True), ForeignKey('projects.id'), primary_key=True),
    Column('user_id', UUID(as_uuid=True), ForeignKey('users.id'), primary_key=True),
    Column('role', String(50), nullable=False, default='viewer'),
    Column('joined_at', DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)),
    Column('permissions', JSON, default=list)
)

project_integrations = Table(
    'project_integrations',
    Base.metadata,
    Column('project_id', UUID(as_uuid=True), ForeignKey('projects.id'), primary_key=True),
    Column('integration_id', UUID(as_uuid=True), ForeignKey('integrations.id'), primary_key=True),
    Column('enabled', Boolean, default=True),
    Column('configured_at', DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
)

class User(Base):
    """User model for authentication and profile management"""
    __tablename__ = 'users'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    avatar_url = Column(String(500), nullable=True)
    
    # Authentication
    auth_provider = Column(String(50), nullable=False, default='auth0')  # auth0, firebase, etc.
    auth_provider_id = Column(String(255), nullable=False, index=True)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    # Subscription and billing
    subscription_tier = Column(String(50), nullable=False, default='starter')  # starter, professional, enterprise
    subscription_status = Column(String(50), default='active')  # active, cancelled, past_due
    subscription_started_at = Column(DateTime(timezone=True), nullable=True)
    subscription_ends_at = Column(DateTime(timezone=True), nullable=True)
    
    # Token usage
    tokens_remaining = Column(Integer, default=100)  # Current token balance
    tokens_used_this_month = Column(Integer, default=0)
    token_reset_date = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    last_active_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    owned_projects = relationship("Project", back_populates="owner", foreign_keys="Project.owner_id")
    projects = relationship("Project", secondary=project_members, back_populates="members")
    token_purchases = relationship("TokenPurchase", back_populates="user")
    usage_logs = relationship("UsageLog", back_populates="user")
    
    # Indexes
    __table_args__ = (
        Index('idx_user_email', 'email'),
        Index('idx_user_auth_provider', 'auth_provider', 'auth_provider_id'),
        Index('idx_user_subscription', 'subscription_tier', 'subscription_status'),
    )
    
    def get_monthly_token_allocation(self) -> int:
        """Get monthly token allocation based on subscription tier"""
        allocations = {
            'starter': 100,
            'professional': 220,
            'enterprise': 380
        }
        return allocations.get(self.subscription_tier, 100)
    
    def can_use_tokens(self, tokens_needed: int) -> bool:
        """Check if user has enough tokens for a request"""
        return self.tokens_remaining >= tokens_needed
    
    def use_tokens(self, tokens_used: int) -> bool:
        """Deduct tokens from user's balance"""
        if self.tokens_remaining >= tokens_used:
            self.tokens_remaining -= tokens_used
            self.tokens_used_this_month += tokens_used
            return True
        return False

class Project(Base):
    """Project model for organizing knowledge and team collaboration"""
    __tablename__ = 'projects'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Project settings
    settings = Column(JSON, default=dict)  # AI model preferences, context length, etc.
    is_active = Column(Boolean, default=True)
    visibility = Column(String(20), default='private')  # private, team, public
    
    # Owner and team
    owner_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    max_members = Column(Integer, default=5)  # Based on subscription tier
    
    # Knowledge base stats
    document_count = Column(Integer, default=0)
    total_size_bytes = Column(Integer, default=0)
    last_sync_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    owner = relationship("User", back_populates="owned_projects", foreign_keys=[owner_id])
    members = relationship("User", secondary=project_members, back_populates="projects")
    integrations = relationship("Integration", secondary=project_integrations, back_populates="projects")
    documents = relationship("Document", back_populates="project")
    queries = relationship("Query", back_populates="project")
    meetings = relationship("Meeting", back_populates="project")
    
    # Indexes
    __table_args__ = (
        Index('idx_project_owner', 'owner_id'),
        Index('idx_project_active', 'is_active'),
        Index('idx_project_created', 'created_at'),
    )

class Integration(Base):
    """Integration model for external service connections"""
    __tablename__ = 'integrations'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)  # GitHub, Jira, Slack, etc.
    type = Column(String(50), nullable=False)  # github, jira, slack, confluence, notion
    
    # Configuration
    config = Column(JSON, default=dict)  # Encrypted connection details
    webhook_url = Column(String(500), nullable=True)
    webhook_secret = Column(String(255), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    last_sync_at = Column(DateTime(timezone=True), nullable=True)
    sync_frequency = Column(String(20), default='daily')  # hourly, daily, weekly
    sync_status = Column(String(50), default='pending')  # pending, syncing, completed, failed
    
    # Stats
    items_synced = Column(Integer, default=0)
    last_error = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    projects = relationship("Project", secondary=project_integrations, back_populates="integrations")
    
    # Indexes
    __table_args__ = (
        Index('idx_integration_type', 'type'),
        Index('idx_integration_active', 'is_active'),
    )

class Document(Base):
    """Document model for storing processed content"""
    __tablename__ = 'documents'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    content_hash = Column(String(64), nullable=False, index=True)  # For deduplication
    
    # Source information
    source_type = Column(String(50), nullable=False)  # github, jira, slack, meeting, document
    source_id = Column(String(255), nullable=True)  # External ID from source system
    source_url = Column(String(1000), nullable=True)
    file_path = Column(String(1000), nullable=True)
    
    # Project association
    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.id'), nullable=False)
    
    # Content metadata
    metadata = Column(JSON, default=dict)  # File type, language, tags, etc.
    size_bytes = Column(Integer, default=0)
    
    # Processing status
    is_processed = Column(Boolean, default=False)
    processing_status = Column(String(50), default='pending')  # pending, processing, completed, failed
    embedding_status = Column(String(50), default='pending')  # pending, processing, completed, failed
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    source_created_at = Column(DateTime(timezone=True), nullable=True)  # Original creation time
    source_updated_at = Column(DateTime(timezone=True), nullable=True)  # Original update time
    
    # Relationships
    project = relationship("Project", back_populates="documents")
    
    # Indexes
    __table_args__ = (
        Index('idx_document_project', 'project_id'),
        Index('idx_document_source', 'source_type', 'source_id'),
        Index('idx_document_hash', 'content_hash'),
        Index('idx_document_processed', 'is_processed'),
        UniqueConstraint('project_id', 'content_hash', name='uq_project_content'),
    )

class Query(Base):
    """Query model for tracking AI queries and responses"""
    __tablename__ = 'queries'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    query_text = Column(Text, nullable=False)
    response_text = Column(Text, nullable=True)
    
    # Context and metadata
    context = Column(JSON, default=dict)  # Additional context provided
    sources_used = Column(JSON, default=list)  # Documents used for context
    
    # AI model information
    model_used = Column(String(100), nullable=True)
    tokens_used = Column(Integer, default=0)
    confidence_score = Column(Float, nullable=True)
    response_time_ms = Column(Integer, nullable=True)
    
    # User and project
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.id'), nullable=False)
    
    # Status
    status = Column(String(50), default='completed')  # pending, processing, completed, failed
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    project = relationship("Project", back_populates="queries")
    user = relationship("User")
    
    # Indexes
    __table_args__ = (
        Index('idx_query_user', 'user_id'),
        Index('idx_query_project', 'project_id'),
        Index('idx_query_created', 'created_at'),
        Index('idx_query_tokens', 'tokens_used'),
    )

class Meeting(Base):
    """Meeting model for storing meeting transcripts and analysis"""
    __tablename__ = 'meetings'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(500), nullable=False)
    transcript = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    
    # Meeting details
    participants = Column(JSON, default=list)  # List of participant emails/names
    duration_minutes = Column(Integer, nullable=True)
    meeting_date = Column(DateTime(timezone=True), nullable=False)
    
    # Processing
    audio_url = Column(String(1000), nullable=True)
    transcription_status = Column(String(50), default='pending')  # pending, processing, completed, failed
    analysis_status = Column(String(50), default='pending')  # pending, processing, completed, failed
    
    # Extracted information
    action_items = Column(JSON, default=list)
    key_decisions = Column(JSON, default=list)
    topics_discussed = Column(JSON, default=list)
    
    # Project association
    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.id'), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    project = relationship("Project", back_populates="meetings")
    
    # Indexes
    __table_args__ = (
        Index('idx_meeting_project', 'project_id'),
        Index('idx_meeting_date', 'meeting_date'),
        Index('idx_meeting_status', 'transcription_status', 'analysis_status'),
    )

class TokenPurchase(Base):
    """Token purchase model for tracking add-on token purchases"""
    __tablename__ = 'token_purchases'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    
    # Purchase details
    pack_type = Column(String(50), nullable=False)  # small, medium, large, enterprise
    tokens_purchased = Column(Integer, nullable=False)
    amount_paid = Column(Float, nullable=False)
    currency = Column(String(3), default='USD')
    
    # Payment information
    payment_method = Column(String(100), nullable=True)
    payment_provider = Column(String(50), default='stripe')
    transaction_id = Column(String(255), nullable=True, index=True)
    payment_status = Column(String(50), default='pending')  # pending, completed, failed, refunded
    
    # Timestamps
    purchased_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    processed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="token_purchases")
    
    # Indexes
    __table_args__ = (
        Index('idx_token_purchase_user', 'user_id'),
        Index('idx_token_purchase_status', 'payment_status'),
        Index('idx_token_purchase_date', 'purchased_at'),
    )

class UsageLog(Base):
    """Usage log model for tracking detailed token usage and analytics"""
    __tablename__ = 'usage_logs'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.id'), nullable=True)
    
    # Usage details
    feature = Column(String(100), nullable=False)  # ai_query, document_processing, meeting_transcription
    tokens_used = Column(Integer, nullable=False)
    operation_type = Column(String(100), nullable=True)  # query, ingestion, analysis
    
    # Context
    metadata = Column(JSON, default=dict)  # Additional context about the operation
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    user = relationship("User", back_populates="usage_logs")
    
    # Indexes
    __table_args__ = (
        Index('idx_usage_user', 'user_id'),
        Index('idx_usage_project', 'project_id'),
        Index('idx_usage_feature', 'feature'),
        Index('idx_usage_date', 'created_at'),
    )

class APIKey(Base):
    """API key model for programmatic access"""
    __tablename__ = 'api_keys'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    
    # Key details
    name = Column(String(255), nullable=False)
    key_hash = Column(String(255), nullable=False, unique=True, index=True)
    key_prefix = Column(String(20), nullable=False)  # First few characters for identification
    
    # Permissions and limits
    scopes = Column(JSON, default=list)  # List of allowed operations
    rate_limit = Column(Integer, default=100)  # Requests per hour
    is_active = Column(Boolean, default=True)
    
    # Usage tracking
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    usage_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User")
    
    # Indexes
    __table_args__ = (
        Index('idx_api_key_user', 'user_id'),
        Index('idx_api_key_hash', 'key_hash'),
        Index('idx_api_key_active', 'is_active'),
    )
