"""
Simple base interface for communication channels.

This module defines a minimal interface for channel implementations
to ensure basic consistency across different communication platforms.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseChannel(ABC):
    """
    Simple base interface for communication channels.
    
    Defines the minimal interface that all channels (Instagram, Telegram) 
    must implement for basic message processing.
    """
    
    @abstractmethod
    async def process_message(self, raw_data: Dict[str, Any]) -> str:
        pass
    
    @abstractmethod
    def get_session_id(self, message_data: Dict[str, Any]) -> str:
        pass
    
    @abstractmethod
    async def send_reply(self, reply: str, metadata: Dict[str, Any]) -> bool:
        pass
    
    @abstractmethod
    def extract_message_data(self, raw_input: Dict[str, Any]) -> Dict[str, Any]:
        pass