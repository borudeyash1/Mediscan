"""
PostgreSQL async database pool management via SQLAlchemy 2.0.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import text

from app.config import settings

logger = structlog.get_logger(__name__)

_engine = None
_session_factory = None


async def init_db_pools():
    """Initialize the async PostgreSQL connection pool."""
    global _engine, _session_factory
    _engine = create_async_engine(
        settings.pg_clinical_dsn,
        pool_size=20,
        max_overflow=10,
        pool_pre_ping=True,
        echo=settings.DEBUG,
    )
    _session_factory = async_sessionmaker(_engine, class_=AsyncSession, expire_on_commit=False)
    logger.info("database.pool_initialized", dsn=settings.PG_CLINICAL_HOST)


async def close_db_pools():
    """Gracefully close the database engine."""
    global _engine
    if _engine:
        await _engine.dispose()
        logger.info("database.pool_closed")


async def get_session() -> AsyncSession:
    """Dependency for getting an async database session."""
    async with _session_factory() as session:
        yield session


async def check_pg_health() -> bool:
    """Health check for PostgreSQL connectivity."""
    try:
        async with _engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error("database.health_check_failed", error=str(e))
        return False
