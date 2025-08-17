"""
Core AI processing components.

This package contains the channel-agnostic core logic for AI processing,
including routing, context retrieval, and reply generation. These components
are shared across all communication channels.
"""

from .chain import CoreChain, get_core_chain, process_message_with_core
from .router import supervisor_route
from .rag import retrieve_context
from .reply import generate_reply

__all__ = [
    "CoreChain", 
    "get_core_chain", 
    "process_message_with_core",
    "supervisor_route",
    "retrieve_context", 
    "generate_reply"
]