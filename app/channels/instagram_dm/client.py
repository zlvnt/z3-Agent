"""
Instagram DM API client for sending direct messages.

This module provides a lightweight InstagramDMClient class for interacting with
the Instagram Graph API Messaging endpoint.
"""

import httpx
from typing import Optional

from app.config import settings


class InstagramDMClient:
    """
    Instagram DM API client for sending messages via Graph API.

    Features:
    - Async HTTP client for Instagram Messaging API
    - Simple error handling
    - Graph API v{version}/me/messages endpoint
    """

    def __init__(self, access_token: Optional[str] = None, api_version: Optional[str] = None):
        """
        Initialize Instagram DM API client.

        Args:
            access_token: Instagram access token (gets from settings if None)
            api_version: Graph API version (default from settings)

        Raises:
            ValueError: If no access token is provided or found in settings
        """
        self.access_token = access_token or settings.INSTAGRAM_ACCESS_TOKEN
        if not self.access_token:
            raise ValueError("INSTAGRAM_ACCESS_TOKEN is required")

        self.api_version = api_version or settings.GRAPH_API_VERSION
        self.base_url = f"{settings.INSTAGRAM_API_BASE_URL}/v{self.api_version}"

        print(f"📸 InstagramDMClient initialized (API v{self.api_version})")

    async def send_message(
        self,
        recipient_id: str,
        message_text: str
    ) -> bool:
        """
        Send direct message to Instagram user.

        Uses the Instagram Messaging API:
        POST /{api-version}/me/messages

        Args:
            recipient_id: Instagram user ID (IGSID)
            message_text: Message text to send

        Returns:
            bool: True if message sent successfully, False otherwise
        """
        try:
            if not message_text or not message_text.strip():
                return False

            # Instagram message length limit (1000 characters)
            if len(message_text) > 1000:
                message_text = message_text[:995] + "..."

            payload = {
                "recipient": {
                    "id": recipient_id
                },
                "message": {
                    "text": message_text
                }
            }

            params = {
                "access_token": self.access_token
            }

            # Use httpx client for request
            # Instagram Messaging API uses Facebook Page ID (connected to Instagram)
            page_id = settings.PAGE_ID

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/{page_id}/messages",
                    json=payload,
                    params=params,
                    timeout=30.0
                )

                if response.status_code == 200:
                    result = response.json()
                    # Instagram Messaging API returns message_id on success
                    if result.get("message_id"):
                        print(f"✅ Instagram DM sent to {recipient_id}")
                        return True

                print(f"❌ Instagram API error: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            print(f"❌ Failed to send Instagram DM: {e}")
            return False


# Global instance
_instagram_dm_client = None

def get_instagram_dm_client() -> InstagramDMClient:
    """Get global InstagramDMClient instance."""
    global _instagram_dm_client
    if _instagram_dm_client is None:
        _instagram_dm_client = InstagramDMClient()
    return _instagram_dm_client


# Helper function
async def send_instagram_dm(
    recipient_id: str,
    message_text: str
) -> bool:
    """
    Send Instagram DM - helper function.

    Args:
        recipient_id: Instagram user ID (IGSID)
        message_text: Message text to send

    Returns:
        bool: True if message sent successfully
    """
    try:
        client = get_instagram_dm_client()
        return await client.send_message(
            recipient_id=recipient_id,
            message_text=message_text
        )
    except Exception as e:
        print(f"❌ Failed to send Instagram DM: {e}")
        return False
