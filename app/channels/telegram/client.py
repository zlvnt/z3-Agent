"""
Telegram Bot API client.

Simple async HTTP client for sending messages via Telegram Bot API.
"""

import httpx
from typing import Optional

from app.config import settings


class TelegramClient:
    """Async Telegram Bot API client."""

    def __init__(self, token: Optional[str] = None):
        self.token = token or settings.TELEGRAM_BOT_TOKEN
        self.base_url = f"https://api.telegram.org/bot{self.token}"

    async def send_message(
        self,
        chat_id: int,
        text: str,
        reply_to_message_id: Optional[int] = None,
    ) -> bool:
        """
        Send a text message via Telegram Bot API.

        Args:
            chat_id: Target chat ID
            text: Message text (max 4096 chars)
            reply_to_message_id: Optional message ID to reply to

        Returns:
            bool: True if sent successfully
        """
        # Telegram message limit
        if len(text) > 4096:
            text = text[:4093] + "..."

        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
        }
        if reply_to_message_id:
            payload["reply_parameters"] = {"message_id": reply_to_message_id}

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/sendMessage",
                    json=payload,
                )
                if response.status_code == 200:
                    return True
                else:
                    print(f"Telegram API error: {response.status_code} - {response.text}")
                    return False
        except Exception as e:
            print(f"Failed to send Telegram message: {e}")
            return False

    async def get_webhook_info(self) -> dict:
        """Get current webhook configuration."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/getWebhookInfo")
                if response.status_code == 200:
                    return response.json().get("result", {})
                return {"error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}

    async def delete_webhook(self) -> bool:
        """Delete the current webhook."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(f"{self.base_url}/deleteWebhook")
                return response.status_code == 200
        except Exception as e:
            print(f"Failed to delete webhook: {e}")
            return False

    async def get_me(self) -> dict:
        """Get bot info."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/getMe")
                if response.status_code == 200:
                    return response.json().get("result", {})
                return {"error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}


# Global instance
_telegram_client = None


def get_telegram_client() -> TelegramClient:
    """Get global TelegramClient instance."""
    global _telegram_client
    if _telegram_client is None:
        _telegram_client = TelegramClient()
    return _telegram_client


async def send_telegram_message(
    chat_id: int, text: str, reply_to_message_id: Optional[int] = None
) -> bool:
    """Helper function to send a Telegram message."""
    client = get_telegram_client()
    return await client.send_message(chat_id, text, reply_to_message_id)
