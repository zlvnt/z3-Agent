import httpx
from typing import Optional, Dict, Any

from app.config import settings


class TelegramAPI:
    def __init__(self, token: Optional[str] = None):
        self.token = token or getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
        if not self.token:
            raise ValueError("TELEGRAM_BOT_TOKEN is required")
        
        self.base_url = f"https://api.telegram.org/bot{self.token}"
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def send_message(
        self, 
        chat_id: int, 
        text: str,
        reply_to_message_id: Optional[int] = None,
        parse_mode: str = "HTML"
    ) -> Dict[str, Any]:
        """
        Send text message to Telegram chat.
        """
        try:
            payload = {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": parse_mode
            }
            
            if reply_to_message_id:
                payload["reply_to_message_id"] = reply_to_message_id
            
            response = await self.client.post(
                f"{self.base_url}/sendMessage",
                json=payload
            )
            response.raise_for_status()
            
            result = response.json()
            print(f"✅ Telegram message sent to chat {chat_id}")
            return result
            
        except httpx.HTTPError as e:
            print(f"❌ Failed to send Telegram message: {e}")
            raise
        except Exception as e:
            print(f"❌ Unexpected error sending Telegram message: {e}")
            raise
    
    async def set_webhook(self, webhook_url: str, secret_token: Optional[str] = None) -> Dict[str, Any]:
        """
        Set webhook URL for receiving updates.
        """
        try:
            payload = {
                "url": webhook_url,
                "max_connections": 40,
                "allowed_updates": ["message", "callback_query"]
            }
            
            if secret_token:
                payload["secret_token"] = secret_token
            
            response = await self.client.post(
                f"{self.base_url}/setWebhook",
                json=payload
            )
            response.raise_for_status()
            
            result = response.json()
            print(f"✅ Telegram webhook set to: {webhook_url}")
            return result
            
        except Exception as e:
            print(f"❌ Failed to set Telegram webhook: {e}")
            raise
    
    
    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()


# Global instance (lazy loading)
_telegram_api = None

async def get_telegram_api() -> TelegramAPI:
    """Get global TelegramAPI instance (singleton pattern)."""
    global _telegram_api
    if _telegram_api is None:
        _telegram_api = TelegramAPI()
    return _telegram_api


# Helper functions matching Instagram API pattern
async def send_telegram_message(chat_id: int, text: str, reply_to_message_id: Optional[int] = None) -> bool:
    """
    Send message to Telegram chat - helper function matching Instagram pattern.
    """
    try:
        api = await get_telegram_api()
        await api.send_message(chat_id, text, reply_to_message_id)
        return True
    except Exception as e:
        print(f"❌ Failed to send Telegram message: {e}")
        return False


