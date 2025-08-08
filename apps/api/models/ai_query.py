"""
AI Query models for NeuroSync API
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, Integer, ForeignKey, DateTime, JSON, Float, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

from .user_models import Base

class AIQuery(Base):
    """AI Query model for tracking user interactions with AI"""
    __tablename__ = "ai_queries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    query_text = Column(Text, nullable=False)
    response = Column(Text, nullable=True)
    status = Column(String, default="completed")  # pending, completed, failed
    tokens_used = Column(Integer, default=0)
    duration_ms = Column(Integer, default=0)
    
    # Relations
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="SET NULL"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # Additional query data
    query_metadata = Column(JSON, nullable=True)
    
    # Relationships
    project = relationship("Project", back_populates="ai_queries")
    
    def __repr__(self):
        return f"<AIQuery id={self.id} user_id={self.user_id}>"
    
    @property
    def truncated_query(self):
        """Return truncated query for display"""
        if len(self.query_text) > 50:
            return self.query_text[:47] + "..."
        return self.query_text
