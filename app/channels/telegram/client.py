"""
Simple Telegram API client for basic bot operations.

This module provides a lightweight TelegramClient class for interacting with 
the Telegram Bot API with minimal configuration and dependencies.
"""

import httpx
from typing import Optional

from app.config import settings


class TelegramClient:
    """
    Simple Telegram API client for basic bot operations.
    
    Features:
    - Basic async HTTP client for Telegram API
    - Simple error handling
    - Lightweight configuration
    """
    
    def __init__(self, token: Optional[str] = None):
        """
        Initialize simple Telegram API client.
        
        Args:
            token: Telegram bot token (gets from settings if None)
            
        Raises:
            ValueError: If no token is provided or found in settings
        """
        self.token = token or getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
        if not self.token:
            raise ValueError("TELEGRAM_BOT_TOKEN is required")
        
        self.base_url = f"https://api.telegram.org/bot{self.token}"
        
        print(f"🤖 TelegramClient initialized")
    
    async def send_message(
        self, 
        chat_id: int, 
        text: str,
        reply_to_message_id: Optional[int] = None
    ) -> bool:
        """
        Send text message to Telegram chat.
        
        Args:
            chat_id: Target chat/user ID
            text: Message text to send
            reply_to_message_id: Message ID to reply to (optional)
            
        Returns:
            bool: True if message sent successfully, False otherwise
        """
        try:
            if not text or not text.strip():
                return False
            
            # Telegram message length limit
            if len(text) > 4096:
                text = text[:4090] + "..."
            
            payload = {
                "chat_id": chat_id,
                "text": text
            }
            
            if reply_to_message_id:
                payload["reply_to_message_id"] = reply_to_message_id
            
            # Use simple httpx client for each request
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/sendMessage",
                    json=payload,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get("ok", False):
                        print(f"✅ Telegram message sent to chat {chat_id}")
                        return True
                
                print(f"❌ Telegram API error: {response.status_code}")
                return False
            
        except Exception as e:
            print(f"❌ Failed to send Telegram message: {e}")
            return False


# Simple global instance
_telegram_client = None

def get_telegram_client() -> TelegramClient:
    """Get global TelegramClient instance."""
    global _telegram_client
    if _telegram_client is None:
        _telegram_client = TelegramClient()
    return _telegram_client


# Helper function for backward compatibility
async def send_telegram_message(
    chat_id: int, 
    text: str, 
    reply_to_message_id: Optional[int] = None
) -> bool:
    """
    Send message to Telegram chat - helper function.
    
    Args:
        chat_id: Target chat/user ID
        text: Message text to send
        reply_to_message_id: Message ID to reply to (optional)
        
    Returns:
        bool: True if message sent successfully
    """
    try:
        client = get_telegram_client()
        return await client.send_message(
            chat_id=chat_id,
            text=text,
            reply_to_message_id=reply_to_message_id
        )
    except Exception as e:
        print(f"❌ Failed to send Telegram message: {e}")
        return False