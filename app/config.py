from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # Instagram Graph API (Optional - channel disabled, focusing on Telegram)
    INSTAGRAM_ACCESS_TOKEN: Optional[str] = Field(None, alias="INSTAGRAM_ACCESS_TOKEN")
    INSTAGRAM_ACCOUNT_ID: Optional[str] = Field(None, alias="INSTAGRAM_ACCOUNT_ID")
    PAGE_ID: Optional[str] = Field(None, alias="PAGE_ID")  # Facebook Page ID for Instagram DM
    VERIFY_TOKEN: Optional[str] = Field(None, alias="VERIFY_TOKEN")
    APP_SECRET: Optional[str] = Field(None, alias="APP_SECRET")
    
    # Telegram Bot API
    TELEGRAM_BOT_TOKEN: Optional[str] = Field(None, alias="TELEGRAM_BOT_TOKEN")
    TELEGRAM_BOT_USERNAME: str = Field("z3_agent_bot", alias="TELEGRAM_BOT_USERNAME")
    TELEGRAM_WEBHOOK_SECRET: Optional[str] = Field(None, alias="TELEGRAM_WEBHOOK_SECRET")
    
    # Telegram Alert Configuration
    TELEGRAM_ALERT_CHAT_ID: Optional[str] = Field(None, alias="TELEGRAM_ALERT_CHAT_ID")

    # Telegram CS Group for HITL Escalation
    TELEGRAM_CS_GROUP_CHAT_ID: Optional[str] = Field(None, alias="TELEGRAM_CS_GROUP_CHAT_ID")
    ALERT_ERROR_RATE_THRESHOLD: float = Field(0.10, alias="ALERT_ERROR_RATE_THRESHOLD")
    ALERT_RESPONSE_TIME_THRESHOLD: float = Field(5.0, alias="ALERT_RESPONSE_TIME_THRESHOLD")  
    ALERT_COOLDOWN_MINUTES: int = Field(15, alias="ALERT_COOLDOWN_MINUTES")
    
    # Telegram Memory Configuration
    TELEGRAM_DB_PATH: str = Field("data/telegram_memory.db", alias="TELEGRAM_DB_PATH")
    DATABASE_URL: Optional[str] = Field(None, alias="DATABASE_URL")  # PostgreSQL connection string (optional, defaults to SQLite)

    # AI Model config
    GEMINI_API_KEY: str = Field(..., alias="GEMINI_API_KEY")
    MODEL_NAME: str = Field(..., alias="MODEL_NAME")
    
    BOT_USERNAME: str = Field("z3_agent", alias="BOT_USERNAME")

    # Agent Mode (social = casual replies only, cs = full CS with RAG/escalation)
    AGENT_MODE: str = Field("social", alias="AGENT_MODE")

    # =========================================================================
    # RAG Configuration (previously in configs/rag/default.yaml)
    # =========================================================================

    # Embedding Model
    EMBEDDING_MODEL: str = Field(
        "sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
        alias="EMBEDDING_MODEL"
    )

    # Document Chunking
    CHUNK_SIZE: int = Field(500, alias="CHUNK_SIZE")
    CHUNK_OVERLAP: int = Field(50, alias="CHUNK_OVERLAP")

    # Retrieval
    RETRIEVAL_K: int = Field(7, alias="RETRIEVAL_K")

    # Reranker (BGE cross-encoder)
    USE_RERANKER: bool = Field(True, alias="USE_RERANKER")
    RERANKER_MODEL: str = Field("BAAI/bge-reranker-base", alias="RERANKER_MODEL")
    RERANKER_TOP_K: int = Field(3, alias="RERANKER_TOP_K")
    RERANKER_USE_FP16: bool = Field(True, alias="RERANKER_USE_FP16")

    # Relevance Threshold
    RELEVANCE_THRESHOLD: float = Field(1.0, alias="RELEVANCE_THRESHOLD")

    # Adaptive Fallback
    ENABLE_ADAPTIVE_FALLBACK: bool = Field(True, alias="ENABLE_ADAPTIVE_FALLBACK")
    ADAPTIVE_FALLBACK_THRESHOLD_HIGH: float = Field(0.3, alias="ADAPTIVE_FALLBACK_THRESHOLD_HIGH")
    ADAPTIVE_FALLBACK_THRESHOLD_LOW: float = Field(0.2, alias="ADAPTIVE_FALLBACK_THRESHOLD_LOW")

    # Unified Processor
    USE_UNIFIED_PROCESSOR: bool = Field(True, alias="USE_UNIFIED_PROCESSOR")
    UNIFIED_PROCESSOR_PROMPT_PATH: str = Field(
        "prompts/unified_processor_prompt.txt",
        alias="UNIFIED_PROCESSOR_PROMPT_PATH"
    )
    UNIFIED_PROCESSOR_TEMPERATURE: float = Field(0.3, alias="UNIFIED_PROCESSOR_TEMPERATURE")

    # Quality Gate Thresholds
    QUALITY_GATE_THRESHOLD_GOOD: float = Field(0.5, alias="QUALITY_GATE_THRESHOLD_GOOD")
    QUALITY_GATE_THRESHOLD_MEDIUM: float = Field(0.0, alias="QUALITY_GATE_THRESHOLD_MEDIUM")

    # Reply Generation
    REPLY_TEMPERATURE: float = Field(0.7, alias="REPLY_TEMPERATURE")

    # Logging
    LOG_LEVEL: str = Field("INFO", alias="LOG_LEVEL")
    
    # Request Logging Configuration
    REQUEST_LOG_FILE: str = Field("logs/requests.jsonl", alias="REQUEST_LOG_FILE")
    REQUEST_LOG_MAX_QUERY_LENGTH: int = Field(100, alias="REQUEST_LOG_MAX_QUERY_LENGTH")

    # Path config
    CONVERSATIONS_PATH: str = Field("data/conversations.json", alias="CONVERSATIONS_PATH")

    # Pr path
    REPLY_PROMPT_PATH: str = Field("content/reply-prompt.txt", alias="REPLY_PROMPT_PATH")
    SUPERVISOR_PROMPT_PATH: str = Field("content/supervisor-prompt.txt", alias="SUPERVISOR_PROMPT_PATH")

    # Graph API Version
    GRAPH_API_VERSION: str = Field("24.0", alias="GRAPH_API_VERSION")
    INSTAGRAM_API_BASE_URL: str = Field("https://graph.facebook.com", alias="INSTAGRAM_API_BASE_URL")

    #vectorfile
    DOCS_DIR: str = Field("docs", alias="DOCS_DIR")
    VECTOR_DIR: str = Field("data/vector_store", alias="VECTOR_DIR")

    #Persona
    PERSONALITY_PATH: str = Field("content/personality1.json", alias="PERSONALITY_PATH")

    # Reply Configuration
    REPLY_CONFIG_PATH: str = Field("content/reply_config1.json", alias="REPLY_CONFIG_PATH")
    SOCIAL_PROMPT_PATH: str = Field("templates/social_prompt.txt", alias="SOCIAL_PROMPT_PATH")

    # CORS (comma-separated origins for frontend access)
    CORS_ORIGINS: str = Field("http://localhost:3000", alias="CORS_ORIGINS")

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }

# Disable cache to force reload .env
def get_settings() -> Settings:
    return Settings()

# public instance
settings: Settings = get_settings()