"""
Document-related database models for NeuroSync API
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, Integer, ForeignKey, DateTime, JSON, Float, Text, BigInteger
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

from .user_models import Base

class Document(Base):
    """Document model for content synced from integrations"""
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=True)
    content_type = Column(String, default="text/plain")
    source = Column(String, nullable=True)  # e.g., "github", "notion", "upload"
    external_id = Column(String, nullable=True)  # ID from external system
    status = Column(String, default="synced")
    
    # Relations
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="SET NULL"), nullable=True)
    
    # File stats
    file_size = Column(BigInteger, default=0)
    word_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    synced_at = Column(DateTime, default=datetime.utcnow)
    
    # Additional document data
    document_metadata = Column(JSON, nullable=True)
    
    # Relationships
    project = relationship("Project", back_populates="documents")
    
    def __repr__(self):
        return f"<Document id={self.id} title={self.title} user_id={self.user_id}>"
