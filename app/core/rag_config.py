"""
RAG Configuration for z3-Agent.

Loads RAG settings from Pydantic Settings (environment variables).
All settings can be configured via env vars for production deployment.
"""

from functools import lru_cache


class RAGConfig:
    """RAG configuration loaded from Pydantic Settings."""

    def __init__(self):
        """Initialize from Pydantic settings."""
        from app.config import settings

        # Embedding settings
        self.embedding_model: str = settings.EMBEDDING_MODEL

        # Chunking settings
        self.chunk_size: int = settings.CHUNK_SIZE
        self.chunk_overlap: int = settings.CHUNK_OVERLAP

        # Retrieval settings
        self.retrieval_k: int = settings.RETRIEVAL_K
        self.relevance_threshold: float = settings.RELEVANCE_THRESHOLD

        # Reranker settings
        self.use_reranker: bool = settings.USE_RERANKER
        self.reranker_model: str = settings.RERANKER_MODEL
        self.reranker_top_k: int = settings.RERANKER_TOP_K
        self.reranker_use_fp16: bool = settings.RERANKER_USE_FP16

        # Adaptive fallback
        self.enable_adaptive_fallback: bool = settings.ENABLE_ADAPTIVE_FALLBACK
        self.adaptive_fallback_threshold_high: float = settings.ADAPTIVE_FALLBACK_THRESHOLD_HIGH
        self.adaptive_fallback_threshold_low: float = settings.ADAPTIVE_FALLBACK_THRESHOLD_LOW

        # Unified Processor
        self.use_unified_processor: bool = settings.USE_UNIFIED_PROCESSOR
        self.unified_processor_prompt_path: str = settings.UNIFIED_PROCESSOR_PROMPT_PATH
        self.unified_processor_temperature: float = settings.UNIFIED_PROCESSOR_TEMPERATURE

        # Quality Gate thresholds
        self.quality_gate_threshold_good: float = settings.QUALITY_GATE_THRESHOLD_GOOD
        self.quality_gate_threshold_medium: float = settings.QUALITY_GATE_THRESHOLD_MEDIUM

        # Reply temperature
        self.reply_temperature: float = settings.REPLY_TEMPERATURE

    def __repr__(self) -> str:
        return (
            f"RAGConfig(embedding={self.embedding_model}, "
            f"chunk_size={self.chunk_size}, retrieval_k={self.retrieval_k}, "
            f"use_reranker={self.use_reranker})"
        )


@lru_cache(maxsize=1)
def load_rag_config(config_name: str = "default") -> RAGConfig:
    """
    Load RAG configuration from Pydantic Settings.

    Args:
        config_name: Ignored (kept for backward compatibility).
                    All settings now come from environment variables.

    Returns:
        RAGConfig object with settings from env vars
    """
    rag_config = RAGConfig()
    print(f"✓ RAG config loaded from env: {rag_config}")
    return rag_config


def get_default_config() -> RAGConfig:
    """Get default RAG configuration."""
    return load_rag_config("default")
