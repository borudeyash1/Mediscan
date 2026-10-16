"""
Neo4j Knowledge Graph client for SNOMED-CT / RxNorm / DDI traversal.
"""

import structlog
from neo4j import AsyncGraphDatabase

from app.config import settings

logger = structlog.get_logger(__name__)

_driver = None


async def init_neo4j():
    """Initialize the async Neo4j driver."""
    global _driver
    _driver = AsyncGraphDatabase.driver(
        settings.NEO4J_URI,
        auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
    )
    logger.info("neo4j.initialized", uri=settings.NEO4J_URI)


async def close_neo4j():
    """Gracefully close the Neo4j driver."""
    global _driver
    if _driver:
        await _driver.close()
        logger.info("neo4j.closed")


def get_neo4j_driver():
    """Get the Neo4j driver instance."""
    return _driver


async def check_neo4j_health() -> bool:
    """Health check for Neo4j connectivity."""
    try:
        async with _driver.session() as session:
            result = await session.run("RETURN 1 AS health")
            await result.single()
        return True
    except Exception as e:
        logger.error("neo4j.health_check_failed", error=str(e))
        return False
