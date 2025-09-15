"""
Backend Database Configuration
Direct environment variable configuration for clean service separation.
"""

import os

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker


class BackendConfig:
    """Backend service configuration using environment variables"""

    def __init__(self) -> None:
        self.database_url: str = os.getenv(
            "DATABASE_URL", "postgresql://anime_user:anime_password@localhost:5433/anime_dashboard"
        )
        self.redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")

        # Database connection settings
        self.db_pool_size: int = int(os.getenv("DB_POOL_SIZE", "5"))
        self.db_pool_max_overflow: int = int(os.getenv("DB_POOL_MAX_OVERFLOW", "10"))
        self.db_pool_timeout: int = int(os.getenv("DB_POOL_TIMEOUT", "30"))


# Global configuration instance
config = BackendConfig()


def create_database_engine() -> Engine:
    """Create SQLAlchemy engine with connection pooling"""
    return create_engine(
        config.database_url,
        pool_size=config.db_pool_size,
        max_overflow=config.db_pool_max_overflow,
        pool_timeout=config.db_pool_timeout,
        echo=False,  # Set to True for SQL debugging
    )


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    """Create sessionmaker factory for database sessions"""
    return sessionmaker(bind=engine, expire_on_commit=False)


# Global database components
database_engine = create_database_engine()
SessionLocal = create_session_factory(database_engine)


def get_database_session() -> Session:
    """Get a database session for dependency injection"""
    return SessionLocal()


def test_database_connection() -> bool:
    """Test database connectivity"""
    try:
        from sqlalchemy import text

        with database_engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            return result.fetchone()[0] == 1
    except Exception:
        return False
