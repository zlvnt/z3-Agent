"""
Simplified Telegram memory management with LangChain integration.

This module provides basic conversation memory for Telegram channels using
LangChain's SQLChatMessageHistory with minimal configuration.
"""

from typing import Optional
from pathlib import Path

from langchain_community.chat_message_histories import SQLChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory

from app.config import settings


class TelegramMemory:
    """
    Simple Telegram memory manager using LangChain SQLChatMessageHistory.
    
    Features:
    - Basic LangChain SQLChatMessageHistory integration
    - Simple conversation storage and retrieval
    - Minimal configuration for lightweight usage
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize simple Telegram memory manager.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path or getattr(settings, 'TELEGRAM_DB_PATH', 'data/telegram_memory.db')
        
        # Ensure database directory exists
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        print(f"🧠 TelegramMemory initialized: {self.db_path}")
    
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
            
            print(f"💾 Saved interaction for session: {session_id}")
                
        except Exception as e:
            print(f"❌ Error saving interaction for {session_id}: {e}")
            # Don't raise - memory failures shouldn't break message processing


# Simple factory function
def create_telegram_memory(db_path: Optional[str] = None) -> TelegramMemory:
    """
    Create TelegramMemory instance with simple configuration.
    
    Args:
        db_path: Override database path
        
    Returns:
        TelegramMemory: Memory instance
    """
    return TelegramMemory(db_path=db_path)


# Global instance for easy access
_telegram_memory = None

def get_telegram_memory() -> TelegramMemory:
    """
    Get global TelegramMemory instance.
    
    Returns:
        TelegramMemory: Global memory instance
    """
    global _telegram_memory
    if _telegram_memory is None:
        _telegram_memory = create_telegram_memory()
    return _telegram_memory