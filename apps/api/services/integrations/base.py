"""
Base integration service for NeuroSync API
Defines common interface for all integration services
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session
from models.integration import Integration
from models.project import Project

logger = logging.getLogger(__name__)

class BaseIntegrationService(ABC):
    """
    Base class for all integration services
    Defines common interface for integration operations
    """
    
    def __init__(self, db: Session, integration: Integration = None):
        """
        Initialize integration service
        
        Args:
            db: SQLAlchemy database session
            integration: Optional Integration model instance
        """
        self.db = db
        self.integration = integration
        
    @abstractmethod
    async def test_connection(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Test connection to the integration service
        
        Args:
            config: Integration configuration (API tokens, URLs, etc.)
            
        Returns:
            Dict with connection test results
            {
                'success': bool,
                'message': str,
                'details': Optional[Dict]
            }
        """
        pass
        
    @abstractmethod
    async def get_metadata(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get integration metadata (workspace info, user info, etc.)
        
        Args:
            config: Integration configuration
            
        Returns:
            Dict with integration metadata
        """
        pass
        
    @abstractmethod
    async def ingest_data(self, project_id: UUID, limit: int = 100) -> Dict[str, Any]:
        """
        Ingest data from the integration
        
        Args:
            project_id: Project ID to associate data with
            limit: Maximum number of items to ingest
            
        Returns:
            Dict with ingestion results
            {
                'success': bool,
                'message': str,
                'items_processed': int,
                'items_imported': int,
                'errors': List[str]
            }
        """
        pass
        
    @abstractmethod
    async def filter_data_importance(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Apply ML-based importance filtering to ingested data
        
        Args:
            data: List of data items to filter
            
        Returns:
            List of data items with importance scores
        """
        pass
        
    @abstractmethod
    async def persist_data(self, project_id: UUID, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Persist filtered data to database and vector store
        
        Args:
            project_id: Project ID to associate data with
            data: Data items to persist
            
        Returns:
            Dict with persistence results
            {
                'success': bool,
                'message': str,
                'items_persisted': int,
                'errors': List[str]
            }
        """
        pass
        
    @abstractmethod
    async def sync_integration(self, project_id: UUID, full_sync: bool = False) -> Dict[str, Any]:
        """
        Run full integration sync flow:
        1. Ingest data from integration
        2. Apply ML-based importance filtering
        3. Persist filtered data
        
        Args:
            project_id: Project ID to associate data with
            full_sync: Whether to run a full sync or incremental
            
        Returns:
            Dict with sync results
        """
        pass
        
    async def update_sync_status(self, status: str, message: Optional[str] = None):
        """
        Update integration sync status
        
        Args:
            status: Status string
            message: Optional status message
        """
        if not self.integration:
            return
            
        self.integration.last_sync = datetime.utcnow()
        self.integration.last_sync_status = status
        
        if message:
            self.integration.error_message = message if status == "error" else None
            
        self.db.commit()
        self.db.refresh(self.integration)
        
    async def schedule_next_sync(self, next_sync: datetime):
        """
        Schedule next integration sync
        
        Args:
            next_sync: Next scheduled sync datetime
        """
        if not self.integration:
            return
            
        self.integration.next_scheduled_sync = next_sync
        self.db.commit()
        self.db.refresh(self.integration)
