"""
CCIP Backend Configuration.

Loads settings from environment variables with sensible defaults for development.
"""

from functools import lru_cache
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
ENV_FILE = BACKEND_DIR / ".env"
DEFAULT_DB_FILE = BACKEND_DIR / "ccip_dev.db"


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "CCIP - Campus Career & Curriculum Intelligence Platform"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # Database (defaults to absolute path of ccip_dev.db in backend directory)
    DATABASE_URL: str = f"sqlite+aiosqlite:///{DEFAULT_DB_FILE.as_posix()}"
    DATABASE_ECHO: bool = False

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Auth / JWT
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # UMS Integration Mode
    UMS_MODE: str = "mock"  # "mock" | "api" | "etl"

    # LLM / AI (Basic models & features)
    LLM_PROVIDER: str = "gemini"
    GEMINI_API_KEY: str = ""

    # File Storage
    UPLOAD_DIR: str = str((BACKEND_DIR / "uploads").as_posix())
    MAX_RESUME_SIZE_MB: int = 10

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]

    model_config = {
        "env_file": str(ENV_FILE),
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "extra": "ignore",
    }


@lru_cache()
def get_settings() -> Settings:
    return Settings()
