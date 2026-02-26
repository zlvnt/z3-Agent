"""
History management service.

Provides unified access to conversation history across channels.
"""

from typing import Optional


def format_history(messages: list, last_n: int = 10) -> str:
    """
    Format a list of messages into a string for AI context.

    Args:
        messages: List of message objects with .type and .content
        last_n: Number of recent messages to include

    Returns:
        Formatted history string
    """
    if not messages:
        return ""

    formatted = []
    for msg in messages[-last_n:]:
        role = "User" if msg.type == "human" else "Bot"
        formatted.append(f"{role}: {msg.content}")

    return "\n".join(formatted)


def truncate_history(history: str, max_chars: int = 2000) -> str:
    """Truncate history to fit within token limits."""
    if len(history) <= max_chars:
        return history
    return history[-max_chars:]
