"""
LangChain conditional chain architecture untuk Instagram AI Agent.

Provides:
- Structured data models untuk type-safe communication
- Conditional chain implementation
- Memory integration strategy
- FastAPI integration layer
"""

from .models import (
    RouteDecision,
    ContextSource,
    RouterOutput,
    ContextChunk,
    ContextOutput,
    ChainInput,
    ChainOutput,
    ChainError,
    MemoryState,
    ChainInputType,
    ChainOutputType,
    RouterOutputType,
    ContextOutputType,
)

__all__ = [
    "RouteDecision",
    "ContextSource", 
    "RouterOutput",
    "ContextChunk",
    "ContextOutput",
    "ChainInput",
    "ChainOutput",
    "ChainError",
    "MemoryState",
    "ChainInputType",
    "ChainOutputType",
    "RouterOutputType",
    "ContextOutputType",
]