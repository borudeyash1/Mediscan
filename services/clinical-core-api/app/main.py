"""
MediScan Enterprise — Clinical Core API
========================================
Modular, domain-driven FastAPI service consolidating:
  - Medical Copilot & Ambient Scribe
  - Multimodal Diagnostic Orchestrator
  - Document Vision & Lab Parser
  - Clinical Decision Support & Pharmacology
  - FHIR R4 Interoperability Hub
"""

from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import (
    copilot,
    cds_pharmacology,
    diagnosis,
    document_vision,
    fhir_interop,
    telemetry,
    population_health,
)
from app.middleware.audit import AuditMiddleware

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup & shutdown lifecycle."""
    logger.info(
        "clinical_core_api.starting",
        environment=settings.ENVIRONMENT,
        version=settings.APP_VERSION,
    )
    # Startup: initialize database pools, caches, Kafka producers
    from app.infrastructure.database import init_db_pools
    from app.infrastructure.cache import init_redis
    from app.infrastructure.neo4j_client import init_neo4j
    from app.infrastructure.qdrant_client import init_qdrant
    from app.infrastructure.ollama_router import clinical_router

    await init_db_pools()
    await init_redis()
    await init_neo4j()
    await init_qdrant()
    await clinical_router.initialize()

    logger.info("clinical_core_api.ready", msg="All infrastructure connections established")
    yield

    # Shutdown: graceful cleanup
    logger.info("clinical_core_api.shutting_down")
    from app.infrastructure.database import close_db_pools
    from app.infrastructure.cache import close_redis
    from app.infrastructure.neo4j_client import close_neo4j

    await close_db_pools()
    await close_redis()
    await close_neo4j()


def create_app() -> FastAPI:
    """Factory function to create and configure the FastAPI application."""
    app = FastAPI(
        title="MediScan Clinical Core API",
        description="Enterprise Clinical Intelligence & Autonomous Healthcare Platform — Core API Service",
        version=settings.APP_VERSION,
        docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
        redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
        lifespan=lifespan,
    )

    # --- Middleware ---
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(AuditMiddleware)

    # --- WebSocket Streaming Endpoints ---
    from domains.copilot_voice.ambient_scribe import handle_ambient_scribe_ws
    from fastapi import WebSocket

    @app.websocket("/ws/v2/ambient-scribe/{encounter_id}")
    async def ambient_scribe_websocket(websocket: WebSocket, encounter_id: str):
        await handle_ambient_scribe_ws(websocket, encounter_id)

    # --- Domain Routers ---
    app.include_router(copilot.router, prefix="/api/v2/copilot", tags=["Medical Copilot"])
    app.include_router(diagnosis.router, prefix="/api/v2", tags=["Multimodal Diagnosis"])
    app.include_router(diagnosis.router, prefix="/api/v2/diagnosis", tags=["Multimodal Diagnosis"])
    app.include_router(document_vision.router, prefix="/api/v2/documents", tags=["Document Vision"])
    app.include_router(cds_pharmacology.router, prefix="/api/v2/cds", tags=["CDS Pharmacology"])
    app.include_router(telemetry.router, prefix="/api/v2/telemetry", tags=["Wearable RPM"])
    app.include_router(population_health.router, prefix="/api/v2/population-health", tags=["Population Health"])
    app.include_router(fhir_interop.router, prefix="/fhir/r4", tags=["FHIR R4 Interoperability"])
    app.include_router(fhir_interop.router, tags=["CDS Hooks & ABDM"])

    # --- Health Check ---
    @app.get("/health", tags=["System"])
    async def health_check():
        return {
            "status": "healthy",
            "service": "clinical-core-api",
            "version": settings.APP_VERSION,
        }

    @app.get("/ready", tags=["System"])
    async def readiness_check():
        """Deep readiness check — verifies all downstream dependencies."""
        from app.infrastructure.database import check_pg_health
        from app.infrastructure.cache import check_redis_health
        from app.infrastructure.neo4j_client import check_neo4j_health
        from app.infrastructure.qdrant_client import check_qdrant_health
        from app.infrastructure.ollama_router import clinical_router

        checks = {
            "postgres": await check_pg_health(),
            "redis": await check_redis_health(),
            "neo4j": await check_neo4j_health(),
            "qdrant": await check_qdrant_health(),
            "ollama_models": list(clinical_router._available_models) if clinical_router._available_models else "discovering",
        }
        all_healthy = all(v is True for k, v in checks.items() if k != "ollama_models")
        return {
            "status": "ready" if all_healthy else "degraded",
            "checks": checks,
        }

    return app


app = create_app()
