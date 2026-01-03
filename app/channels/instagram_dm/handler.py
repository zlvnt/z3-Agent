"""
Instagram DM channel handler implementation.

This module implements the InstagramDMChannel class that provides Instagram
Direct Message processing, conversation management, and API integration
following the BaseChannel interface.

Similar to TelegramChannel but adapted for Instagram Messaging API.
"""

from typing import Dict, Any

from app.channels.base import BaseChannel
from app.config import settings


class InstagramDMChannel(BaseChannel):
    """
    Instagram DM channel implementation with memory management and API integration.

    This class handles Instagram Direct Message processing including:
    - Private DM conversations with session management
    - Memory management with SQLite storage
    - Integration with core AI processing system
    - Instagram Graph API for sending messages
    """

    def __init__(self):
        """Initialize Instagram DM channel with dependencies."""
        from .memory import get_instagram_dm_memory
        from .client import get_instagram_dm_client

        self.memory = get_instagram_dm_memory()
        self.client = get_instagram_dm_client()
        self.account_id = settings.INSTAGRAM_ACCOUNT_ID

        print(f"📸 InstagramDMChannel initialized")

    async def process_message(self, raw_data: Dict[str, Any]) -> str:
        """
        Process incoming Instagram DM through the complete pipeline.

        Pipeline:
        1. Extract and validate message data
        2. Check if message should be processed (skip own messages, empty, etc)
        3. Generate session ID for conversation tracking
        4. Get conversation history for context
        5. Process through core AI system
        6. Send reply back to Instagram
        7. Save interaction to memory

        Args:
            raw_data: Raw Instagram webhook messaging object

        Returns:
            str: Status message describing the processing result
        """
        try:
            # Step 1: Extract message data
            message_data = self.extract_message_data(raw_data)

            # Step 2: Validate and filter message
            if not message_data or not isinstance(message_data, dict):
                return "Invalid message data format"

            if not self.should_process_message(message_data):
                return "Message skipped (own message, empty, or filtered)"

            # Step 3: Generate session ID
            session_id = self.get_session_id(message_data)

            # Step 4: Get conversation history
            history = self.get_conversation_history(session_id)

            print(f"📨 Processing Instagram DM: {message_data['message_text'][:50]}... from {message_data.get('sender_id', 'unknown')}")

            # Step 5: Process through core AI system
            reply = await self._process_with_core_system(
                text=message_data['message_text'],
                history=history,
                session_id=session_id
            )

            # Step 6: Send reply back to Instagram
            if reply:
                send_metadata = {
                    'recipient_id': message_data['sender_id'],
                    'message_id': message_data.get('message_id'),
                }

                success = await self.send_reply(reply, send_metadata)

                if success:
                    # Step 7: Save interaction to memory
                    if self.memory:
                        self.memory.save_interaction(
                            session_id=session_id,
                            user_message=message_data['message_text'],
                            bot_reply=reply
                        )

                    print(f"✅ Instagram DM reply sent to {message_data.get('sender_id', 'unknown')}")
                    return f"Message processed successfully for session: {session_id}"
                else:
                    return "Failed to send reply to Instagram"
            else:
                return "No reply generated"

        except Exception as e:
            print(f"❌ Error in process_message: {e}")
            return f"Error: {str(e)}"

    def get_session_id(self, message_data: Dict[str, Any]) -> str:
        """
        Generate unique session ID for Instagram DM conversations.

        Session ID format: 'ig_dm_{sender_id}'

        Args:
            message_data: Parsed message data

        Returns:
            str: Unique session identifier
        """
        sender_id = message_data.get('sender_id', 'unknown')
        return f"ig_dm_{sender_id}"

    async def send_reply(self, reply: str, metadata: Dict[str, Any]) -> bool:
        """
        Send reply message to Instagram using the Graph API.

        Args:
            reply: The AI-generated response text
            metadata: Contains recipient_id, etc.

        Returns:
            bool: True if sent successfully, False otherwise
        """
        if not self.client:
            print("❌ No Instagram client available for sending message")
            return False

        try:
            return await self.client.send_message(
                recipient_id=metadata['recipient_id'],
                message_text=reply
            )
        except Exception as e:
            print(f"❌ Failed to send Instagram DM: {e}")
            return False

    def get_conversation_history(self, session_id: str) -> str:
        """Get conversation history for AI context."""
        if not self.memory:
            return ""

        try:
            return self.memory.get_history(session_id)
        except Exception as e:
            print(f"⚠️ Failed to get conversation history: {e}")
            return ""

    def extract_message_data(self, raw_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse Instagram Messaging webhook into standardized format.

        Instagram Messaging webhook structure:
        {
            "sender": {"id": "USER_IGSID"},
            "recipient": {"id": "PAGE_IGSID"},
            "timestamp": 1234567890,
            "message": {
                "mid": "MESSAGE_ID",
                "text": "Hello"
            }
        }

        Args:
            raw_input: Raw Instagram messaging webhook

        Returns:
            Dict[str, Any]: Standardized message data

        Raises:
            ValueError: If required fields are missing
        """
        try:
            # Extract sender info
            sender = raw_input.get("sender", {})
            sender_id = sender.get("id")
            if not sender_id:
                raise ValueError("Missing sender ID in Instagram message")

            # Extract recipient info
            recipient = raw_input.get("recipient", {})
            recipient_id = recipient.get("id")

            # Extract message content
            message = raw_input.get("message", {})
            message_text = message.get("text", "").strip()
            message_id = message.get("mid", "")

            if not message_text:
                raise ValueError("Empty message text")

            # Get timestamp
            timestamp = raw_input.get("timestamp", 0)

            return {
                "sender_id": sender_id,
                "recipient_id": recipient_id,
                "message_text": message_text,
                "message_id": message_id,
                "timestamp": timestamp,
                # Check if this is an echo (message sent by the page itself)
                "is_echo": message.get("is_echo", False),
            }

        except Exception as e:
            raise ValueError(f"Failed to extract Instagram DM data: {e}")

    def should_process_message(self, message_data: Dict[str, Any]) -> bool:
        """
        Determine if this Instagram DM should be processed.

        Instagram-specific filtering:
        - Skip echo messages (sent by page itself)
        - Skip empty messages
        - Skip messages from the account itself

        Args:
            message_data: Standardized message data

        Returns:
            bool: True if message should be processed
        """
        # Basic validation
        if not message_data.get('message_text', '').strip():
            return False

        # Skip echo messages (messages sent by the page)
        if message_data.get('is_echo', False):
            print(f"🔄 Skipping echo message (sent by page)")
            return False

        # Skip if sender is the account itself
        sender_id = message_data.get('sender_id', '')
        if sender_id == self.account_id:
            print(f"🔄 Skipping message from account itself")
            return False

        return True

    async def _process_with_core_system(self, text: str, history: str, session_id: str) -> str:
        """
        Process message through core AI system.

        Uses the CoreChain for channel-agnostic AI processing.

        Args:
            text: User message text
            history: Formatted conversation history
            session_id: Unique session identifier

        Returns:
            str: AI-generated reply
        """
        try:
            from app.core.chain import process_message_with_core

            # Process through core chain
            reply = await process_message_with_core(
                text=text,
                history=history
            )

            return reply

        except Exception as e:
            print(f"❌ Error in core system processing: {e}")
            return "Sorry, I encountered an issue processing your message. Please try again."

    async def get_memory_stats(self, session_id: str) -> Dict[str, Any]:
        """
        Get memory statistics for this conversation.

        Args:
            session_id: Unique session identifier

        Returns:
            Dict containing memory statistics
        """
        if not self.memory:
            return {"error": "No memory instance available"}

        try:
            return await self.memory.get_memory_size(session_id)
        except Exception as e:
            return {"error": f"Failed to get memory stats: {e}"}


# Global instance
_instagram_dm_channel = None


def get_instagram_dm_channel() -> InstagramDMChannel:
    """Get global InstagramDMChannel instance."""
    global _instagram_dm_channel
    if _instagram_dm_channel is None:
        _instagram_dm_channel = InstagramDMChannel()
    return _instagram_dm_channel
