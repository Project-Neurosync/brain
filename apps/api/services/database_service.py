"""
NeuroSync Database Service
Comprehensive database service integrating PostgreSQL, ChromaDB, Redis, and Neo4j
"""

import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import redis
import chromadb
from chromadb.config import Settings as ChromaSettings

from config.settings import get_settings
from database.connection import DatabaseManager

logger = logging.getLogger(__name__)

class DatabaseService:
    """Unified database service for all NeuroSync data operations"""
    
    def __init__(self):
        self.settings = get_settings()
        self.db_manager = DatabaseManager()
        self.redis_client = None
        self.chroma_client = None
        self.neo4j_driver = None
        
    async def initialize(self):
        """Initialize all database connections"""
        logger.info("Initializing NeuroSync Database Service...")
        
        # Initialize PostgreSQL
        await self._init_postgresql()
        
        # Initialize Redis
        await self._init_redis()
        
        # Initialize ChromaDB
        await self._init_chromadb()
        
        # Initialize Neo4j (optional)
        await self._init_neo4j()
        
        logger.info("All databases initialized successfully!")
    
    def get_db_session(self):
        """Get database session context manager"""
        return self.db_manager.get_session()
    
    async def _init_postgresql(self):
        """Initialize PostgreSQL connection"""
        try:
            # Create tables using the database manager
            self.db_manager.create_tables()
            logger.info("✅ PostgreSQL initialized")
        except Exception as e:
            logger.error(f"❌ PostgreSQL initialization failed: {str(e)}")
            raise
    
    async def _init_redis(self):
        """Initialize Redis connection"""
        try:
            self.redis_client = redis.from_url(
                self.settings.redis_url,
                max_connections=self.settings.redis_max_connections,
                decode_responses=self.settings.redis_decode_responses
            )
            # Test connection
            await self.redis_client.ping()
            logger.info("✅ Redis initialized")
        except Exception as e:
            logger.warning(f"⚠️ Redis initialization failed: {str(e)} - Continuing without Redis")
            self.redis_client = None
    
    async def _init_chromadb(self):
        """Initialize ChromaDB for vector storage"""
        try:
            self.chroma_client = chromadb.PersistentClient(
                path=self.settings.vector_db_path,
                settings=ChromaSettings(allow_reset=self.settings.vector_db_reset)
            )
            # Create default collection if it doesn't exist
            try:
                self.chroma_client.get_collection("neurosync_vectors")
            except:
                self.chroma_client.create_collection("neurosync_vectors")
            
            logger.info("✅ ChromaDB initialized")
        except Exception as e:
            logger.error(f"❌ ChromaDB initialization failed: {str(e)}")
            raise
    
    async def _init_neo4j(self):
        """Initialize Neo4j connection (optional)"""
        try:
            # Import neo4j only if needed to avoid dependency issues
            from neo4j import GraphDatabase
            
            self.neo4j_driver = GraphDatabase.driver(
                self.settings.neo4j_uri,
                auth=(self.settings.neo4j_user, self.settings.neo4j_password)
            )
            # Test connection
            with self.neo4j_driver.session() as session:
                session.run("RETURN 1")
            
            logger.info("✅ Neo4j initialized")
        except ImportError:
            logger.info("ℹ️ Neo4j driver not installed - skipping Neo4j initialization")
            self.neo4j_driver = None
        except Exception as e:
            logger.warning(f"⚠️ Neo4j initialization failed: {str(e)} - Continuing without Neo4j")
            self.neo4j_driver = None
    
    # PostgreSQL Operations
    def get_db_session(self):
        """Get PostgreSQL database session"""
        return self.db_manager.get_session()
    
    # Redis Operations
    async def cache_set(self, key: str, value: Any, expire: int = 3600):
        """Set value in Redis cache"""
        if not self.redis_client:
            return False
        
        try:
            serialized_value = json.dumps(value) if not isinstance(value, str) else value
            return await self.redis_client.setex(key, expire, serialized_value)
        except Exception as e:
            logger.error(f"Redis cache set error: {str(e)}")
            return False
    
    async def cache_get(self, key: str):
        """Get value from Redis cache"""
        if not self.redis_client:
            return None
        
        try:
            value = await self.redis_client.get(key)
            if value:
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value
            return None
        except Exception as e:
            logger.error(f"Redis cache get error: {str(e)}")
            return None
    
    # ChromaDB Operations
    def vector_search(self, query_text: str, n_results: int = 5):
        """Search vectors in ChromaDB"""
        if not self.chroma_client:
            return []
        
        try:
            collection = self.chroma_client.get_collection("neurosync_vectors")
            results = collection.query(
                query_texts=[query_text],
                n_results=n_results
            )
            return results
        except Exception as e:
            logger.error(f"Vector search error: {str(e)}")
            return []
    
    def vector_add(self, documents: List[str], metadatas: List[Dict], ids: List[str]):
        """Add vectors to ChromaDB"""
        if not self.chroma_client:
            return False
        
        try:
            collection = self.chroma_client.get_collection("neurosync_vectors")
            collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            return True
        except Exception as e:
            logger.error(f"Vector add error: {str(e)}")
            return False
    
    # Neo4j Operations
    def graph_query(self, query: str, parameters: Dict = None):
        """Execute Neo4j graph query"""
        if not self.neo4j_driver:
            return []
        
        try:
            with self.neo4j_driver.session() as session:
                result = session.run(query, parameters or {})
                return [record.data() for record in result]
        except Exception as e:
            logger.error(f"Graph query error: {str(e)}")
            return []
    
    async def health_check(self):
        """Check health of all database connections"""
        health = {
            "postgresql": False,
            "redis": False,
            "chromadb": False,
            "neo4j": False
        }
        
        # PostgreSQL health check
        try:
            with self.db_manager.get_session() as session:
                session.execute("SELECT 1")
            health["postgresql"] = True
        except Exception as e:
            logger.error(f"PostgreSQL health check failed: {str(e)}")
        
        # Redis health check
        if self.redis_client:
            try:
                await self.redis_client.ping()
                health["redis"] = True
            except Exception as e:
                logger.error(f"Redis health check failed: {str(e)}")
        
        # ChromaDB health check
        if self.chroma_client:
            try:
                self.chroma_client.heartbeat()
                health["chromadb"] = True
            except Exception as e:
                logger.error(f"ChromaDB health check failed: {str(e)}")
        
        # Neo4j health check
        if self.neo4j_driver:
            try:
                with self.neo4j_driver.session() as session:
                    session.run("RETURN 1")
                health["neo4j"] = True
            except Exception as e:
                logger.error(f"Neo4j health check failed: {str(e)}")
        
        return health
    
    async def close(self):
        """Close all database connections"""
        if self.redis_client:
            await self.redis_client.close()
        
        if self.neo4j_driver:
            self.neo4j_driver.close()
        
        logger.info("All database connections closed")

# Global database service instance
db_service = DatabaseService()
