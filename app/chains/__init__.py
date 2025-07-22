"""
Simple LangChain conditional chain untuk Instagram AI Agent.

Minimal approach - wrap existing functions dengan proper chain architecture.
"""

from .conditional_chain import (
    InstagramConditionalChain,
    create_instagram_chain, 
    process_with_chain
)

__all__ = [
    "InstagramConditionalChain",
    "create_instagram_chain",
    "process_with_chain"
]