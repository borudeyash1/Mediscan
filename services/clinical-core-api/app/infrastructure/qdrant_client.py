"""
Qdrant Vector Database client for Hybrid Clinical RAG.
"""

import structlog
from qdrant_client import QdrantClient as SyncQdrantClient
from qdrant_client import AsyncQdrantClient

from app.config import settings

logger = structlog.get_logger(__name__)

_async_client = None
_sync_client = None


async def init_qdrant():
    """Initialize the async Qdrant client."""
    global _async_client, _sync_client
    _async_client = AsyncQdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)
    _sync_client = SyncQdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)
    logger.info("qdrant.initialized", host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)


def get_qdrant_async():
    """Get the async Qdrant client instance."""
    return _async_client


def get_qdrant_sync():
    """Get the sync Qdrant client (for admin operations)."""
    return _sync_client


async def check_qdrant_health() -> bool:
    """Health check for Qdrant connectivity."""
    try:
        collections = await _async_client.get_collections()
        return True
    except Exception as e:
        logger.error("qdrant.health_check_failed", error=str(e))
        return False
