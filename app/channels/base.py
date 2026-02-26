"""
Base channel interface for z3-Agent.

All channel implementations (Telegram, Instagram, etc.) should inherit
from BaseChannel and implement its abstract methods.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseChannel(ABC):
    """
    Abstract base class for all channel implementations.

    Provides a standard interface for message processing across different
    messaging platforms.
    """

    @abstractmethod
    async def process_message(self, raw_data: Dict[str, Any]) -> str:
        """
        Process incoming message through the complete pipeline.

        Args:
            raw_data: Raw platform-specific message data

        Returns:
            str: Status message
        """
        pass

    @abstractmethod
    def get_session_id(self, message_data: Dict[str, Any]) -> str:
        """
        Generate unique session ID for conversation tracking.

        Args:
            message_data: Parsed message data

        Returns:
            str: Unique session identifier
        """
        pass

    @abstractmethod
    async def send_reply(self, reply: str, metadata: Dict[str, Any]) -> bool:
        """
        Send reply back to the platform.

        Args:
            reply: AI-generated response text
            metadata: Platform-specific metadata for delivery

        Returns:
            bool: True if sent successfully
        """
        pass

    @abstractmethod
    def extract_message_data(self, raw_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse platform-specific data into standardized format.

        Args:
            raw_input: Raw platform data

        Returns:
            Dict: Standardized message data
        """
        pass

    def should_process_message(self, message_data: Dict[str, Any]) -> bool:
        """
        Determine if message should be processed.
        Default: process all messages.
        """
        return True

    async def process_with_metrics(self, raw_data: Dict[str, Any]) -> str:
        """Process message with metrics recording."""
        import time
        from app.monitoring.enhanced_metrics import get_enhanced_metrics_instance

        start = time.time()
        try:
            result = await self.process_message(raw_data)
            duration = time.time() - start
            metrics = get_enhanced_metrics_instance()
            metrics.record_request(duration, success=True)
            return result
        except Exception as e:
            duration = time.time() - start
            metrics = get_enhanced_metrics_instance()
            metrics.record_request(duration, success=False)
            raise
