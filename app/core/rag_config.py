"""
RAG Configuration Loader for z3-Agent.

Loads RAG settings from YAML config files.
Supports multiple configs for different use cases (default, instagram, telegram, etc.)

Adapted from agentic-rag research domain_config.py
"""

from pathlib import Path
from typing import Dict, Any
from functools import lru_cache
import yaml


class RAGConfig:
    """RAG configuration loaded from YAML."""

    def __init__(self, config_dict: Dict[str, Any]):
        """Initialize from config dictionary."""
        # Embedding settings
        self.embedding_model: str = config_dict.get(
            "embedding_model",
            "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
        )

        # Chunking settings
        self.chunk_size: int = config_dict.get("chunk_size", 500)
        self.chunk_overlap: int = config_dict.get("chunk_overlap", 50)

        # Retrieval settings
        self.retrieval_k: int = config_dict.get("retrieval_k", 7)
        self.relevance_threshold: float = config_dict.get("relevance_threshold", 1.0)

        # Reranker settings
        self.use_reranker: bool = config_dict.get("use_reranker", True)
        self.reranker_model: str = config_dict.get("reranker_model", "BAAI/bge-reranker-base")
        self.reranker_top_k: int = config_dict.get("reranker_top_k", 3)
        self.reranker_use_fp16: bool = config_dict.get("reranker_use_fp16", True)

        # Adaptive fallback
        self.enable_adaptive_fallback: bool = config_dict.get("enable_adaptive_fallback", True)

        # Unified Processor
        self.use_unified_processor: bool = config_dict.get("use_unified_processor", True)
        self.unified_processor_prompt_path: str = config_dict.get(
            "unified_processor_prompt_path",
            "prompts/unified_processor_prompt.txt"
        )

        # Phase 1: Quality Gate thresholds (reranker score based)
        self.quality_gate_threshold_good: float = config_dict.get("quality_gate_threshold_good", 0.5)
        self.quality_gate_threshold_medium: float = config_dict.get("quality_gate_threshold_medium", 0.0)

    def __repr__(self) -> str:
        return (
            f"RAGConfig(embedding={self.embedding_model}, "
            f"chunk_size={self.chunk_size}, retrieval_k={self.retrieval_k}, "
            f"use_reranker={self.use_reranker})"
        )


@lru_cache(maxsize=4)
def load_rag_config(config_name: str = "default") -> RAGConfig:
    """
    Load RAG configuration from YAML file.

    Args:
        config_name: Name of config file (without .yaml extension)
                    e.g., "default", "instagram", "telegram"

    Returns:
        RAGConfig object with loaded settings

    Raises:
        FileNotFoundError: If config file doesn't exist
        yaml.YAMLError: If config file is invalid
    """
    # Try to find config file in multiple locations
    possible_paths = [
        Path("configs/rag") / f"{config_name}.yaml",
        Path("../configs/rag") / f"{config_name}.yaml",
        Path(__file__).parent.parent.parent / "configs" / "rag" / f"{config_name}.yaml",
    ]

    config_path = None
    for path in possible_paths:
        if path.exists():
            config_path = path
            break

    if config_path is None:
        raise FileNotFoundError(
            f"RAG config not found: {config_name}.yaml\n"
            f"Searched in: {[str(p) for p in possible_paths]}"
        )

    print(f"Loading RAG config: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        config_dict = yaml.safe_load(f)

    rag_config = RAGConfig(config_dict)
    print(f"✓ RAG config loaded: {rag_config}")

    return rag_config


def get_default_config() -> RAGConfig:
    """Get default RAG configuration."""
    return load_rag_config("default")
