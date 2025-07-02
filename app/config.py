"""
Centralised configuration using **Pydantic BaseSettings**.
All variables are sourced from environment (.env in dev / Secret Manager in prod).
"""

from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    # -------------------------------------------------- Core
    ENV: str = Field("local", description="Environment name (local/staging/prod)")

    # -------------------------------------------------- Instagram Graph
    INSTAGRAM_ACCESS_TOKEN: str = Field(..., env="INSTAGRAM_ACCESS_TOKEN")
    APP_SECRET: str = Field(..., env="APP_SECRET")
    VERIFY_TOKEN: str = Field(..., env="VERIFY_TOKEN")
    BOT_USERNAME: str = Field("z3_agent", env="BOT_USERNAME")

    # -------------------------------------------------- LLM back‑ends (Gemini / OpenAI / etc.)
    GEMINI_API_KEY: Optional[str] = Field(None, env="GEMINI_API_KEY")
    OPENAI_API_KEY: Optional[str] = Field(None, env="OPENAI_API_KEY")
    MODEL_NAME: str = Field("gemini-pro", env="MODEL_NAME")

    # -------------------------------------------------- Logging
    LOG_LEVEL: str = Field("INFO", env="LOG_LEVEL")

    # -------------------------------------------------- Paths / persistence
    BASE_DIR: Path = Path(__file__).resolve().parent
    PERSONALITY_PATH: str = Field(
        default_factory=lambda: str(Path(__file__).resolve().parent / "personality1.json"),
        env="PERSONALITY_PATH",
    )
    CONVERSATIONS_PATH: str = Field("conversations.json", env="CONVERSATIONS_PATH")

    # Vector / database back‑end
    VECTOR_BACKEND: str = Field("faiss", env="VECTOR_BACKEND")  # faiss / pinecone / chroma
    S3_BUCKET_PROMPTS: Optional[str] = Field(None, env="S3_BUCKET_PROMPTS")

    # -------------------------------------------------- Pydantic config
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> "Settings":
    """Singleton accessor so Settings is parsed only once per process."""
    return Settings()


# ---------------------------------------------------------------------------
# Shortcut import for convenience, e.g.:
#   from app.config import settings
# ---------------------------------------------------------------------------
settings = get_settings()