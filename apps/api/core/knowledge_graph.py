"""
Knowledge Graph Builder for NeuroSync AI Backend
Handles knowledge graph construction and relationship mapping.
"""

from typing import Dict, List, Any, Optional, Tuple
import logging
from datetime import datetime

class KnowledgeGraphBuilder:
    """
    Builds and manages knowledge graphs from ingested data.
    Maps relationships between entities, concepts, and documents.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the Knowledge Graph Builder."""
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        self.nodes = {}
        self.edges = {}
        self.relationships = {}
    
    async def initialize(self) -> None:
        """Initialize the knowledge graph system."""
        self.logger.info("Initializing Knowledge Graph Builder...")
        # TODO: Initialize graph database connection
    
    async def close(self) -> None:
        """Close knowledge graph connections."""
        self.logger.info("Closing Knowledge Graph Builder...")
        # TODO: Close graph database connections
    
    async def add_entity(
        self,
        entity_id: str,
        entity_type: str,
        properties: Dict[str, Any],
        project_id: str
    ) -> str:
        """
        Add an entity to the knowledge graph.
        
        Args:
            entity_id: Unique identifier for the entity
            entity_type: Type of entity (person, file, concept, etc.)
            properties: Properties of the entity
            project_id: Project this entity belongs to
            
        Returns:
            Entity ID
        """
        self.nodes[entity_id] = {
            "id": entity_id,
            "type": entity_type,
            "properties": properties,
            "project_id": project_id,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        self.logger.info(f"Added entity {entity_id} of type {entity_type}")
        return entity_id
    
    async def add_relationship(
        self,
        source_id: str,
        target_id: str,
        relationship_type: str,
        properties: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Add a relationship between two entities.
        
        Args:
            source_id: Source entity ID
            target_id: Target entity ID
            relationship_type: Type of relationship
            properties: Optional relationship properties
            
        Returns:
            Relationship ID
        """
        import uuid
        rel_id = str(uuid.uuid4())
        
        self.edges[rel_id] = {
            "id": rel_id,
            "source": source_id,
            "target": target_id,
            "type": relationship_type,
            "properties": properties or {},
            "created_at": datetime.utcnow()
        }
        
        # Update relationships index
        if source_id not in self.relationships:
            self.relationships[source_id] = []
        if target_id not in self.relationships:
            self.relationships[target_id] = []
            
        self.relationships[source_id].append(rel_id)
        self.relationships[target_id].append(rel_id)
        
        return rel_id
    
    async def find_related_entities(
        self,
        entity_id: str,
        relationship_types: Optional[List[str]] = None,
        max_depth: int = 2
    ) -> List[Dict[str, Any]]:
        """
        Find entities related to the given entity.
        
        Args:
            entity_id: Entity to find relationships for
            relationship_types: Filter by relationship types
            max_depth: Maximum relationship depth to traverse
            
        Returns:
            List of related entities with relationship info
        """
        related = []
        visited = set()
        
        def traverse(current_id: str, depth: int):
            if depth > max_depth or current_id in visited:
                return
            
            visited.add(current_id)
            
            if current_id in self.relationships:
                for rel_id in self.relationships[current_id]:
                    edge = self.edges[rel_id]
                    
                    # Filter by relationship type if specified
                    if relationship_types and edge["type"] not in relationship_types:
                        continue
                    
                    # Get the other entity in the relationship
                    other_id = edge["target"] if edge["source"] == current_id else edge["source"]
                    
                    if other_id in self.nodes:
                        related.append({
                            "entity": self.nodes[other_id],
                            "relationship": edge,
                            "depth": depth
                        })
                        
                        if depth < max_depth:
                            traverse(other_id, depth + 1)
        
        traverse(entity_id, 0)
        return related
    
    async def get_graph_stats(self, project_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get statistics about the knowledge graph.
        
        Args:
            project_id: Optional project filter
            
        Returns:
            Graph statistics
        """
        nodes = self.nodes
        if project_id:
            nodes = {k: v for k, v in self.nodes.items() if v.get("project_id") == project_id}
        
        entity_types = {}
        for node in nodes.values():
            entity_type = node["type"]
            entity_types[entity_type] = entity_types.get(entity_type, 0) + 1
        
        return {
            "total_nodes": len(nodes),
            "total_edges": len(self.edges),
            "entity_types": entity_types,
            "avg_connections": len(self.edges) * 2 / len(nodes) if nodes else 0
        }
