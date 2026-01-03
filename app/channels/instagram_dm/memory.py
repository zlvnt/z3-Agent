"""
Instagram DM memory management with LangChain integration.

This module provides conversation memory for Instagram DM channels using
LangChain's SQLChatMessageHistory with minimal configuration.
"""

from typing import Optional
from pathlib import Path

from langchain_community.chat_message_histories import SQLChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory

from app.config import settings


class InstagramDMMemory:
    """
    Instagram DM memory manager using LangChain SQLChatMessageHistory.

    Features:
    - LangChain SQLChatMessageHistory integration
    - Conversation storage and retrieval
    - Separate database from Telegram (no cross-contamination)
    """

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize Instagram DM memory manager.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path or "data/instagram_dm_memory.db"

        # Ensure database directory exists
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        print(f"🧠 InstagramDMMemory initialized: {self.db_path}")

    def _get_session_history(self, session_id: str) -> BaseChatMessageHistory:
        """
        Get LangChain message history for a session.

        Args:
            session_id: Unique session identifier

        Returns:
            BaseChatMessageHistory: LangChain message history instance
        """
        return SQLChatMessageHistory(
            session_id=session_id,
            connection_string=f"sqlite:///{self.db_path}"
        )

    def get_history(self, session_id: str) -> str:
        """
        Get formatted conversation history for AI context.

        Args:
            session_id: Unique session identifier

        Returns:
            str: Formatted conversation history or empty string
        """
        try:
            history = self._get_session_history(session_id)
            messages = history.messages

            if not messages:
                return ""

            # Format last 10 messages for AI context
            formatted_history = []
            for msg in messages[-10:]:
                role = "Human" if msg.type == "human" else "Assistant"
                formatted_history.append(f"{role}: {msg.content}")

            return "\n".join(formatted_history)

        except Exception as e:
            print(f"⚠️ Failed to get conversation history for {session_id}: {e}")
            return ""

    def save_interaction(self, session_id: str, user_message: str, bot_reply: str):
        """
        Save user message and bot reply to conversation history.

        Args:
            session_id: Unique session identifier
            user_message: User's input message
            bot_reply: Bot's generated response
        """
        try:
            history = self._get_session_history(session_id)

            # Add user message and bot reply
            history.add_user_message(user_message)
            history.add_ai_message(bot_reply)

            print(f"💾 Saved Instagram DM interaction for session: {session_id}")

        except Exception as e:
            print(f"❌ Error saving interaction for {session_id}: {e}")
            # Don't raise - memory failures shouldn't break message processing

    async def get_memory_size(self, session_id: str) -> dict:
        """
        Get memory statistics for a session.

        Args:
            session_id: Unique session identifier

        Returns:
            dict: Memory statistics
        """
        try:
            history = self._get_session_history(session_id)
            messages = history.messages

            return {
                "session_id": session_id,
                "total_messages": len(messages),
                "user_messages": len([m for m in messages if m.type == "human"]),
                "bot_messages": len([m for m in messages if m.type == "ai"])
            }
        except Exception as e:
            return {"error": str(e)}


# Factory function
def create_instagram_dm_memory(db_path: Optional[str] = None) -> InstagramDMMemory:
    """
    Create InstagramDMMemory instance.

    Args:
        db_path: Override database path

    Returns:
        InstagramDMMemory: Memory instance
    """
    return InstagramDMMemory(db_path=db_path)


# Global instance
_instagram_dm_memory = None

def get_instagram_dm_memory() -> InstagramDMMemory:
    """
    Get global InstagramDMMemory instance.

    Returns:
        InstagramDMMemory: Global memory instance
    """
    global _instagram_dm_memory
    if _instagram_dm_memory is None:
        _instagram_dm_memory = create_instagram_dm_memory()
    return _instagram_dm_memory
