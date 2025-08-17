"""
Telegram channel implementation for the multi-channel AI agent.

This package provides Telegram-specific functionality including:
- Message processing and conversation management
- Memory management with SQLite and pruning
- API client for sending messages
- Webhook handling for incoming updates
"""

from .handler import TelegramChannel

__all__ = ["TelegramChannel"]