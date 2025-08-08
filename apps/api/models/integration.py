"""
Integration model for NeuroSync API
Handles database schema for third-party service integrations
"""

from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from uuid import uuid4

from .user_models import Base

class Integration(Base):
    """
    Integration model for third-party services (GitHub, Slack, Jira, Confluence, Notion)
    """
    __tablename__ = "integrations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)  # User who owns this integration
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=True, index=True)  # Allow projectless integrations initially
    type = Column(String, nullable=False, index=True)  # github, slack, jira, etc.
    name = Column(String, nullable=True)  # optional friendly name
    status = Column(String, default="disconnected")  # connected, disconnected, error, syncing
    error_message = Column(String, nullable=True)  # error message if status is error
    
    # Configuration details (tokens, URLs, etc.)
    config = Column(JSON, default={})
    
    # API and sync information
    last_sync = Column(DateTime, nullable=True)
    last_sync_status = Column(String, nullable=True)
    next_scheduled_sync = Column(DateTime, nullable=True)
    
    # Control flags
    is_active = Column(Boolean, default=True)
    auto_sync = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    project = relationship("Project", back_populates="integrations")
    user = relationship("User", backref="integrations")
    
    def __repr__(self):
        return f"<Integration(id={self.id}, type={self.type}, project_id={self.project_id}, status={self.status})>"
