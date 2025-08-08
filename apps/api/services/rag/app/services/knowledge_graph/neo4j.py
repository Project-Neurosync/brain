"""
Production-ready Neo4j knowledge graph service.

This module provides a Neo4j implementation of the knowledge graph service
optimized for production use with Neo4j Aura or self-hosted instances.
"""

import asyncio
import logging
import os
import time
import uuid
from typing import Dict, List, Any, Optional, Union, Set, Tuple, cast
from datetime import datetime, timezone
from functools import wraps

import neo4j
from neo4j import AsyncGraphDatabase, AsyncDriver
from neo4j.exceptions import ServiceUnavailable, ClientError, TransientError
from neo4j.time import DateTime

from app.core.config import settings
from app.services.knowledge_graph.base import (
    BaseKnowledgeGraph, 
    Entity, 
    Relationship,
    EntityType,
    RelationType,
    Path,
    GraphStats,
)

# Set up logger
logger = logging.getLogger(__name__)


# Retry decorator for transient Neo4j errors
def retry_on_exception(
    retries: int = 3,
    backoff_factor: float = 0.5,
    allowed_exceptions: tuple = (ServiceUnavailable, TransientError),
):
    """
    Retry decorator for handling transient Neo4j errors with exponential backoff.
    
    Args:
        retries: Maximum number of retries
        backoff_factor: Backoff factor for exponential wait between retries
        allowed_exceptions: Exceptions that trigger a retry
        
    Returns:
        Decorated function
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(retries + 1):
                try:
                    return await func(*args, **kwargs)
                except allowed_exceptions as e:
                    last_exception = e
                    if attempt < retries:
                        wait_time = backoff_factor * (2 ** attempt)
                        logger.warning(
                            f"Neo4j operation failed (attempt {attempt+1}/{retries+1}). "
                            f"Retrying in {wait_time:.2f}s. Error: {str(e)}"
                        )
                        await asyncio.sleep(wait_time)
                    else:
                        logger.error(
                            f"Neo4j operation failed after {retries+1} attempts: {str(e)}"
                        )
            raise last_exception
        return wrapper
    return decorator


class Neo4jKnowledgeGraph(BaseKnowledgeGraph):
    """Production-ready Neo4j knowledge graph service."""
    
    def __init__(
        self,
        uri: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        database: Optional[str] = None,
        connection_acquisition_timeout: int = 60,
        connection_timeout: int = 30,
        max_transaction_retry_time: int = 30,
        connection_pool_size: int = 50,
    ):
        """
        Initialize the Neo4j knowledge graph service.
        
        Args:
            uri: Neo4j connection URI (defaults to settings)
            username: Neo4j username (defaults to settings)
            password: Neo4j password (defaults to settings)
            database: Neo4j database name (defaults to settings)
            connection_acquisition_timeout: Timeout for acquiring connections from pool
            connection_timeout: Connection timeout
            max_transaction_retry_time: Max time to retry transactions
            connection_pool_size: Size of the connection pool
        """
        self.uri = uri or settings.neo4j.uri
        self.username = username or settings.neo4j.username
        self.password = password or settings.neo4j.password
        self.database = database or settings.neo4j.database
        self.driver: Optional[AsyncDriver] = None
        self.connection_acquisition_timeout = connection_acquisition_timeout
        self.connection_timeout = connection_timeout
        self.max_transaction_retry_time = max_transaction_retry_time
        self.connection_pool_size = connection_pool_size
        
        # Performance monitoring
        self.metrics = {
            "operations": 0,
            "errors": 0,
            "retries": 0,
        }
        
    async def initialize(self) -> None:
        """Initialize the Neo4j driver and ensure database connection."""
        if self.driver is not None:
            return
        
        try:
            logger.info(f"Initializing Neo4j connection to {self.uri}")
            
            # Create driver with optimal production settings
            self.driver = AsyncGraphDatabase.driver(
                self.uri,
                auth=(self.username, self.password),
                max_connection_lifetime=3600,  # 1 hour
                max_connection_pool_size=self.connection_pool_size,
                connection_acquisition_timeout=self.connection_acquisition_timeout,
                connection_timeout=self.connection_timeout,
                max_transaction_retry_time=self.max_transaction_retry_time,
                resolver=None,  # Use system DNS resolver
                encrypted=True,  # Always use encryption in production
                trust="TRUST_SYSTEM_CA_SIGNED_CERTIFICATES",  # Trust system CA certs
                user_agent=f"NeuralKG/{settings.app_version}"
            )
            
            # Test connection
            await self._verify_connectivity()
            
            # Create constraints and indices for performance
            await self._create_constraints_and_indices()
            
            logger.info("Neo4j connection initialized successfully")
            
        except Exception as e:
            self.metrics["errors"] += 1
            logger.error(f"Failed to initialize Neo4j connection: {str(e)}")
            raise
            
    async def _verify_connectivity(self) -> bool:
        """Verify connection to Neo4j database."""
        if not self.driver:
            await self.initialize()
            
        try:
            async with self.driver.session(database=self.database) as session:
                result = await session.run("RETURN 1 AS test")
                record = await result.single()
                return record and record.get("test") == 1
        except Exception as e:
            logger.error(f"Neo4j connectivity test failed: {str(e)}")
            raise
            
    async def _create_constraints_and_indices(self) -> None:
        """Create constraints and indices for optimal performance."""
        if not self.driver:
            await self.initialize()
            
        # Critical performance optimization for production
        constraints = [
            # Entity ID uniqueness constraint - essential
            "CREATE CONSTRAINT entity_id_unique IF NOT EXISTS FOR (e:Entity) REQUIRE e.id IS UNIQUE",
            
            # Project + entity type composite index - for fast lookups by type within projects
            "CREATE INDEX entity_project_type IF NOT EXISTS FOR (e:Entity) ON (e.project_id, e.type)",
            
            # Relationship ID uniqueness constraint
            "CREATE CONSTRAINT relationship_id_unique IF NOT EXISTS FOR ()-[r:RELATES_TO]->() REQUIRE r.id IS UNIQUE",
            
            # Project ID index for fast filtering by project
            "CREATE INDEX entity_project IF NOT EXISTS FOR (e:Entity) ON (e.project_id)",
            
            # Full-text search index for entity names - critical for search performance
            "CALL db.index.fulltext.createNodeIndex('entity_name_fulltext', ['Entity'], ['name'])"
        ]
        
        try:
            async with self.driver.session(database=self.database) as session:
                for constraint in constraints:
                    try:
                        await session.run(constraint)
                    except ClientError as e:
                        # Skip if constraint/index already exists
                        if "already exists" not in str(e):
                            logger.warning(f"Failed to create constraint/index: {str(e)}")
        except Exception as e:
            logger.error(f"Failed to create constraints/indices: {str(e)}")
            # Continue despite errors - this shouldn't block startup
            
    async def close(self) -> None:
        """Close the Neo4j driver and release all resources."""
        if self.driver:
            try:
                await self.driver.close()
                logger.info("Neo4j connection closed")
            except Exception as e:
                logger.error(f"Error closing Neo4j connection: {str(e)}")
            finally:
                self.driver = None
                
    def _prepare_entity(self, entity: Entity, project_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Prepare entity for Neo4j operations.
        
        Args:
            entity: The entity to prepare
            project_id: Optional project ID
            
        Returns:
            Dictionary of entity properties ready for Neo4j
        """
        # Generate ID if not provided
        entity_id = entity.id or str(uuid.uuid4())
        
        # Basic properties
        properties = {
            "id": entity_id,
            "name": entity.name,
            "type": entity.type.value,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
        
        # Add project_id for isolation if provided
        if project_id:
            properties["project_id"] = project_id
            
        # Add custom properties
        if entity.properties:
            # Filter out None values and serialize complex objects
            for key, value in entity.properties.items():
                if value is not None:
                    if isinstance(value, (dict, list)):
                        # Neo4j doesn't handle complex objects well in Cypher
                        # Convert to string for storage (not ideal for querying)
                        import json
                        properties[key] = json.dumps(value)
                    else:
                        properties[key] = value
                        
        return properties
    
    def _prepare_relationship(
        self, 
        relationship: Relationship,
        project_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Prepare relationship for Neo4j operations.
        
        Args:
            relationship: The relationship to prepare
            project_id: Optional project ID
            
        Returns:
            Dictionary of relationship properties ready for Neo4j
        """
        # Generate ID if not provided
        rel_id = relationship.id or str(uuid.uuid4())
        
        # Basic properties
        properties = {
            "id": rel_id,
            "type": relationship.type.value,
            "strength": float(relationship.strength),
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
        
        # Add project_id for isolation if provided
        if project_id:
            properties["project_id"] = project_id
            
        # Add custom properties
        if relationship.properties:
            # Filter out None values and serialize complex objects
            for key, value in relationship.properties.items():
                if value is not None:
                    if isinstance(value, (dict, list)):
                        # Neo4j doesn't handle complex objects well in Cypher
                        import json
                        properties[key] = json.dumps(value)
                    else:
                        properties[key] = value
                        
        return properties
    
    def _neo4j_to_entity(self, record: Dict[str, Any]) -> Entity:
        """
        Convert a Neo4j node record to an Entity.
        
        Args:
            record: Neo4j node record
            
        Returns:
            Entity object
        """
        # Extract and parse properties
        properties = {}
        for key, value in record.items():
            if key not in ["id", "name", "type", "created_at", "updated_at", "project_id"]:
                # Try to parse JSON strings back to objects
                if isinstance(value, str) and (value.startswith("{") or value.startswith("[")):
                    try:
                        import json
                        properties[key] = json.loads(value)
                    except:
                        properties[key] = value
                else:
                    properties[key] = value
        
        # Create and return entity
        try:
            entity_type = EntityType(record["type"])
        except ValueError:
            # Fallback for unknown entity types
            entity_type = EntityType.CUSTOM
            
        return Entity(
            id=record["id"],
            name=record["name"],
            type=entity_type,
            properties=properties,
        )
    
    def _neo4j_to_relationship(self, record: Dict[str, Any]) -> Relationship:
        """
        Convert a Neo4j relationship record to a Relationship.
        
        Args:
            record: Neo4j relationship record
            
        Returns:
            Relationship object
        """
        # Extract and parse properties
        properties = {}
        for key, value in record.items():
            if key not in ["id", "type", "strength", "source_id", "target_id", 
                           "created_at", "updated_at", "project_id"]:
                # Try to parse JSON strings back to objects
                if isinstance(value, str) and (value.startswith("{") or value.startswith("[")):
                    try:
                        import json
                        properties[key] = json.loads(value)
                    except:
                        properties[key] = value
                else:
                    properties[key] = value
        
        # Create and return relationship
        try:
            rel_type = RelationType(record["type"])
        except ValueError:
            # Fallback for unknown relationship types
            rel_type = RelationType.CUSTOM
            
        return Relationship(
            id=record["id"],
            type=rel_type,
            source_id=record["source_id"],
            target_id=record["target_id"],
            strength=float(record.get("strength", 1.0)),
            properties=properties,
        )
    
    @retry_on_exception()
    async def add_entity(self, entity: Entity, project_id: Optional[str] = None) -> str:
        """
        Add an entity to the knowledge graph.
        
        Args:
            entity: Entity to add
            project_id: Optional project ID for isolation
            
        Returns:
            ID of the created entity
        """
        if not self.driver:
            await self.initialize()
        
        # Prepare entity for Neo4j
        properties = self._prepare_entity(entity, project_id)
        entity_id = properties["id"]
        
        # Create query with parameters
        query = """
        CREATE (e:Entity {properties})
        RETURN e.id as id
        """
        
        try:
            self.metrics["operations"] += 1
            async with self.driver.session(database=self.database) as session:
                result = await session.run(query, {"properties": properties})
                record = await result.single()
                logger.debug(f"Entity created: {entity_id}")
                return record["id"]
        except Exception as e:
            self.metrics["errors"] += 1
            logger.error(f"Error creating entity: {str(e)}")
            raise
    
    @retry_on_exception()
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
        if not entities:
            return []
            
        if not self.driver:
            await self.initialize()
        
        # Prepare entities for Neo4j
        entity_props = [self._prepare_entity(entity, project_id) for entity in entities]
        entity_ids = [props["id"] for props in entity_props]
        
        # Create query with parameters - use UNWIND for batch processing
        query = """
        UNWIND $entities AS entity
        CREATE (e:Entity)
        SET e = entity
        RETURN e.id as id
        """
        
        try:
            self.metrics["operations"] += 1
            async with self.driver.session(database=self.database) as session:
                result = await session.run(query, {"entities": entity_props})
                records = await result.fetch(len(entity_props))
                created_ids = [record["id"] for record in records]
                logger.debug(f"Created {len(created_ids)} entities in batch")
                return created_ids
        except Exception as e:
            self.metrics["errors"] += 1
            logger.error(f"Error creating entities batch: {str(e)}")
            raise
    
    @retry_on_exception()
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
        if not self.driver:
            await self.initialize()
        
        # Prepare relationship for Neo4j
        properties = self._prepare_relationship(relationship, project_id)
        rel_id = properties["id"]
        rel_type = properties["type"]
        
        # Remove type from properties as it's used for the relationship type
        del properties["type"]
        
        # Create query with parameters
        query = """
        MATCH (source:Entity {id: $source_id}), (target:Entity {id: $target_id})
        CREATE (source)-[r:RELATES_TO {properties}]->(target)
        RETURN r.id as id
        """
        
        try:
            self.metrics["operations"] += 1
            async with self.driver.session(database=self.database) as session:
                result = await session.run(
                    query, 
                    {
                        "source_id": relationship.source_id,
                        "target_id": relationship.target_id,
                        "properties": properties
                    }
                )
                record = await result.single()
                logger.debug(f"Relationship created: {rel_id} ({rel_type})")
                return record["id"]
        except Exception as e:
            self.metrics["errors"] += 1
            logger.error(f"Error creating relationship: {str(e)}")
            raise
    
    @retry_on_exception()
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
        if not relationships:
            return []
            
        if not self.driver:
            await self.initialize()
        
        # Prepare batch data
        batch_data = []
        for rel in relationships:
            props = self._prepare_relationship(rel, project_id)
            rel_type = props.pop("type")  # Remove type from properties
            batch_data.append({
                "source_id": rel.source_id,
                "target_id": rel.target_id,
                "properties": props
            })
        
        # Create query with parameters - use UNWIND for batch processing
        query = """
        UNWIND $batch AS item
        MATCH (source:Entity {id: item.source_id}), (target:Entity {id: item.target_id})
        CREATE (source)-[r:RELATES_TO]->(target)
        SET r = item.properties
        RETURN r.id as id
        """
        
        try:
            self.metrics["operations"] += 1
            async with self.driver.session(database=self.database) as session:
                result = await session.run(query, {"batch": batch_data})
                records = await result.fetch(len(batch_data))
                created_ids = [record["id"] for record in records]
                logger.debug(f"Created {len(created_ids)} relationships in batch")
                return created_ids
        except Exception as e:
            self.metrics["errors"] += 1
            logger.error(f"Error creating relationships batch: {str(e)}")
            raise
    
    @retry_on_exception()
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
        if not self.driver:
            await self.initialize()
        
        # Create query with parameters
        query = """
        MATCH (e:Entity {id: $entity_id})
        WHERE $project_id IS NULL OR e.project_id = $project_id
        RETURN e
        """
        
        try:
            self.metrics["operations"] += 1
            async with self.driver.session(database=self.database) as session:
                result = await session.run(
                    query, 
                    {
                        "entity_id": entity_id,
                        "project_id": project_id
                    }
                )
                record = await result.single()
                
                if not record:
                    return None
                    
                # Convert Neo4j node to Entity
                node = record["e"]
                node_dict = dict(node.items())
                
                return self._neo4j_to_entity(node_dict)
        except Exception as e:
            self.metrics["errors"] += 1
            logger.error(f"Error retrieving entity: {str(e)}")
            if "No record found" in str(e):
                return None
            raise

    @retry_on_exception()
    async def get_entities_by_type(
        self,
        entity_type: EntityType,
        project_id: Optional[str] = None,
        limit: int = 100,
        skip: int = 0
    ) -> List[Entity]:
        """
        Get entities by type with pagination.
        
        Args:
            entity_type: Type of entities to retrieve
            project_id: Optional project ID for isolation
            limit: Maximum number of entities to return
            skip: Number of entities to skip for pagination
            
        Returns:
            List of entities
        """
        if not self.driver:
            await self.initialize()
            
        # Create query with parameters
        query = """
        MATCH (e:Entity {type: $type})
        WHERE $project_id IS NULL OR e.project_id = $project_id
        RETURN e
        ORDER BY e.created_at DESC
        SKIP $skip
        LIMIT $limit
        """
        
        try:
            self.metrics["operations"] += 1
            async with self.driver.session(database=self.database) as session:
                result = await session.run(
                    query, 
                    {
                        "type": entity_type.value,
                        "project_id": project_id,
                        "skip": skip,
                        "limit": limit
                    }
                )
                records = await result.fetch(limit)
                
                entities = []
                for record in records:
                    node = record["e"]
                    node_dict = dict(node.items())
                    entity = self._neo4j_to_entity(node_dict)
                    entities.append(entity)
                    
                return entities
        except Exception as e:
            self.metrics["errors"] += 1
            logger.error(f"Error retrieving entities by type: {str(e)}")
            raise
            
    @retry_on_exception()
    async def search_entities(
        self,
        query: str,
        project_id: Optional[str] = None,
        entity_types: Optional[List[EntityType]] = None,
        limit: int = 20
    ) -> List[Entity]:
        """
        Search entities by name using full-text search.
        
        Args:
            query: Search query
            project_id: Optional project ID for isolation
            entity_types: Optional list of entity types to filter by
            limit: Maximum number of entities to return
            
        Returns:
            List of entities matching the search
        """
        if not self.driver:
            await self.initialize()
            
        # Convert entity types to values
        type_values = None
        if entity_types:
            type_values = [et.value for et in entity_types]
            
        # Create full-text search query
        if type_values:
            cypher_query = """
            CALL db.index.fulltext.queryNodes('entity_name_fulltext', $query)
            YIELD node, score
            WHERE node.type IN $type_values
            AND ($project_id IS NULL OR node.project_id = $project_id)
            RETURN node, score
            ORDER BY score DESC
            LIMIT $limit
            """
        else:
            cypher_query = """
            CALL db.index.fulltext.queryNodes('entity_name_fulltext', $query)
            YIELD node, score
            WHERE ($project_id IS NULL OR node.project_id = $project_id)
            RETURN node, score
            ORDER BY score DESC
            LIMIT $limit
            """
            
        try:
            self.metrics["operations"] += 1
            async with self.driver.session(database=self.database) as session:
                result = await session.run(
                    cypher_query,
                    {
                        "query": query,
                        "project_id": project_id,
                        "type_values": type_values,
                        "limit": limit
                    }
                )
                records = await result.fetch(limit)
                
                entities = []
                for record in records:
                    node = record["node"]
                    node_dict = dict(node.items())
                    entity = self._neo4j_to_entity(node_dict)
                    entities.append(entity)
                    
                return entities
        except Exception as e:
            self.metrics["errors"] += 1
            logger.error(f"Error searching entities: {str(e)}")
            # Fall back to basic search if full-text search fails
            try:
                # Fallback to CONTAINS for systems without full-text search
                fallback_query = """
                MATCH (e:Entity)
                WHERE e.name CONTAINS $query
                AND ($project_id IS NULL OR e.project_id = $project_id)
                AND ($type_values IS NULL OR e.type IN $type_values)
                RETURN e
                LIMIT $limit
                """
                
                async with self.driver.session(database=self.database) as session:
                    result = await session.run(
                        fallback_query,
                        {
                            "query": query,
                            "project_id": project_id,
                            "type_values": type_values,
                            "limit": limit
                        }
                    )
                    records = await result.fetch(limit)
                    
                    entities = []
                    for record in records:
                        node = record["e"]
                        node_dict = dict(node.items())
                        entity = self._neo4j_to_entity(node_dict)
                        entities.append(entity)
                        
                    logger.warning(f"Fell back to basic search: {query}")
                    return entities
            except Exception as fallback_error:
                logger.error(f"Error in fallback search: {str(fallback_error)}")
                # Return empty list on complete failure
                return []
                
    @retry_on_exception()
    async def get_relationship(
        self,
        relationship_id: str,
        project_id: Optional[str] = None
    ) -> Optional[Relationship]:
        """
        Get a relationship by ID.
        
        Args:
            relationship_id: ID of the relationship to retrieve
            project_id: Optional project ID for isolation
            
        Returns:
            Relationship if found, None otherwise
        """
        if not self.driver:
            await self.initialize()
            
        # Create query with parameters
        query = """
        MATCH (source)-[r:RELATES_TO {id: $rel_id}]->(target)
        WHERE $project_id IS NULL OR r.project_id = $project_id
        RETURN r, source.id AS source_id, target.id AS target_id
        """
        
        try:
            self.metrics["operations"] += 1
            async with self.driver.session(database=self.database) as session:
                result = await session.run(
                    query, 
                    {
                        "rel_id": relationship_id,
                        "project_id": project_id
                    }
                )
                record = await result.single()
                
                if not record:
                    return None
                    
                # Convert Neo4j relationship to Relationship
                rel = record["r"]
                rel_dict = dict(rel.items())
                rel_dict["source_id"] = record["source_id"]
                rel_dict["target_id"] = record["target_id"]
                
                return self._neo4j_to_relationship(rel_dict)
        except Exception as e:
            self.metrics["errors"] += 1
            logger.error(f"Error retrieving relationship: {str(e)}")
            if "No record found" in str(e):
                return None
            raise
            
    @retry_on_exception()
    async def find_related_entities(
        self,
        entity_id: str,
        project_id: Optional[str] = None,
        max_depth: int = 1,
        min_strength: float = 0.0,
        relationship_types: Optional[List[RelationType]] = None,
        limit: int = 50
    ) -> List[Tuple[Entity, Relationship]]:
        """
        Find entities related to the given entity with filtering.
        
        Args:
            entity_id: ID of the entity to start from
            project_id: Optional project ID for isolation
            max_depth: Maximum traversal depth (1-3 recommended for performance)
            min_strength: Minimum relationship strength
            relationship_types: Optional list of relationship types to include
            limit: Maximum number of related entities to return
            
        Returns:
            List of tuples containing (Entity, Relationship)
        """
        if not self.driver:
            await self.initialize()
            
        # Convert relationship types to values
        rel_type_values = None
        if relationship_types:
            rel_type_values = [rt.value for rt in relationship_types]
            
        # Prepare relationship type filter
        rel_type_filter = ""
        if rel_type_values:
            rel_type_filter = "AND r.type IN $rel_type_values"
            
        # Create query with parameters
        query = f"""
        MATCH path = (start:Entity {{id: $entity_id}})-[r:RELATES_TO*1..{max_depth}]-(related:Entity)
        WHERE 
          ($project_id IS NULL OR start.project_id = $project_id) 
          AND ($project_id IS NULL OR related.project_id = $project_id)
          AND all(rel in r WHERE rel.strength >= $min_strength {rel_type_filter})
        WITH related, r, path
        ORDER BY length(path), related.name
        LIMIT $limit
        MATCH (start:Entity {{id: $entity_id}})-[direct_rel:RELATES_TO]->(related)
        RETURN related, direct_rel
        """
        
        try:
            self.metrics["operations"] += 1
            async with self.driver.session(database=self.database) as session:
                result = await session.run(
                    query, 
                    {
                        "entity_id": entity_id,
                        "project_id": project_id,
                        "min_strength": min_strength,
                        "rel_type_values": rel_type_values,
                        "limit": limit
                    }
                )
                records = await result.fetch(limit)
                
                related_entities = []
                for record in records:
                    entity_node = record["related"]
                    rel = record["direct_rel"]
                    
                    entity_dict = dict(entity_node.items())
                    rel_dict = dict(rel.items())
                    rel_dict["source_id"] = entity_id
                    rel_dict["target_id"] = entity_dict["id"]
                    
                    entity = self._neo4j_to_entity(entity_dict)
                    relationship = self._neo4j_to_relationship(rel_dict)
                    
                    related_entities.append((entity, relationship))
                    
                return related_entities
        except Exception as e:
            self.metrics["errors"] += 1
            logger.error(f"Error finding related entities: {str(e)}")
            raise
            
    @retry_on_exception()
    async def find_shortest_path(
        self,
        source_id: str,
        target_id: str,
        project_id: Optional[str] = None,
        max_depth: int = 4,
        min_strength: float = 0.0
    ) -> Optional[Path]:
        """
        Find shortest path between two entities.
        
        Args:
            source_id: ID of the source entity
            target_id: ID of the target entity
            project_id: Optional project ID for isolation
            max_depth: Maximum traversal depth
            min_strength: Minimum relationship strength
            
        Returns:
            Path object if path exists, None otherwise
        """
        if not self.driver:
            await self.initialize()
            
        # Create query with parameters
        query = f"""
        MATCH path = shortestPath((source:Entity {{id: $source_id}})-[r:RELATES_TO*1..{max_depth}]-(target:Entity {{id: $target_id}}))
        WHERE 
          ($project_id IS NULL OR source.project_id = $project_id) 
          AND ($project_id IS NULL OR target.project_id = $project_id)
          AND all(rel in r WHERE rel.strength >= $min_strength)
        UNWIND nodes(path) AS node
        WITH collect(node) as nodes, relationships(path) as rels
        RETURN nodes, rels
        """
        
        try:
            self.metrics["operations"] += 1
            async with self.driver.session(database=self.database) as session:
                result = await session.run(
                    query, 
                    {
                        "source_id": source_id,
                        "target_id": target_id,
                        "project_id": project_id,
                        "min_strength": min_strength
                    }
                )
                record = await result.single()
                
                if not record:
                    return None
                    
                # Convert path to entities and relationships
                node_list = record["nodes"]
                rel_list = record["rels"]
                
                entities = []
                relationships = []
                
                # Convert nodes to entities
                for node in node_list:
                    node_dict = dict(node.items())
                    entity = self._neo4j_to_entity(node_dict)
                    entities.append(entity)
                    
                # Convert relationships
                prev_node = None
                for i, rel in enumerate(rel_list):
                    rel_dict = dict(rel.items())
                    
                    # Get source and target IDs from the path
                    if i < len(node_list) - 1:
                        source_node = node_list[i]
                        target_node = node_list[i + 1]
                        rel_dict["source_id"] = source_node["id"]
                        rel_dict["target_id"] = target_node["id"]
                        
                    relationship = self._neo4j_to_relationship(rel_dict)
                    relationships.append(relationship)
                    
                return Path(entities=entities, relationships=relationships)
        except Exception as e:
            self.metrics["errors"] += 1
            logger.error(f"Error finding shortest path: {str(e)}")
            if "No record found" in str(e):
                return None
            raise
            
    @retry_on_exception()
    async def delete_entity(
        self,
        entity_id: str,
        project_id: Optional[str] = None,
        cascade: bool = False
    ) -> bool:
        """
        Delete an entity from the knowledge graph.
        
        Args:
            entity_id: ID of the entity to delete
            project_id: Optional project ID for isolation
            cascade: If True, delete all related relationships
            
        Returns:
            True if successful, False otherwise
        """
        if not self.driver:
            await self.initialize()
            
        try:
            self.metrics["operations"] += 1
            async with self.driver.session(database=self.database) as session:
                if cascade:
                    # Delete entity and all connected relationships
                    query = """
                    MATCH (e:Entity {id: $entity_id})
                    WHERE $project_id IS NULL OR e.project_id = $project_id
                    OPTIONAL MATCH (e)-[r]-()
                    DELETE r, e
                    RETURN count(e) as deleted
                    """
                else:
                    # Delete only if no relationships exist
                    query = """
                    MATCH (e:Entity {id: $entity_id})
                    WHERE $project_id IS NULL OR e.project_id = $project_id
                    AND NOT (e)-[]-()
                    DELETE e
                    RETURN count(e) as deleted
                    """
                    
                result = await session.run(
                    query, 
                    {
                        "entity_id": entity_id,
                        "project_id": project_id
                    }
                )
                record = await result.single()
                
                deleted = record and record.get("deleted", 0) > 0
                if deleted:
                    logger.debug(f"Entity deleted: {entity_id}")
                else:
                    logger.warning(f"Entity not deleted (may have relationships): {entity_id}")
                    
                return deleted
        except Exception as e:
            self.metrics["errors"] += 1
            logger.error(f"Error deleting entity: {str(e)}")
            raise
            
    @retry_on_exception()
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
        if not self.driver:
            await self.initialize()
            
        # Create query with parameters
        query = """
        MATCH ()-[r:RELATES_TO {id: $rel_id}]->()
        WHERE $project_id IS NULL OR r.project_id = $project_id
        DELETE r
        RETURN count(r) as deleted
        """
        
        try:
            self.metrics["operations"] += 1
            async with self.driver.session(database=self.database) as session:
                result = await session.run(
                    query, 
                    {
                        "rel_id": relationship_id,
                        "project_id": project_id
                    }
                )
                record = await result.single()
                
                deleted = record and record.get("deleted", 0) > 0
                if deleted:
                    logger.debug(f"Relationship deleted: {relationship_id}")
                    
                return deleted
        except Exception as e:
            self.metrics["errors"] += 1
            logger.error(f"Error deleting relationship: {str(e)}")
            raise
            
    @retry_on_exception()
    async def get_graph_stats(
        self,
        project_id: Optional[str] = None
    ) -> GraphStats:
        """
        Get statistics about the knowledge graph.
        
        Args:
            project_id: Optional project ID for isolation
            
        Returns:
            GraphStats object with metrics
        """
        if not self.driver:
            await self.initialize()
            
        # Create query with parameters
        query = """
        MATCH (e:Entity)
        WHERE $project_id IS NULL OR e.project_id = $project_id
        WITH count(e) as entity_count
        MATCH ()-[r:RELATES_TO]->()
        WHERE $project_id IS NULL OR r.project_id = $project_id
        RETURN entity_count, count(r) as relationship_count
        """
        
        # Entity type distribution query
        type_query = """
        MATCH (e:Entity)
        WHERE $project_id IS NULL OR e.project_id = $project_id
        RETURN e.type as type, count(e) as count
        ORDER BY count DESC
        """
        
        # Most connected entities query
        connected_query = """
        MATCH (e:Entity)
        WHERE $project_id IS NULL OR e.project_id = $project_id
        WITH e, size((e)-[:RELATES_TO]-()) as connection_count
        RETURN e.id as id, e.name as name, e.type as type, connection_count
        ORDER BY connection_count DESC
        LIMIT 10
        """
        
        try:
            self.metrics["operations"] += 1
            async with self.driver.session(database=self.database) as session:
                # Get basic counts
                result = await session.run(
                    query, 
                    {
                        "project_id": project_id
                    }
                )
                record = await result.single()
                
                entity_count = record["entity_count"] if record else 0
                relationship_count = record["relationship_count"] if record else 0
                
                # Get entity type distribution
                type_result = await session.run(
                    type_query,
                    {
                        "project_id": project_id
                    }
                )
                type_records = await type_result.fetch()
                
                type_distribution = {}
                for record in type_records:
                    type_name = record["type"]
                    count = record["count"]
                    type_distribution[type_name] = count
                
                # Get most connected entities
                connected_result = await session.run(
                    connected_query,
                    {
                        "project_id": project_id
                    }
                )
                connected_records = await connected_result.fetch(10)
                
                most_connected = []
                for record in connected_records:
                    most_connected.append({
                        "id": record["id"],
                        "name": record["name"],
                        "type": record["type"],
                        "connection_count": record["connection_count"]
                    })
                
                # Calculate graph density for connected graph
                # Density = actual edges / potential edges
                # For directed graph: potential edges = n * (n - 1)
                density = 0
                if entity_count > 1:
                    potential_edges = entity_count * (entity_count - 1)
                    density = relationship_count / potential_edges if potential_edges > 0 else 0
                
                return GraphStats(
                    entity_count=entity_count,
                    relationship_count=relationship_count,
                    entity_type_distribution=type_distribution,
                    most_connected_entities=most_connected,
                    density=density,
                    project_id=project_id
                )
        except Exception as e:
            self.metrics["errors"] += 1
            logger.error(f"Error getting graph stats: {str(e)}")
            raise
            
    @retry_on_exception()
    async def delete_project_graph(self, project_id: str) -> bool:
        """
        Delete all entities and relationships for a project.
        
        Args:
            project_id: Project ID to delete
            
        Returns:
            True if successful, False otherwise
        """
        if not self.driver:
            await self.initialize()
            
        if not project_id:
            raise ValueError("project_id is required")
            
        # Create query with parameters - delete relationships first, then entities
        query = """
        MATCH (e:Entity {project_id: $project_id})
        OPTIONAL MATCH (e)-[r]-()
        WITH e, collect(r) as rels
        FOREACH (rel IN rels | DELETE rel)
        DELETE e
        RETURN count(e) as deleted
        """
        
        try:
            self.metrics["operations"] += 1
            async with self.driver.session(database=self.database) as session:
                result = await session.run(
                    query, 
                    {
                        "project_id": project_id
                    }
                )
                record = await result.single()
                
                deleted = record and record.get("deleted", 0) > 0
                if deleted:
                    logger.info(f"Project graph deleted: {project_id}")
                    
                return deleted
        except Exception as e:
            self.metrics["errors"] += 1
            logger.error(f"Error deleting project graph: {str(e)}")
            raise
            
    @retry_on_exception()
    async def get_most_central_entities(
        self,
        project_id: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get the most central entities based on betweenness centrality.
        
        Args:
            project_id: Optional project ID for isolation
            limit: Maximum number of central entities to return
            
        Returns:
            List of entities with centrality scores
        """
        if not self.driver:
            await self.initialize()
            
        # Neo4j graph algorithms for centrality
        # Uses built-in graph algorithms
        query = """
        CALL gds.graph.project.cypher(
          'centralityGraph',
          'MATCH (e:Entity) WHERE $project_id IS NULL OR e.project_id = $project_id RETURN id(e) AS id',
          'MATCH (e1:Entity)-[r:RELATES_TO]->(e2:Entity) 
           WHERE ($project_id IS NULL OR e1.project_id = $project_id) 
           AND ($project_id IS NULL OR e2.project_id = $project_id)
           RETURN id(e1) AS source, id(e2) AS target, r.strength as weight'
        )
        YIELD graphName
        
        CALL gds.betweenness.stream('centralityGraph')
        YIELD nodeId, score
        WITH gds.util.asNode(nodeId) as entity, score
        ORDER BY score DESC
        LIMIT $limit
        
        RETURN entity.id as id, entity.name as name, entity.type as type, score
        """
        
        try:
            self.metrics["operations"] += 1
            
            # Try with graph algorithms first
            try:
                async with self.driver.session(database=self.database) as session:
                    result = await session.run(
                        query, 
                        {
                            "project_id": project_id,
                            "limit": limit
                        }
                    )
                    records = await result.fetch(limit)
                    
                    central_entities = []
                    for record in records:
                        central_entities.append({
                            "id": record["id"],
                            "name": record["name"],
                            "type": record["type"],
                            "centrality_score": record["score"]
                        })
                        
                    # Drop the projected graph
                    await session.run("CALL gds.graph.drop('centralityGraph')")
                        
                    return central_entities
                    
            except Exception as alg_error:
                # Fall back to degree centrality if graph algorithms not available
                logger.warning(f"Graph algorithms not available, falling back to degree centrality: {str(alg_error)}")
                
                fallback_query = """
                MATCH (e:Entity)
                WHERE $project_id IS NULL OR e.project_id = $project_id
                WITH e, size((e)-[:RELATES_TO]-()) as degree
                RETURN e.id as id, e.name as name, e.type as type, degree as score
                ORDER BY degree DESC
                LIMIT $limit
                """
                
                async with self.driver.session(database=self.database) as session:
                    fallback_result = await session.run(
                        fallback_query,
                        {
                            "project_id": project_id,
                            "limit": limit
                        }
                    )
                    fallback_records = await fallback_result.fetch(limit)
                    
                    central_entities = []
                    for record in fallback_records:
                        central_entities.append({
                            "id": record["id"],
                            "name": record["name"],
                            "type": record["type"],
                            "centrality_score": record["score"]
                        })
                        
                    return central_entities
        except Exception as e:
            self.metrics["errors"] += 1
            logger.error(f"Error getting central entities: {str(e)}")
            raise
            
    @retry_on_exception()
    async def get_entity_timeline(
        self,
        entity_id: str,
        project_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get timeline of an entity's relationships.
        
        Args:
            entity_id: ID of the entity to get timeline for
            project_id: Optional project ID for isolation
            limit: Maximum number of timeline events to return
            
        Returns:
            List of relationship events sorted by time
        """
        if not self.driver:
            await self.initialize()
            
        # Create query with parameters
        query = """
        MATCH (e:Entity {id: $entity_id})-[r:RELATES_TO]-(other)
        WHERE $project_id IS NULL OR e.project_id = $project_id
        RETURN r, other
        ORDER BY r.created_at DESC
        LIMIT $limit
        """
        
        try:
            self.metrics["operations"] += 1
            async with self.driver.session(database=self.database) as session:
                result = await session.run(
                    query, 
                    {
                        "entity_id": entity_id,
                        "project_id": project_id,
                        "limit": limit
                    }
                )
                records = await result.fetch(limit)
                
                timeline = []
                for record in records:
                    rel = record["r"]
                    other = record["other"]
                    
                    rel_dict = dict(rel.items())
                    other_dict = dict(other.items())
                    
                    # Determine if the entity is the source or target
                    if rel.start_node.id == other.id:
                        rel_dict["source_id"] = other_dict["id"]
                        rel_dict["target_id"] = entity_id
                        direction = "incoming"
                    else:
                        rel_dict["source_id"] = entity_id
                        rel_dict["target_id"] = other_dict["id"]
                        direction = "outgoing"
                    
                    relationship = self._neo4j_to_relationship(rel_dict)
                    other_entity = self._neo4j_to_entity(other_dict)
                    
                    timeline_event = {
                        "timestamp": rel_dict.get("created_at", datetime.now(timezone.utc)),
                        "relationship": relationship,
                        "related_entity": other_entity,
                        "direction": direction
                    }
                    timeline.append(timeline_event)
                
                # Sort by timestamp descending
                timeline.sort(key=lambda x: x["timestamp"], reverse=True)
                return timeline
        except Exception as e:
            self.metrics["errors"] += 1
            logger.error(f"Error getting entity timeline: {str(e)}")
            raise
            
    @retry_on_exception()
    async def update_entity(
        self,
        entity_id: str,
        updates: Dict[str, Any],
        project_id: Optional[str] = None
    ) -> bool:
        """
        Update an entity's properties.
        
        Args:
            entity_id: ID of the entity to update
            updates: Dictionary of properties to update
            project_id: Optional project ID for isolation
            
        Returns:
            True if successful, False otherwise
        """
        if not self.driver:
            await self.initialize()
            
        # Prepare updates
        properties = {}
        for key, value in updates.items():
            if value is not None:
                if isinstance(value, (dict, list)):
                    import json
                    properties[key] = json.dumps(value)
                else:
                    properties[key] = value
        
        # Always update the updated_at timestamp
        properties["updated_at"] = datetime.now(timezone.utc)
        
        # Create query with parameters
        query = """
        MATCH (e:Entity {id: $entity_id})
        WHERE $project_id IS NULL OR e.project_id = $project_id
        SET e += $properties
        RETURN count(e) as updated
        """
        
        try:
            self.metrics["operations"] += 1
            async with self.driver.session(database=self.database) as session:
                result = await session.run(
                    query, 
                    {
                        "entity_id": entity_id,
                        "project_id": project_id,
                        "properties": properties
                    }
                )
                record = await result.single()
                
                updated = record and record.get("updated", 0) > 0
                if updated:
                    logger.debug(f"Entity updated: {entity_id}")
                    
                return updated
        except Exception as e:
            self.metrics["errors"] += 1
            logger.error(f"Error updating entity: {str(e)}")
            raise
            
    @retry_on_exception()
    async def update_relationship(
        self,
        relationship_id: str,
        updates: Dict[str, Any],
        project_id: Optional[str] = None
    ) -> bool:
        """
        Update a relationship's properties.
        
        Args:
            relationship_id: ID of the relationship to update
            updates: Dictionary of properties to update
            project_id: Optional project ID for isolation
            
        Returns:
            True if successful, False otherwise
        """
        if not self.driver:
            await self.initialize()
            
        # Prepare updates
        properties = {}
        for key, value in updates.items():
            if value is not None:
                if isinstance(value, (dict, list)):
                    import json
                    properties[key] = json.dumps(value)
                else:
                    properties[key] = value
        
        # Always update the updated_at timestamp
        properties["updated_at"] = datetime.now(timezone.utc)
        
        # Create query with parameters
        query = """
        MATCH ()-[r:RELATES_TO {id: $rel_id}]->()
        WHERE $project_id IS NULL OR r.project_id = $project_id
        SET r += $properties
        RETURN count(r) as updated
        """
        
        try:
            self.metrics["operations"] += 1
            async with self.driver.session(database=self.database) as session:
                result = await session.run(
                    query, 
                    {
                        "rel_id": relationship_id,
                        "project_id": project_id,
                        "properties": properties
                    }
                )
                record = await result.single()
                
                updated = record and record.get("updated", 0) > 0
                if updated:
                    logger.debug(f"Relationship updated: {relationship_id}")
                    
                return updated
        except Exception as e:
            self.metrics["errors"] += 1
            logger.error(f"Error updating relationship: {str(e)}")
            raise
            
    @retry_on_exception()
    async def get_health_check(self) -> Dict[str, Any]:
        """
        Get health check information for the Neo4j connection.
        
        Returns:
            Dictionary with connection status and metrics
        """
        if not self.driver:
            try:
                await self.initialize()
            except Exception as e:
                return {
                    "status": "error",
                    "message": str(e),
                    "metrics": self.metrics,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
        
        try:
            # Test connection
            connection_ok = await self._verify_connectivity()
            
            # Get database info
            db_info = {}
            async with self.driver.session(database=self.database) as session:
                result = await session.run("CALL dbms.components() YIELD name, versions, edition")
                record = await result.single()
                
                if record:
                    db_info = {
                        "name": record["name"],
                        "version": record["versions"][0],
                        "edition": record["edition"]
                    }
                
            return {
                "status": "healthy" if connection_ok else "unhealthy",
                "database": self.database,
                "uri": self.uri,
                "db_info": db_info,
                "metrics": self.metrics,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            self.metrics["errors"] += 1
            logger.error(f"Error getting health check: {str(e)}")
            
            return {
                "status": "error",
                "message": str(e),
                "metrics": self.metrics,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    @retry_on_exception()
    async def backup_graph(
        self,
        project_id: Optional[str] = None,
        output_format: str = "csv"
    ) -> Dict[str, Any]:
        """
        Create a backup of the knowledge graph.
        
        Args:
            project_id: Optional project ID to backup only one project
            output_format: Output format (csv or json)
            
        Returns:
            Dictionary with backup metadata and file paths
        """
        if not self.driver:
            await self.initialize()
            
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        project_suffix = f"_{project_id}" if project_id else "_all"
        backup_dir = os.path.join(os.getcwd(), "backups", f"graph_backup{project_suffix}_{timestamp}")
        
        # Create backup directory if it doesn't exist
        os.makedirs(backup_dir, exist_ok=True)
        
        # Define backup files
        entity_file = os.path.join(backup_dir, f"entities.{output_format}")
        relationship_file = os.path.join(backup_dir, f"relationships.{output_format}")
        
        # Create query with parameters
        entity_query = """
        MATCH (e:Entity)
        WHERE $project_id IS NULL OR e.project_id = $project_id
        RETURN e
        """
        
        relationship_query = """
        MATCH (source)-[r:RELATES_TO]->(target)
        WHERE $project_id IS NULL OR r.project_id = $project_id
        RETURN r, source.id AS source_id, target.id AS target_id
        """
        
        try:
            self.metrics["operations"] += 1
            
            # Extract entities
            entities = []
            async with self.driver.session(database=self.database) as session:
                entity_result = await session.run(
                    entity_query, 
                    {
                        "project_id": project_id
                    }
                )
                entity_records = await entity_result.fetch()
                
                for record in entity_records:
                    node = record["e"]
                    node_dict = dict(node.items())
                    entity = self._neo4j_to_entity(node_dict)
                    entities.append(entity.dict())
                
            # Extract relationships
            relationships = []
            async with self.driver.session(database=self.database) as session:
                rel_result = await session.run(
                    relationship_query,
                    {
                        "project_id": project_id
                    }
                )
                rel_records = await rel_result.fetch()
                
                for record in rel_records:
                    rel = record["r"]
                    rel_dict = dict(rel.items())
                    rel_dict["source_id"] = record["source_id"]
                    rel_dict["target_id"] = record["target_id"]
                    relationship = self._neo4j_to_relationship(rel_dict)
                    relationships.append(relationship.dict())
            
            # Write to files
            if output_format == "csv":
                import csv
                
                # Write entities to CSV
                if entities:
                    keys = entities[0].keys()
                    with open(entity_file, 'w', newline='') as output_file:
                        dict_writer = csv.DictWriter(output_file, keys)
                        dict_writer.writeheader()
                        dict_writer.writerows(entities)
                
                # Write relationships to CSV
                if relationships:
                    keys = relationships[0].keys()
                    with open(relationship_file, 'w', newline='') as output_file:
                        dict_writer = csv.DictWriter(output_file, keys)
                        dict_writer.writeheader()
                        dict_writer.writerows(relationships)
                        
            else:  # json
                import json
                
                # Write entities to JSON
                with open(entity_file, 'w') as f:
                    json.dump(entities, f, default=str)
                
                # Write relationships to JSON
                with open(relationship_file, 'w') as f:
                    json.dump(relationships, f, default=str)
            
            return {
                "status": "success",
                "timestamp": timestamp,
                "format": output_format,
                "backup_dir": backup_dir,
                "entity_file": entity_file,
                "relationship_file": relationship_file,
                "entity_count": len(entities),
                "relationship_count": len(relationships),
                "project_id": project_id
            }
        except Exception as e:
            self.metrics["errors"] += 1
            logger.error(f"Error creating graph backup: {str(e)}")
            raise
