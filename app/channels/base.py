"""
Simple base interface for communication channels.

This module defines a minimal interface for channel implementations
to ensure basic consistency across different communication platforms.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
import time


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
    
    def record_metrics(self, duration: float, success: bool = True, username: str = None, error_category: str = None):
        """Record metrics for this channel request"""
        try:
            from app.monitoring.enhanced_metrics import get_enhanced_metrics_instance
            metrics = get_enhanced_metrics_instance()
            channel_name = self.__class__.__name__.lower().replace('channel', '')
            metrics.record_channel_request(channel_name, duration, success, username, error_category)
        except Exception as e:
            print(f"WARNING: Metrics recording failed: {e}")
    
    async def process_with_metrics(self, raw_data: Dict[str, Any]) -> str:
        """Process message with automatic metrics recording"""
        start_time = time.time()
        success = True
        error_category = None
        username = None
        
        try:
            # Extract username for tracking
            message_data = self.extract_message_data(raw_data)
            username = message_data.get('username') or message_data.get('user_id')
            
            # Process the message
            reply = await self.process_message(raw_data)
            return reply
            
        except Exception as e:
            success = False
            error_category = type(e).__name__.lower()
            raise
        finally:
            # Record metrics regardless of success/failure
            duration = time.time() - start_time
            self.record_metrics(duration, success, username, error_category)