"""
MediScan Enterprise — Application Configuration
Centralized settings via pydantic-settings for 12-factor compliance.
"""

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # --- Application ---
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = Field(default="development", description="development | staging | production")
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # --- Security ---
    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173"]
    JWT_SECRET_KEY: str = "mediscan-dev-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 5

    # --- PostgreSQL (Clinical Store) ---
    PG_CLINICAL_HOST: str = "localhost"
    PG_CLINICAL_PORT: int = 5432
    PG_CLINICAL_DB: str = "mediscan_clinical"
    PG_CLINICAL_USER: str = "mediscan_admin"
    PG_CLINICAL_PASSWORD: str = "mediscan_dev_2026"

    @property
    def pg_clinical_dsn(self) -> str:
        return (
            f"postgresql+asyncpg://{self.PG_CLINICAL_USER}:{self.PG_CLINICAL_PASSWORD}"
            f"@{self.PG_CLINICAL_HOST}:{self.PG_CLINICAL_PORT}/{self.PG_CLINICAL_DB}"
        )

    # --- TimescaleDB (Telemetry) ---
    TSDB_HOST: str = "localhost"
    TSDB_PORT: int = 5433
    TSDB_DB: str = "mediscan_telemetry"
    TSDB_USER: str = "mediscan_admin"
    TSDB_PASSWORD: str = "mediscan_dev_2026"

    # --- Redis / Valkey ---
    REDIS_URL: str = "redis://localhost:6379/0"

    # --- Neo4j ---
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "mediscan_dev_2026"

    # --- Qdrant ---
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_GRPC_PORT: int = 6334

    # --- Redpanda / Kafka ---
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:19092"

    # --- Ollama Dual-Engine Local AI ---
    OLLAMA_HOST_URL: str = Field(default="http://localhost:11434", validation_alias="OLLAMA_HOST_URL")
    OLLAMA_DOCKER_URL: str = Field(default="http://host.docker.internal:11434", validation_alias="OLLAMA_DOCKER_URL")
    OLLAMA_MEDICAL_MODEL: str = Field(default="medgemma:4b", validation_alias="OLLAMA_MEDICAL_MODEL")
    OLLAMA_STRUCTURED_MODEL: str = Field(default="qwen2.5-coder:7b", validation_alias="OLLAMA_STRUCTURED_MODEL")
    OLLAMA_EMBED_MODEL: str = Field(default="nomic-embed-text", validation_alias="OLLAMA_EMBED_MODEL")
    QDRANT_VECTOR_SIZE: int = Field(default=768, validation_alias="QDRANT_VECTOR_SIZE")
    OLLAMA_TEMPERATURE: float = Field(default=0.1, validation_alias="OLLAMA_TEMPERATURE")
    OLLAMA_NUM_CTX: int = Field(default=8192, validation_alias="OLLAMA_NUM_CTX")

    model_config = {"env_prefix": "MEDISCAN_", "env_file": ".env", "extra": "ignore"}


settings = Settings()
