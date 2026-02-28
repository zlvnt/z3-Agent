"""
Telegram channel handler implementation.

This module implements the TelegramChannel class that provides Telegram-specific
message processing, conversation management, and API integration following the
BaseChannel interface.
"""

import asyncio
from typing import Dict, Any

from app.channels.base import BaseChannel
from app.config import settings


class TelegramChannel(BaseChannel):
    """
    Telegram channel implementation with memory management and API integration.
    
    This class handles Telegram-specific message processing including:
    - Private and group chat support with proper session management
    - Memory management with pruning to prevent unlimited growth
    - Integration with core AI processing system
    - Graceful error handling and fallbacks
    """
    
    def __init__(self):
        """Initialize Telegram channel with direct dependencies."""
        from .memory import get_telegram_memory
        from .client import get_telegram_client
        
        self.memory = get_telegram_memory()
        self.client = get_telegram_client()
        self.bot_username = getattr(settings, 'TELEGRAM_BOT_USERNAME', 'z3_agent_bot')
        
        print(f"🤖 TelegramChannel initialized")
    
    async def process_message(self, raw_data: Dict[str, Any]) -> str:
        """
        Process incoming Telegram message through the complete pipeline.
        
        Pipeline:
        1. Extract and validate message data
        2. Check if message should be processed (skip bots, empty, etc)
        3. Generate session ID for conversation tracking
        4. Get conversation history for context
        5. Process through core AI system
        6. Send reply back to Telegram
        7. Save interaction to memory
        
        Args:
            raw_data: Raw Telegram webhook update object
            
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
                return "Message skipped (bot, empty, or filtered)"
            
            # Step 3: Generate session ID
            session_id = self.get_session_id(message_data)
            
            # Step 4: Get conversation history
            history = self.get_conversation_history(session_id)
            
            print(f"📨 Processing Telegram message: {message_data['message_text'][:50]}... from @{message_data.get('username', 'unknown')}")
            
            # Step 5: Process through core AI system
            reply = await self._process_with_core_system(
                text=message_data['message_text'],
                history=history,
                session_id=session_id,
                message_data=message_data
            )
            
            # Step 6: Send reply back to Telegram
            if reply:
                send_metadata = {
                    'chat_id': message_data['chat_id'],
                    'reply_to_message_id': message_data['message_id'],
                    'user_id': message_data['user_id'],
                    'username': message_data.get('username', 'unknown')
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
                    
                    print(f"✅ Telegram reply sent to @{message_data.get('username', 'unknown')}")
                    return f"Message processed successfully for session: {session_id}"
                else:
                    return "Failed to send reply to Telegram"
            else:
                return "No reply generated"
                
        except Exception as e:
            print(f"❌ Error in process_message: {e}")
            return f"Error: {str(e)}"
    
    def get_session_id(self, message_data: Dict[str, Any]) -> str:
        """
        Generate unique session ID for Telegram conversations.
        
        Session ID formats (TESTING MODE - using username):
        - Private chats: 'tg_private_{username}'
        - Group chats: 'tg_group_{chat_id}_{username}'
        
        NOTE: This is temporary for testing multiple sessions.
        Production should use user_id for reliability.
        
        Args:
            message_data: Parsed message data
            
        Returns:
            str: Unique session identifier
        """
        username = message_data.get('username', 'unknown')
        chat_id = message_data['chat_id']
        is_group = message_data.get('is_group', False)
        
        # Fallback to user_id if username is empty or 'unknown'
        if not username or username == 'unknown':
            user_id = message_data['user_id']
            if is_group:
                return f"tg_group_{chat_id}_{user_id}"
            else:
                return f"tg_private_{user_id}"
        
        # Use username for testing
        if is_group:
            return f"tg_group_{chat_id}_{username}"
        else:
            return f"tg_private_{username}"
    
    async def send_reply(self, reply: str, metadata: Dict[str, Any]) -> bool:
        """
        Send reply message to Telegram using the API client.
        
        Args:
            reply: The AI-generated response text
            metadata: Contains chat_id, reply_to_message_id, etc.
            
        Returns:
            bool: True if sent successfully, False otherwise
        """
        if not self.client:
            print("❌ No Telegram client available for sending message")
            return False
        
        try:
            return await self.client.send_message(
                chat_id=metadata['chat_id'],
                text=reply,
                reply_to_message_id=metadata.get('reply_to_message_id')
            )
        except Exception as e:
            print(f"❌ Failed to send Telegram message: {e}")
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
        Parse Telegram webhook update into standardized format.
        
        Telegram webhook structure:
        {
            "update_id": 123,
            "message": {
                "message_id": 456,
                "from": {"id": 789, "username": "user", "first_name": "Name"},
                "chat": {"id": 789, "type": "private"},
                "text": "Hello",
                "date": 1234567890
            }
        }
        
        Args:
            raw_input: Raw Telegram webhook update
            
        Returns:
            Dict[str, Any]: Standardized message data
            
        Raises:
            ValueError: If required fields are missing
        """
        try:
            message = raw_input.get("message", {})
            if not message:
                raise ValueError("No 'message' field in Telegram update")
            
            # Extract user information
            user = message.get("from", {})
            user_id = user.get("id")
            if not user_id:
                raise ValueError("Missing user ID in Telegram message")
            
            # Extract chat information
            chat = message.get("chat", {})
            chat_id = chat.get("id")
            if not chat_id:
                raise ValueError("Missing chat ID in Telegram message")
            
            # Determine if this is a group chat
            chat_type = chat.get("type", "private")
            is_group = chat_type in ["group", "supergroup", "channel"]
            
            # Extract message content
            message_text = message.get("text", "").strip()
            if not message_text:
                raise ValueError("Empty message text")
            
            message_id = message.get("message_id")
            if not message_id:
                raise ValueError("Missing message ID")
            
            # Extract username with fallback
            username = user.get("username")
            if not username:
                # Fallback to first_name + last_name or just first_name
                first_name = user.get("first_name", "")
                last_name = user.get("last_name", "")
                username = f"{first_name} {last_name}".strip() or "unknown"
            
            # Get timestamp
            timestamp = message.get("date", 0)
            
            return {
                "user_id": str(user_id),
                "username": username,
                "message_text": message_text,
                "chat_id": chat_id,  # Keep as integer for Telegram API
                "message_id": message_id,  # Keep as integer for Telegram API
                "timestamp": timestamp,
                "is_group": is_group,
                "chat_type": chat_type,
                "update_id": raw_input.get("update_id"),
                # Additional Telegram-specific fields
                "first_name": user.get("first_name"),
                "last_name": user.get("last_name"),
                "language_code": user.get("language_code")
            }
            
        except Exception as e:
            raise ValueError(f"Failed to extract Telegram message data: {e}")
    
    def should_process_message(self, message_data: Dict[str, Any]) -> bool:
        """
        Determine if this Telegram message should be processed.
        
        Telegram-specific filtering:
        - Skip messages from the bot itself (prevent loops)
        - Skip empty messages
        - Skip system messages (joins, leaves, etc.)
        
        Args:
            message_data: Standardized message data
            
        Returns:
            bool: True if message should be processed
        """
        # Basic validation
        if not message_data.get('message_text', '').strip():
            return False
        
        # Skip messages from the bot itself
        username = message_data.get('username', '')
        if username == self.bot_username:
            print(f"🔄 Skipping message from bot itself: {username}")
            return False
        
        return True
    
    async def _process_with_core_system(
        self, text: str, history: str, session_id: str, message_data: Dict[str, Any] = None
    ) -> str:
        """
        Process message through core AI system.

        Uses CoreChain for AI processing and handles HITL escalation
        by notifying the CS group when escalation is triggered.

        Args:
            text: User message text
            history: Formatted conversation history
            session_id: Unique session identifier
            message_data: Telegram message data (user_id, username, chat_id, etc.)

        Returns:
            str: AI-generated reply
        """
        try:
            from app.core.chain import process_message_with_core_full

            result = await process_message_with_core_full(
                text=text,
                history=history
            )

            reply = result.get("reply", "Mohon maaf, terjadi kendala. Silakan coba lagi.")

            # HITL: notify CS group + create ticket on escalation (fire-and-forget)
            if result.get("escalated", False) and message_data:
                asyncio.create_task(
                    self._notify_escalation(result, session_id, history, message_data)
                )
                asyncio.create_task(
                    self._create_escalation_ticket(result, session_id, history, message_data)
                )

            return reply

        except Exception as e:
            print(f"❌ Error in core system processing: {e}")
            return "Sorry, I encountered an issue processing your message. Please try again."

    async def _notify_escalation(
        self,
        escalation_result: Dict[str, Any],
        session_id: str,
        history: str,
        message_data: Dict[str, Any]
    ) -> None:
        """
        Fire-and-forget CS group notification on escalation.
        Failures are logged but never propagated.
        """
        try:
            from app.channels.telegram.escalation import notify_cs_group

            user_info = {
                'user_id': message_data.get('user_id', 'unknown'),
                'username': message_data.get('username', 'unknown'),
                'chat_id': message_data.get('chat_id', 'unknown'),
                'message_id': message_data.get('message_id'),
                'session_id': session_id,
            }

            await notify_cs_group(
                user_info=user_info,
                escalation_result=escalation_result,
                history_snippet=history
            )
        except Exception as e:
            print(f"WARNING: Escalation notification failed (non-blocking): {e}")
    
    async def _create_escalation_ticket(
        self,
        escalation_result: Dict[str, Any],
        session_id: str,
        history: str,
        message_data: Dict[str, Any]
    ) -> None:
        """Fire-and-forget ticket creation on escalation."""
        try:
            from app.services.ticket_service import get_ticket_service
            service = get_ticket_service()
            ticket_id = service.create_ticket(
                channel="telegram",
                session_id=session_id,
                user_id=str(message_data.get('user_id', '')),
                username=message_data.get('username'),
                chat_id=str(message_data.get('chat_id', '')),
                escalation_stage=escalation_result.get('escalation_stage', 'unknown'),
                escalation_reason=escalation_result.get('escalation_reason', 'Unknown'),
                original_query=escalation_result.get('original_query', ''),
                history_snippet=history[:500] if history else None,
                quality_score=escalation_result.get('quality_score'),
            )
            if ticket_id:
                print(f"🎫 Ticket created: {ticket_id} for @{message_data.get('username', 'unknown')}")
        except Exception as e:
            print(f"WARNING: Ticket creation failed (non-blocking): {e}")

    async def get_memory_stats(self, session_id: str) -> Dict[str, Any]:
        """
        Get memory statistics for this conversation.
        
        This is useful for monitoring and debugging memory usage.
        
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
_telegram_channel = None

def get_telegram_channel() -> TelegramChannel:
    """Get global TelegramChannel instance."""
    global _telegram_channel
    if _telegram_channel is None:
        _telegram_channel = TelegramChannel()
    return _telegram_channel