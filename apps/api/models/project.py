"""
Project-related database models for NeuroSync API
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, Integer, ForeignKey, DateTime, JSON, Float, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

from .user_models import Base

class Project(Base):
    """Project model for organizing user work"""
    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String, default="active")
    progress = Column(Integer, default=0)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Additional project data
    project_metadata = Column(JSON, nullable=True)
    
    # Relationships
    documents = relationship("Document", back_populates="project", cascade="all, delete-orphan")
    ai_queries = relationship("AIQuery", back_populates="project", cascade="all, delete-orphan")
    integrations = relationship("Integration", back_populates="project", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Project id={self.id} name={self.name} user_id={self.user_id}>"
