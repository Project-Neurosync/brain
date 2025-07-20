"""
Production Knowledge Graph for NeuroSync AI Backend
Handles relationship mapping between code, meetings, developers, issues, and decisions using Neo4j.
"""

from typing import Dict, List, Any, Optional, Tuple, Union
import logging
import os
import asyncio
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

from neo4j import GraphDatabase
from pydantic import BaseModel

class GraphEntity(BaseModel):
    """Model for graph entities."""
    id: str
    type: str  # 'person', 'file', 'meeting', 'issue', 'decision', 'concept'
    properties: Dict[str, Any]
    project_id: str
    timestamp: datetime

class GraphRelationship(BaseModel):
    """Model for graph relationships."""
    from_id: str
    to_id: str
    relationship_type: str  # 'AUTHORED', 'DISCUSSED', 'RESOLVED', 'DEPENDS_ON', etc.
    properties: Dict[str, Any]
    project_id: str
    timestamp: datetime
    strength: float = 1.0  # Relationship strength (0.0 to 1.0)

class KnowledgeGraph:
    """
    Production-ready knowledge graph using Neo4j for relationship mapping.
    Supports project isolation, entity relationships, and temporal analysis.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the Knowledge Graph with Neo4j."""
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Neo4j configuration
        self.neo4j_uri = self.config.get('neo4j_uri', 'bolt://localhost:7687')
        self.neo4j_user = self.config.get('neo4j_user', 'neo4j')
        self.neo4j_password = self.config.get('neo4j_password', 'password')
        
        # Neo4j driver
        self._driver = None
        
        # Thread pool for async operations
        self._executor = ThreadPoolExecutor(max_workers=4)
        
        self.logger.info(f"Knowledge graph initialized with Neo4j URI: {self.neo4j_uri}")
    
    async def initialize(self) -> None:
        """Initialize the knowledge graph system."""
        if self._driver is None:
            def _init_driver():
                return GraphDatabase.driver(
                    self.neo4j_uri, 
                    auth=(self.neo4j_user, self.neo4j_password)
                )
            
            self._driver = await asyncio.get_event_loop().run_in_executor(
                self._executor, _init_driver
            )
            
            # Create indexes for better performance
            await self._create_indexes()
            
        self.logger.info("Neo4j driver initialized")
    
    async def _create_indexes(self) -> None:
        """Create Neo4j indexes for better query performance."""
        indexes = [
            "CREATE INDEX entity_id_index IF NOT EXISTS FOR (e:Entity) ON (e.id)",
            "CREATE INDEX entity_project_index IF NOT EXISTS FOR (e:Entity) ON (e.project_id)",
            "CREATE INDEX entity_type_index IF NOT EXISTS FOR (e:Entity) ON (e.type)",
            "CREATE INDEX entity_timestamp_index IF NOT EXISTS FOR (e:Entity) ON (e.timestamp)",
        ]
        
        def _create_indexes():
            with self._driver.session() as session:
                for index_query in indexes:
                    try:
                        session.run(index_query)
                    except Exception as e:
                        self.logger.warning(f"Index creation warning: {e}")
        
        await asyncio.get_event_loop().run_in_executor(
            self._executor, _create_indexes
        )
        
        self.logger.info("Neo4j indexes created")
    
    async def close(self) -> None:
        """Close knowledge graph connections."""
        if self._driver:
            def _close_driver():
                self._driver.close()
            
            await asyncio.get_event_loop().run_in_executor(
                self._executor, _close_driver
            )
            
        self.logger.info("Neo4j driver closed")
    
    async def add_entity(self, entity: GraphEntity) -> str:
        """
        Add an entity to the knowledge graph.
        
        Args:
            entity: GraphEntity object with all entity information
            
        Returns:
            Entity ID
        """
        await self.initialize()
        
        def _add_entity():
            with self._driver.session() as session:
                query = """
                MERGE (e:Entity {id: $entity_id, project_id: $project_id})
                SET e.type = $entity_type,
                    e.timestamp = $timestamp,
                    e.created_at = datetime(),
                    e.updated_at = datetime()
                """
                
                # Add all properties dynamically
                for key, value in entity.properties.items():
                    # Sanitize property names for Cypher
                    safe_key = key.replace('-', '_').replace(' ', '_')
                    query += f", e.{safe_key} = ${safe_key}"
                
                params = {
                    'entity_id': entity.id,
                    'project_id': entity.project_id,
                    'entity_type': entity.type,
                    'timestamp': entity.timestamp.isoformat(),
                    **{k.replace('-', '_').replace(' ', '_'): v for k, v in entity.properties.items()}
                }
                
                session.run(query, params)
        
        await asyncio.get_event_loop().run_in_executor(
            self._executor, _add_entity
        )
        
        self.logger.info(f"Added entity {entity.id} of type {entity.type} to Neo4j")
        return entity.id
    
    async def add_entities_batch(self, entities: List[GraphEntity]) -> List[str]:
        """
        Add multiple entities to the knowledge graph in a batch.
        
        Args:
            entities: List of GraphEntity objects
            
        Returns:
            List of entity IDs
        """
        await self.initialize()
        
        if not entities:
            return []
        
        def _add_entities_batch():
            with self._driver.session() as session:
                with session.begin_transaction() as tx:
                    for entity in entities:
                        query = """
                        MERGE (e:Entity {id: $entity_id, project_id: $project_id})
                        SET e.type = $entity_type,
                            e.timestamp = $timestamp,
                            e.created_at = datetime(),
                            e.updated_at = datetime()
                        """
                        
                        # Add properties dynamically
                        for key, value in entity.properties.items():
                            safe_key = key.replace('-', '_').replace(' ', '_')
                            query += f", e.{safe_key} = ${safe_key}"
                        
                        params = {
                            'entity_id': entity.id,
                            'project_id': entity.project_id,
                            'entity_type': entity.type,
                            'timestamp': entity.timestamp.isoformat(),
                            **{k.replace('-', '_').replace(' ', '_'): v for k, v in entity.properties.items()}
                        }
                        
                        tx.run(query, params)
        
        await asyncio.get_event_loop().run_in_executor(
            self._executor, _add_entities_batch
        )
        
        entity_ids = [entity.id for entity in entities]
        self.logger.info(f"Added {len(entities)} entities to Neo4j in batch")
        return entity_ids
    
    async def add_relationship(self, relationship: GraphRelationship) -> str:
        """
        Add a relationship between two entities.
        
        Args:
            relationship: GraphRelationship object with all relationship information
            
        Returns:
            Relationship ID
        """
        await self.initialize()
        
        import uuid
        rel_id = str(uuid.uuid4())
        
        def _add_relationship():
            with self._driver.session() as session:
                query = """
                MATCH (from:Entity {id: $from_id, project_id: $project_id})
                MATCH (to:Entity {id: $to_id, project_id: $project_id})
                MERGE (from)-[r:%s {id: $rel_id}]->(to)
                SET r.timestamp = $timestamp,
                    r.strength = $strength,
                    r.created_at = datetime(),
                    r.project_id = $project_id
                """ % relationship.relationship_type
                
                # Add relationship properties dynamically
                for key, value in relationship.properties.items():
                    safe_key = key.replace('-', '_').replace(' ', '_')
                    query += f", r.{safe_key} = ${safe_key}"
                
                params = {
                    'from_id': relationship.from_id,
                    'to_id': relationship.to_id,
                    'rel_id': rel_id,
                    'project_id': relationship.project_id,
                    'timestamp': relationship.timestamp.isoformat(),
                    'strength': relationship.strength,
                    **{k.replace('-', '_').replace(' ', '_'): v for k, v in relationship.properties.items()}
                }
                
                session.run(query, params)
        
        await asyncio.get_event_loop().run_in_executor(
            self._executor, _add_relationship
        )
        
        self.logger.info(f"Added relationship {relationship.relationship_type} from {relationship.from_id} to {relationship.to_id}")
        return rel_id
    
    async def add_relationships_batch(self, relationships: List[GraphRelationship]) -> List[str]:
        """
        Add multiple relationships to the knowledge graph in a batch.
        
        Args:
            relationships: List of GraphRelationship objects
            
        Returns:
            List of relationship IDs
        """
        await self.initialize()
        
        if not relationships:
            return []
        
        import uuid
        rel_ids = [str(uuid.uuid4()) for _ in relationships]
        
        def _add_relationships_batch():
            with self._driver.session() as session:
                with session.begin_transaction() as tx:
                    for i, relationship in enumerate(relationships):
                        query = """
                        MATCH (from:Entity {id: $from_id, project_id: $project_id})
                        MATCH (to:Entity {id: $to_id, project_id: $project_id})
                        MERGE (from)-[r:%s {id: $rel_id}]->(to)
                        SET r.timestamp = $timestamp,
                            r.strength = $strength,
                            r.created_at = datetime(),
                            r.project_id = $project_id
                        """ % relationship.relationship_type
                        
                        # Add properties dynamically
                        for key, value in relationship.properties.items():
                            safe_key = key.replace('-', '_').replace(' ', '_')
                            query += f", r.{safe_key} = ${safe_key}"
                        
                        params = {
                            'from_id': relationship.from_id,
                            'to_id': relationship.to_id,
                            'rel_id': rel_ids[i],
                            'project_id': relationship.project_id,
                            'timestamp': relationship.timestamp.isoformat(),
                            'strength': relationship.strength,
                            **{k.replace('-', '_').replace(' ', '_'): v for k, v in relationship.properties.items()}
                        }
                        
                        tx.run(query, params)
        
        await asyncio.get_event_loop().run_in_executor(
            self._executor, _add_relationships_batch
        )
        
        self.logger.info(f"Added {len(relationships)} relationships to Neo4j in batch")
        return rel_ids
    
    async def find_related_entities(
        self,
        entity_id: str,
        project_id: str,
        relationship_types: Optional[List[str]] = None,
        max_depth: int = 2,
        min_strength: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Find entities related to the given entity using Neo4j graph traversal.
        
        Args:
            entity_id: Entity to find relationships for
            project_id: Project ID for isolation
            relationship_types: Filter by relationship types
            max_depth: Maximum relationship depth to traverse
            min_strength: Minimum relationship strength threshold
            
        Returns:
            List of related entities with relationship info
        """
        await self.initialize()
        
        def _find_related():
            with self._driver.session() as session:
                # Build relationship type filter
                rel_filter = ""
                if relationship_types:
                    rel_types = "|".join(relationship_types)
                    rel_filter = f":{rel_types}"
                
                query = f"""
                MATCH path = (start:Entity {{id: $entity_id, project_id: $project_id}})
                -[r{rel_filter}*1..{max_depth}]-
                (related:Entity {{project_id: $project_id}})
                WHERE ALL(rel in relationships(path) WHERE rel.strength >= $min_strength)
                RETURN related, relationships(path) as rels, length(path) as depth
                ORDER BY depth, related.timestamp DESC
                LIMIT 100
                """
                
                result = session.run(query, {
                    'entity_id': entity_id,
                    'project_id': project_id,
                    'min_strength': min_strength
                })
                
                related_entities = []
                for record in result:
                    entity_data = dict(record['related'])
                    relationships_data = [dict(rel) for rel in record['rels']]
                    depth = record['depth']
                    
                    related_entities.append({
                        'entity': entity_data,
                        'relationships': relationships_data,
                        'depth': depth,
                        'path_strength': sum(rel.get('strength', 1.0) for rel in relationships_data) / len(relationships_data)
                    })
                
                return related_entities
        
        related = await asyncio.get_event_loop().run_in_executor(
            self._executor, _find_related
        )
        
        self.logger.info(f"Found {len(related)} related entities for {entity_id}")
        return related
    
    async def find_shortest_path(
        self,
        from_entity_id: str,
        to_entity_id: str,
        project_id: str,
        relationship_types: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Find the shortest path between two entities.
        
        Args:
            from_entity_id: Starting entity ID
            to_entity_id: Target entity ID
            project_id: Project ID for isolation
            relationship_types: Filter by relationship types
            
        Returns:
            Path information or None if no path exists
        """
        await self.initialize()
        
        def _find_shortest_path():
            with self._driver.session() as session:
                rel_filter = ""
                if relationship_types:
                    rel_types = "|".join(relationship_types)
                    rel_filter = f":{rel_types}"
                
                query = f"""
                MATCH path = shortestPath(
                    (from:Entity {{id: $from_id, project_id: $project_id}})
                    -[r{rel_filter}*]-
                    (to:Entity {{id: $to_id, project_id: $project_id}})
                )
                RETURN path, length(path) as path_length
                """
                
                result = session.run(query, {
                    'from_id': from_entity_id,
                    'to_id': to_entity_id,
                    'project_id': project_id
                })
                
                record = result.single()
                if record:
                    path = record['path']
                    return {
                        'entities': [dict(node) for node in path.nodes],
                        'relationships': [dict(rel) for rel in path.relationships],
                        'length': record['path_length']
                    }
                return None
        
        path = await asyncio.get_event_loop().run_in_executor(
            self._executor, _find_shortest_path
        )
        
        return path
    
    async def get_graph_stats(self, project_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get comprehensive statistics about the knowledge graph.
        
        Args:
            project_id: Optional project filter
            
        Returns:
            Graph statistics including nodes, relationships, and analytics
        """
        await self.initialize()
        
        def _get_stats():
            with self._driver.session() as session:
                # Base query with optional project filter
                project_filter = "WHERE e.project_id = $project_id" if project_id else ""
                params = {'project_id': project_id} if project_id else {}
                
                # Get node statistics
                node_query = f"""
                MATCH (e:Entity)
                {project_filter}
                RETURN count(e) as total_nodes,
                       collect(DISTINCT e.type) as entity_types,
                       avg(size((e)-->())) as avg_outgoing_connections,
                       avg(size((e)<--())) as avg_incoming_connections
                """
                
                node_result = session.run(node_query, params).single()
                
                # Get relationship statistics
                rel_query = f"""
                MATCH (e1:Entity)-[r]->(e2:Entity)
                {project_filter.replace('e.', 'e1.') if project_filter else ""}
                {('AND e2.project_id = $project_id' if project_filter else '')}
                RETURN count(r) as total_relationships,
                       collect(DISTINCT type(r)) as relationship_types,
                       avg(r.strength) as avg_relationship_strength
                """
                
                rel_result = session.run(rel_query, params).single()
                
                # Get entity type distribution
                type_query = f"""
                MATCH (e:Entity)
                {project_filter}
                RETURN e.type as entity_type, count(e) as count
                ORDER BY count DESC
                """
                
                type_results = session.run(type_query, params)
                entity_type_distribution = {record['entity_type']: record['count'] for record in type_results}
                
                # Get relationship type distribution
                rel_type_query = f"""
                MATCH (e1:Entity)-[r]->(e2:Entity)
                {project_filter.replace('e.', 'e1.') if project_filter else ""}
                {('AND e2.project_id = $project_id' if project_filter else '')}
                RETURN type(r) as relationship_type, count(r) as count
                ORDER BY count DESC
                """
                
                rel_type_results = session.run(rel_type_query, params)
                relationship_type_distribution = {record['relationship_type']: record['count'] for record in rel_type_results}
                
                # Get most connected entities
                connected_query = f"""
                MATCH (e:Entity)
                {project_filter}
                WITH e, size((e)--()) as connections
                ORDER BY connections DESC
                LIMIT 10
                RETURN e.id as entity_id, e.type as entity_type, connections
                """
                
                connected_results = session.run(connected_query, params)
                most_connected = [{
                    'entity_id': record['entity_id'],
                    'entity_type': record['entity_type'],
                    'connections': record['connections']
                } for record in connected_results]
                
                # Get temporal statistics
                temporal_query = f"""
                MATCH (e:Entity)
                {project_filter}
                WHERE e.timestamp IS NOT NULL
                RETURN min(e.timestamp) as earliest_entity,
                       max(e.timestamp) as latest_entity,
                       count(e) as entities_with_timestamp
                """
                
                temporal_result = session.run(temporal_query, params).single()
                
                return {
                    'total_nodes': node_result['total_nodes'] or 0,
                    'total_relationships': rel_result['total_relationships'] or 0,
                    'entity_types': node_result['entity_types'] or [],
                    'relationship_types': rel_result['relationship_types'] or [],
                    'entity_type_distribution': entity_type_distribution,
                    'relationship_type_distribution': relationship_type_distribution,
                    'avg_outgoing_connections': node_result['avg_outgoing_connections'] or 0,
                    'avg_incoming_connections': node_result['avg_incoming_connections'] or 0,
                    'avg_relationship_strength': rel_result['avg_relationship_strength'] or 0,
                    'most_connected_entities': most_connected,
                    'temporal_range': {
                        'earliest': temporal_result['earliest_entity'],
                        'latest': temporal_result['latest_entity'],
                        'entities_with_timestamp': temporal_result['entities_with_timestamp'] or 0
                    },
                    'graph_density': (rel_result['total_relationships'] or 0) / max(1, (node_result['total_nodes'] or 0) * ((node_result['total_nodes'] or 0) - 1)) if node_result['total_nodes'] and node_result['total_nodes'] > 1 else 0
                }
        
        stats = await asyncio.get_event_loop().run_in_executor(
            self._executor, _get_stats
        )
        
        return stats
    
    async def delete_project_graph(self, project_id: str) -> int:
        """
        Delete all entities and relationships for a specific project.
        
        Args:
            project_id: Project ID to delete graph data for
            
        Returns:
            Number of nodes deleted
        """
        await self.initialize()
        
        def _delete_project():
            with self._driver.session() as session:
                # Delete all relationships first
                rel_query = """
                MATCH (e1:Entity {project_id: $project_id})-[r]-(e2:Entity {project_id: $project_id})
                DELETE r
                """
                session.run(rel_query, {'project_id': project_id})
                
                # Then delete all nodes
                node_query = """
                MATCH (e:Entity {project_id: $project_id})
                DELETE e
                RETURN count(e) as deleted_count
                """
                result = session.run(node_query, {'project_id': project_id})
                return result.single()['deleted_count']
        
        deleted_count = await asyncio.get_event_loop().run_in_executor(
            self._executor, _delete_project
        )
        
        self.logger.info(f"Deleted {deleted_count} entities for project {project_id}")
        return deleted_count
