"""
Database session management with async support.
"""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from app.config import settings
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

logger = logging.getLogger(__name__)


# Create async engine
def get_async_engine() -> AsyncEngine:
    """
    Create and configure async database engine.

    Returns:
        AsyncEngine: Configured async database engine
    """
    # Convert database URL to use asyncpg driver
    db_url = str(settings.database_url).replace("postgresql://", "postgresql+asyncpg://")

    engine = create_async_engine(
        db_url,
        echo=settings.environment == "development",
        pool_pre_ping=True,  # Enable connection health checks
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        pool_recycle=3600,  # Recycle connections after 1 hour
    )
    logger.info(
        "Created async database engine",
        extra={
            "pool_size": settings.db_pool_size,
            "max_overflow": settings.db_max_overflow,
        },
    )
    return engine


# Create engine instance
engine = get_async_engine()

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Don't expire objects after commit
    autoflush=False,  # Disable autoflush for better control
)


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Async context manager for database sessions.

    Provides automatic commit/rollback handling.

    Yields:
        AsyncSession: Database session

    Example:
        async with get_db_session() as session:
            result = await session.execute(select(Model))
            items = result.scalars().all()
    """
    session = AsyncSessionLocal()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for FastAPI routes to get database session.

    Yields:
        AsyncSession: Database session for route handler
    """
    async with get_db_session() as session:
        yield session


async def init_db() -> None:
    """
    Initialize database connection.

    Tests database connectivity and logs connection status.
    """
    from db.base import Base  # noqa: F401

    async with engine.begin() as conn:
        # Test connection
        await conn.execute("SELECT 1")  # type: ignore
    logger.info("Database connection initialized successfully")


async def close_db() -> None:
    """
    Close database connection and dispose of connection pool.
    """
    await engine.dispose()
    logger.info("Database connection closed")
