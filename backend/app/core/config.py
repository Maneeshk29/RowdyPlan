"""Application configuration using pydantic-settings."""

from typing import Any, Dict, List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Rowdy Plan application settings.

    Values are loaded from environment variables (case-insensitive) and
    fall back to the defaults declared here.  A .env file in the project
    root is loaded automatically when present.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # --- Project metadata ---
    PROJECT_NAME: str = "Rowdy Plan"
    API_PREFIX: str = "/api"

    # --- Database ---
    DATABASE_URL: str = "postgresql+asyncpg://localhost:5432/rowdyplan"

    # --- Redis / Celery ---
    REDIS_URL: str = "redis://localhost:6379"

    # --- Embeddings ---
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION: int = 384

    # --- File uploads ---
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10 MB
    ALLOWED_RESUME_TYPES: List[str] = [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ]

    # --- CORS ---
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000", "http://127.0.0.1:8000"]

    # --- LLM (optional, for explanation generation) ---
    LLM_API_URL: Optional[str] = None
    LLM_API_KEY: Optional[str] = None

    # --- Apify / Handshake ingestion ---
    APIFY_API_TOKEN: Optional[str] = None
    APIFY_HANDSHAKE_ACTOR_ID: Optional[str] = None
    APIFY_HANDSHAKE_TASK_ID: Optional[str] = None
    APIFY_HANDSHAKE_INPUT: Dict[str, Any] = Field(default_factory=dict)
    APIFY_TIMEOUT_SECONDS: int = 300


# Singleton – import this wherever settings are needed.
settings = Settings()
