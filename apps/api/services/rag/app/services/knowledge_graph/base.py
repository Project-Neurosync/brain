"""
Base abstract class for knowledge graph services.

This module provides the interface that all knowledge graph implementations must follow.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, List, Any, Optional, Union, Set, Tuple
from pydantic import BaseModel


class EntityType(str, Enum):
    """Types of entities in the knowledge graph."""
    PERSON = "PERSON"
    FILE = "FILE"
    MEETING = "MEETING"
    ISSUE = "ISSUE"
    DECISION = "DECISION"
    CONCEPT = "CONCEPT"
    DOCUMENT = "DOCUMENT"
    PROJECT = "PROJECT"
    REPOSITORY = "REPOSITORY"
    ORGANIZATION = "ORGANIZATION"
    CUSTOM = "CUSTOM"


class RelationType(str, Enum):
    """Types of relationships in the knowledge graph."""
    AUTHORED = "AUTHORED"
    DISCUSSED = "DISCUSSED"
    RESOLVED = "RESOLVED"
    DEPENDS_ON = "DEPENDS_ON"
    IMPLEMENTS = "IMPLEMENTS"
    DECIDED_IN = "DECIDED_IN"
    BELONGS_TO = "BELONGS_TO"
    RELATED_TO = "RELATED_TO"
    CONTAINS = "CONTAINS"
    MENTIONS = "MENTIONS"
    CREATED = "CREATED"
    MODIFIED = "MODIFIED"
    CUSTOM = "CUSTOM"


class Entity(BaseModel):
    """Knowledge graph entity."""
    id: Optional[str] = None
    type: EntityType
    name: str
    properties: Dict[str, Any] = {}
    

class Relationship(BaseModel):
    """Knowledge graph relationship between entities."""
    id: Optional[str] = None
    type: RelationType
    source_id: str
    target_id: str
    properties: Dict[str, Any] = {}
    strength: float = 1.0


class Path(BaseModel):
    """Path between entities in the knowledge graph."""
    entities: List[Entity]
    relationships: List[Relationship]
    

class GraphStats(BaseModel):
    """Statistics about the knowledge graph."""
    entity_counts: Dict[EntityType, int]
    relationship_counts: Dict[RelationType, int]
    total_entities: int
    total_relationships: int
    density: float


class BaseKnowledgeGraph(ABC):
    """Base abstract class for knowledge graph services."""
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the knowledge graph service."""
        pass
    
    @abstractmethod
    async def add_entity(self, entity: Entity, project_id: Optional[str] = None) -> str:
        """
        Add an entity to the knowledge graph.
        
        Args:
            entity: Entity to add
            project_id: Optional project ID for isolation
            
        Returns:
            ID of the created entity
        """
        pass
    
    @abstractmethod
    async def add_entities_batch(
        self, 
        entities: List[Entity], 
        project_id: Optional[str] = None
    ) -> List[str]:
        """
        Add multiple entities in batch.
        
        Args:
            entities: List of entities to add
            project_id: Optional project ID for isolation
            
        Returns:
            List of created entity IDs
        """
        pass
    
    @abstractmethod
    async def add_relationship(
        self, 
        relationship: Relationship, 
        project_id: Optional[str] = None
    ) -> str:
        """
        Add a relationship between entities.
        
        Args:
            relationship: Relationship to add
            project_id: Optional project ID for isolation
            
        Returns:
            ID of the created relationship
        """
        pass
    
    @abstractmethod
    async def add_relationships_batch(
        self, 
        relationships: List[Relationship], 
        project_id: Optional[str] = None
    ) -> List[str]:
        """
        Add multiple relationships in batch.
        
        Args:
            relationships: List of relationships to add
            project_id: Optional project ID for isolation
            
        Returns:
            List of created relationship IDs
        """
        pass
    
    @abstractmethod
    async def get_entity(
        self, 
        entity_id: str, 
        project_id: Optional[str] = None
    ) -> Optional[Entity]:
        """
        Get an entity by ID.
        
        Args:
            entity_id: ID of the entity to retrieve
            project_id: Optional project ID for isolation
            
        Returns:
            Entity if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def get_entities_by_type(
        self, 
        entity_type: EntityType, 
        project_id: Optional[str] = None,
        limit: int = 100,
        skip: int = 0
    ) -> List[Entity]:
        """
        Get entities by type.
        
        Args:
            entity_type: Type of entities to retrieve
            project_id: Optional project ID for isolation
            limit: Maximum number of entities to retrieve
            skip: Number of entities to skip
            
        Returns:
            List of entities
        """
        pass
    
    @abstractmethod
    async def find_related_entities(
        self,
        entity_id: str,
        max_depth: int = 2,
        relationship_types: Optional[List[RelationType]] = None,
        min_strength: float = 0.0,
        project_id: Optional[str] = None
    ) -> List[Entity]:
        """
        Find entities related to the given entity.
        
        Args:
            entity_id: ID of the entity to find related entities for
            max_depth: Maximum traversal depth
            relationship_types: Optional filter for relationship types
            min_strength: Minimum relationship strength
            project_id: Optional project ID for isolation
            
        Returns:
            List of related entities
        """
        pass
    
    @abstractmethod
    async def find_shortest_path(
        self,
        source_id: str,
        target_id: str,
        max_depth: int = 5,
        relationship_types: Optional[List[RelationType]] = None,
        project_id: Optional[str] = None
    ) -> Optional[Path]:
        """
        Find shortest path between two entities.
        
        Args:
            source_id: ID of the source entity
            target_id: ID of the target entity
            max_depth: Maximum traversal depth
            relationship_types: Optional filter for relationship types
            project_id: Optional project ID for isolation
            
        Returns:
            Path if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def get_graph_stats(self, project_id: Optional[str] = None) -> GraphStats:
        """
        Get statistics about the knowledge graph.
        
        Args:
            project_id: Optional project ID for isolation
            
        Returns:
            Graph statistics
        """
        pass
    
    @abstractmethod
    async def delete_entity(
        self, 
        entity_id: str, 
        project_id: Optional[str] = None
    ) -> bool:
        """
        Delete an entity from the knowledge graph.
        
        Args:
            entity_id: ID of the entity to delete
            project_id: Optional project ID for isolation
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def delete_relationship(
        self, 
        relationship_id: str, 
        project_id: Optional[str] = None
    ) -> bool:
        """
        Delete a relationship from the knowledge graph.
        
        Args:
            relationship_id: ID of the relationship to delete
            project_id: Optional project ID for isolation
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def delete_project_graph(self, project_id: str) -> bool:
        """
        Delete all entities and relationships for a project.
        
        Args:
            project_id: ID of the project to delete
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def query(
        self, 
        cypher_query: str, 
        params: Optional[Dict[str, Any]] = None,
        project_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute a raw Cypher query against the knowledge graph.
        
        Args:
            cypher_query: Cypher query to execute
            params: Optional parameters for the query
            project_id: Optional project ID for isolation
            
        Returns:
            Query results as a list of dictionaries
        """
        pass
