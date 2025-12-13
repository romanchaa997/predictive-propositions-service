"""Database configuration and session management."""
import os
from typing import Generator
from sqlalchemy import create_engine, event, Engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool, QueuePool
import logging

logger = logging.getLogger(__name__)


class DatabaseConfig:
    """Database configuration settings."""
    
    # PostgreSQL connection string from environment or default
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql://user:password@localhost:5432/predictive_propositions"
    )
    
    # Connection pool settings
    POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "20"))
    MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "10"))
    POOL_TIMEOUT = int(os.getenv("DB_POOL_TIMEOUT", "30"))
    POOL_RECYCLE = int(os.getenv("DB_POOL_RECYCLE", "3600"))  # Recycle connections every hour
    
    # Use NullPool for serverless/stateless environments
    USE_NULL_POOL = os.getenv("USE_NULL_POOL", "false").lower() == "true"
    
    # Echo SQL queries to logs (disable in production)
    ECHO_SQL = os.getenv("ECHO_SQL", "false").lower() == "true"


def get_engine() -> Engine:
    """Create and configure SQLAlchemy engine."""
    
    if DatabaseConfig.USE_NULL_POOL:
        # For serverless environments (Lambda, Cloud Functions)
        engine = create_engine(
            DatabaseConfig.DATABASE_URL,
            echo=DatabaseConfig.ECHO_SQL,
            poolclass=NullPool,
        )
    else:
        # Standard connection pool for persistent servers
        engine = create_engine(
            DatabaseConfig.DATABASE_URL,
            echo=DatabaseConfig.ECHO_SQL,
            poolclass=QueuePool,
            pool_size=DatabaseConfig.POOL_SIZE,
            max_overflow=DatabaseConfig.MAX_OVERFLOW,
            pool_timeout=DatabaseConfig.POOL_TIMEOUT,
            pool_recycle=DatabaseConfig.POOL_RECYCLE,
            connect_args={
                "connect_timeout": 10,
                "application_name": "predictive_propositions"
            }
        )
    
    # Add event listeners for connection monitoring
    @event.listens_for(Engine, "connect")
    def receive_connect(dbapi_conn, connection_record):
        """Set connection parameters on new connections."""
        # Enable UUID support in PostgreSQL
        dbapi_conn.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\"")
        # Set application timezone to UTC
        dbapi_conn.execute("SET timezone TO 'UTC'")
    
    @event.listens_for(Engine, "pool_connect")
    def receive_pool_connect(dbapi_conn, connection_record):
        """Log pool connection events."""
        logger.debug(f"Database connection established from pool")
    
    @event.listens_for(Engine, "close")
    def receive_close(dbapi_conn, connection_record):
        """Log connection close events."""
        logger.debug(f"Database connection closed")
    
    return engine


# Create engine and session factory
engine = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Dependency injection function for FastAPI.
    
    Usage:
        @app.get("/")
        def read_root(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database and create all tables."""
    from .models import Base
    
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")


def drop_db():
    """Drop all database tables (WARNING: Destructive operation)."""
    from .models import Base
    
    logger.warning("Dropping all database tables...")
    Base.metadata.drop_all(bind=engine)
    logger.warning("All database tables dropped")


class AsyncDatabaseManager:
    """Manages asynchronous database operations for long-running tasks."""
    
    @staticmethod
    async def execute_bulk_insert(records: list, model_class):
        """Execute bulk insert operation."""
        db = SessionLocal()
        try:
            db.bulk_insert_mappings(model_class, records)
            db.commit()
            logger.info(f"Bulk inserted {len(records)} {model_class.__name__} records")
        except Exception as e:
            db.rollback()
            logger.error(f"Bulk insert failed: {str(e)}")
            raise
        finally:
            db.close()
    
    @staticmethod
    async def execute_bulk_update(updates: dict, model_class):
        """Execute bulk update operation."""
        db = SessionLocal()
        try:
            # updates format: {filter_criteria: update_values}
            db.query(model_class).filter_by(**updates['filter']).update(updates['values'])
            db.commit()
            logger.info(f"Bulk updated records in {model_class.__name__}")
        except Exception as e:
            db.rollback()
            logger.error(f"Bulk update failed: {str(e)}")
            raise
        finally:
            db.close()
