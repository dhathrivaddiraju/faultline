import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="allow")

    PROJECT_NAME: str = "Faultline"
    API_V1_STR: str = "/api/v1"
    
    # Database Settings
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql+asyncpg://postgres:postgres@localhost:5432/faultline"
    )
    SQLITE_FALLBACK_URL: str = "sqlite+aiosqlite:///./faultline.db"
    USE_SQLITE_IF_NO_POSTGRES: bool = True
    
    # Redis Settings
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    REDIS_STREAM_KEY: str = "faultline:events:stream"
    REDIS_QUEUE_KEY: str = "faultline:events:queue"
    USE_MEMORY_QUEUE_IF_NO_REDIS: bool = True
    
    # Ingestion Performance Tunables
    INGESTION_BATCH_SIZE: int = 50
    INGESTION_FLUSH_INTERVAL_MS: int = 200
    
    # AI Error Analysis (Claude 3.5 Sonnet)
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY", None)
    CLAUDE_MODEL: str = os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20241022")
    AI_ANALYSIS_AUTO_TRIGGER: bool = True
    AI_ANALYSIS_MIN_OCCURRENCES: int = 1  # Trigger on new incident or threshold
    
    # CORS & Server
    CORS_ORIGINS: list[str] = ["*"]
    HOST: str = "0.0.0.0"
    PORT: int = 8000

settings = Settings()
