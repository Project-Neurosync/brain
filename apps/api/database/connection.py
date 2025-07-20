"""
NeuroSync AI Backend - Database Connection
Database connection management and session handling
"""

import logging
from typing import Generator
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager

from config.settings import get_settings
from models.database import Base

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Database connection and session management"""
    
    def __init__(self):
        self.settings = get_settings()
        self.engine = None
        self.SessionLocal = None
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize database engine and session factory"""
        # Create engine with appropriate settings
        engine_kwargs = {
            "echo": self.settings.database_echo,
        }
        
        # Handle SQLite specific settings
        if self.settings.database_url.startswith("sqlite"):
            engine_kwargs.update({
                "poolclass": StaticPool,
                "connect_args": {"check_same_thread": False}
            })
        else:
            # PostgreSQL and other databases support connection pooling
            engine_kwargs.update({
                "pool_size": self.settings.database_pool_size,
                "max_overflow": self.settings.database_max_overflow,
            })
        
        self.engine = create_engine(
            self.settings.database_url,
            **engine_kwargs
        )
        
        # Add connection event listeners
        self._add_connection_listeners()
        
        # Create session factory
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
        
        logger.info("Database connection initialized")
    
    def _add_connection_listeners(self):
        """Add database connection event listeners"""
        
        @event.listens_for(self.engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            """Set SQLite pragmas for better performance and integrity"""
            if self.settings.database_url.startswith("sqlite"):
                cursor = dbapi_connection.cursor()
                # Enable foreign key constraints
                cursor.execute("PRAGMA foreign_keys=ON")
                # Set journal mode to WAL for better concurrency
                cursor.execute("PRAGMA journal_mode=WAL")
                # Set synchronous mode to NORMAL for better performance
                cursor.execute("PRAGMA synchronous=NORMAL")
                cursor.close()
        
        @event.listens_for(self.engine, "before_cursor_execute")
        def log_queries(conn, cursor, statement, parameters, context, executemany):
            """Log database queries in debug mode"""
            if self.settings.debug and logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"SQL Query: {statement}")
                if parameters:
                    logger.debug(f"Parameters: {parameters}")
    
    def create_tables(self):
        """Create all database tables"""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Error creating database tables: {str(e)}")
            raise
    
    @contextmanager
    def get_session(self):
        """Get database session with automatic cleanup"""
        session = self.SessionLocal()
        try:
            yield session
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {str(e)}")
            raise
        finally:
            session.close()
    
    def drop_tables(self):
        """Drop all database tables (use with caution!)"""
        try:
            Base.metadata.drop_all(bind=self.engine)
            logger.info("Database tables dropped successfully")
        except Exception as e:
            logger.error(f"Error dropping database tables: {str(e)}")
            raise
    
    @contextmanager
    def get_session_context(self) -> Generator[Session, None, None]:
        """Get a database session with automatic cleanup"""
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def health_check(self) -> bool:
        """Check database connection health"""
        try:
            with self.get_session_context() as session:
                session.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            return False
    
    def close(self):
        """Close database connections"""
        if self.engine:
            self.engine.dispose()
            logger.info("Database connections closed")

# Global database manager instance
db_manager = DatabaseManager()

def get_database() -> Generator[Session, None, None]:
    """FastAPI dependency for getting database sessions"""
    session = db_manager.get_session()
    try:
        yield session
    finally:
        session.close()

def init_database():
    """Initialize database tables"""
    db_manager.create_tables()

def close_database():
    """Close database connections"""
    db_manager.close()

# Database utilities
def reset_database():
    """Reset database (drop and recreate all tables)"""
    logger.warning("Resetting database - all data will be lost!")
    db_manager.drop_tables()
    db_manager.create_tables()

async def check_database_health() -> dict:
    """Check database health and return status"""
    try:
        is_healthy = db_manager.health_check()
        return {
            "database": "healthy" if is_healthy else "unhealthy",
            "engine": str(db_manager.engine.url).split('@')[0] + '@***' if db_manager.engine else "not_initialized"
        }
    except Exception as e:
        logger.error(f"Database health check error: {str(e)}")
        return {
            "database": "error",
            "error": str(e)
        }
