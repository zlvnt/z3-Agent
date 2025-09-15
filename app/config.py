from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # Instagram Graph API
    INSTAGRAM_ACCESS_TOKEN: str = Field(..., alias="INSTAGRAM_ACCESS_TOKEN")
    INSTAGRAM_ACCOUNT_ID: str = Field(..., alias="INSTAGRAM_ACCOUNT_ID")
    VERIFY_TOKEN: str = Field(..., alias="VERIFY_TOKEN")
    APP_SECRET: str = Field(..., alias="APP_SECRET")
    
    # Telegram Bot API
    TELEGRAM_BOT_TOKEN: Optional[str] = Field(None, alias="TELEGRAM_BOT_TOKEN")
    TELEGRAM_BOT_USERNAME: str = Field("z3_agent_bot", alias="TELEGRAM_BOT_USERNAME")
    TELEGRAM_WEBHOOK_SECRET: Optional[str] = Field(None, alias="TELEGRAM_WEBHOOK_SECRET")
    
    # Telegram Alert Configuration
    TELEGRAM_ALERT_CHAT_ID: Optional[str] = Field(None, alias="TELEGRAM_ALERT_CHAT_ID")
    ALERT_ERROR_RATE_THRESHOLD: float = Field(0.10, alias="ALERT_ERROR_RATE_THRESHOLD")
    ALERT_RESPONSE_TIME_THRESHOLD: float = Field(5.0, alias="ALERT_RESPONSE_TIME_THRESHOLD")  
    ALERT_COOLDOWN_MINUTES: int = Field(15, alias="ALERT_COOLDOWN_MINUTES")
    
    # Telegram Memory Configuration
    TELEGRAM_DB_PATH: str = Field("data/telegram_memory.db", alias="TELEGRAM_DB_PATH")

    # AI Model config
    GEMINI_API_KEY: Optional[str] = Field(None, alias="GEMINI_API_KEY")
    MODEL_NAME: str = Field(..., alias="MODEL_NAME")
    
    # HuggingFace Embedding Model (local, no API key needed)
    EMBEDDING_MODEL: str = Field("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2", alias="EMBEDDING_MODEL")

    BOT_USERNAME: str = Field("z3_agent", alias="BOT_USERNAME")

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
    GRAPH_API_VERSION: str = Field("18.0", alias="GRAPH_API_VERSION")
    INSTAGRAM_API_BASE_URL: str = Field("https://graph.facebook.com", alias="INSTAGRAM_API_BASE_URL")

    #vectorfile
    DOCS_DIR: str = Field("docs", alias="DOCS_DIR")
    VECTOR_DIR: str = Field("data/vector_store", alias="VECTOR_DIR")

    #Persona
    PERSONALITY_PATH: str = Field("content/personality1.json", alias="PERSONALITY_PATH")

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