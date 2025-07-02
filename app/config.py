"""
Konfigurasi terpusat berbasis Pydantic Settings.
Semua variabel diambil dari environment (.env pada dev / Secret Manager di prod).
"""

from functools import lru_cache
from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    # ────── Core ─────────────────────────────────────────
    ENV: str = Field("local", description="Environment name (local/staging/prod)")

    # Instagram Graph
    INSTAGRAM_ACCESS_TOKEN: str
    APP_SECRET: str
    VERIFY_TOKEN: str
    BOT_USERNAME: str = "z3_agent"

    # LLM (Google Gemini / OpenAI / dll.)
    GEMINI_API_KEY: str | None = None
    OPENAI_API_KEY: str | None = None
    MODEL_NAME: str = "gemini-pro"

    # Logging
    LOG_LEVEL: str = "INFO"

    # Database / Vector store
    VECTOR_BACKEND: str = "faiss"       # faiss / pinecone / chroma
    S3_BUCKET_PROMPTS: str | None = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache
def get_settings() -> Settings:          # pragma: no cover
    """
    Singleton accessor supaya Settings tidak di-re-parse terus.
    """
    return Settings()


# Ekspos langsung singleton untuk import singkat
settings = get_settings()
