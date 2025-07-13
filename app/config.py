from functools import lru_cache
from typing import Optional
from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    # Instagram Graph API
    INSTAGRAM_ACCESS_TOKEN: str = Field(..., env="INSTAGRAM_ACCESS_TOKEN")
    INSTAGRAM_ACCOUNT_ID: str = Field(..., env="INSTAGRAM_ACCOUNT_ID")
    VERIFY_TOKEN: str = Field(..., env="VERIFY_TOKEN")
    APP_SECRET: str = Field("", env="APP_SECRET")

    # AI Model config
    GEMINI_API_KEY: Optional[str] = Field(None, env="GEMINI_API_KEY")
    MODEL_NAME: str = Field(..., env="MODEL_NAME")

    BOT_USERNAME: str = Field("z3_agent", env="BOT_USERNAME")

    # Logging
    LOG_LEVEL: str = Field("INFO", env="LOG_LEVEL")

    # Path config
    CONVERSATIONS_PATH: str = Field("data/conversations.json", env="CONVERSATIONS_PATH")

    # Pr path
    REPLY_PROMPT_PATH: str = Field("content/reply-prompt.txt", env="REPLY_PROMPT_PATH")
    SUPERVISOR_PROMPT_PATH: str = Field("content/supervisor-prompt.txt", env="SUPERVISOR_PROMPT_PATH")

    # Graph API Version
    GRAPH_API_VERSION: str = Field("18.0", env="GRAPH_API_VERSION")
    INSTAGRAM_API_BASE_URL: str = Field("https://graph.facebook.com", env="INSTAGRAM_API_BASE_URL")

    #vectorfile
    DOCS_DIR: str = Field("docs", env="DOCS_DIR")
    VECTOR_DIR: str = Field("data/vector_store", env="VECTOR_DIR")

    #Persona
    PERSONALITY_PATH: str = Field("content/personality1.json", env="PERSONALITY_PATH")

    class Config:
        env_file = ".env"
        case_sensitive = False

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()