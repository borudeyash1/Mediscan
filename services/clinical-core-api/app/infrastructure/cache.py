"""
Redis / Valkey cache client for Feast online features & rate-limiting.
"""

import structlog
import redis.asyncio as redis

from app.config import settings

logger = structlog.get_logger(__name__)

_redis_client = None


async def init_redis():
    """Initialize the async Redis/Valkey connection."""
    global _redis_client
    _redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    logger.info("redis.initialized", url=settings.REDIS_URL)


async def close_redis():
    """Gracefully close the Redis connection."""
    global _redis_client
    if _redis_client:
        await _redis_client.close()
        logger.info("redis.closed")


def get_redis():
    """Get the Redis client instance."""
    return _redis_client


async def check_redis_health() -> bool:
    """Health check for Redis connectivity."""
    try:
        return await _redis_client.ping()
    except Exception as e:
        logger.error("redis.health_check_failed", error=str(e))
        return False
