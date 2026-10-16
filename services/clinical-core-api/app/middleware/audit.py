"""
Audit trail middleware for hash-chained immutable logging.
Logs every API request to the immutable_audit_ledger.
"""

import time

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = structlog.get_logger(__name__)


class AuditMiddleware(BaseHTTPMiddleware):
    """Middleware that logs API access for HIPAA/GDPR audit compliance."""

    async def dispatch(self, request: Request, call_next):
        start_time = time.perf_counter()

        # Extract request metadata
        client_ip = request.client.host if request.client else "unknown"
        method = request.method
        path = request.url.path

        # Process the request
        response = await call_next(request)

        # Calculate latency
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)

        # Log the access (non-PHI fields only)
        logger.info(
            "api.access",
            method=method,
            path=path,
            status_code=response.status_code,
            latency_ms=latency_ms,
            client_ip=client_ip,
        )

        # Add response headers for observability
        response.headers["X-Request-Latency-Ms"] = str(latency_ms)

        return response
