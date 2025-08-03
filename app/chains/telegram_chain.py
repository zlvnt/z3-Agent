from typing import Dict, Any, Optional
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import SQLChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from pathlib import Path
import asyncio

from app.chains.conditional_chain import InstagramConditionalChain
from app.config import settings


class TelegramChainWrapper:
    
    def __init__(self, memory_db_path: Optional[str] = None):
        """
        Initialize Telegram chain with LangChain memory.
        
        Args:
            memory_db_path: Path to SQLite database for conversation storage
        """
        self.memory_db_path = memory_db_path or "data/telegram_memory.db"
        self.base_chain = InstagramConditionalChain(memory_window=5)
        
        # Create chain with LangChain memory
        self.chain_with_memory = RunnableWithMessageHistory(
            runnable=self.base_chain,
            get_session_history=self._get_session_history,
            input_messages_key="comment",
            history_messages_key="chat_history"
        )
    
    def _get_session_history(self, **kwargs) -> BaseChatMessageHistory:
        chat_id = kwargs.get("chat_id", "unknown")
        username = kwargs.get("username", "unknown")
        session_id = f"tg_{chat_id}_{username}"
        
        return SQLChatMessageHistory(
            session_id=session_id,
            connection_string=f"sqlite:///{self.memory_db_path}",
            table_name="telegram_conversations"
        )
    
    async def process_message(
        self, 
        chat_id: str, 
        username: str, 
        message: str,
        enable_monitoring: bool = True
    ) -> str:
        try:
            # Prepare input for chain
            chain_input = {
                "comment": message,
                "post_id": f"tg_chat_{chat_id}",
                "comment_id": f"tg_msg_{asyncio.get_event_loop().time()}",
                "username": username,
                "channel": "telegram"  # Channel identifier
            }
            
            # Configure session for LangChain memory
            config = {
                "configurable": {
                    "chat_id": str(chat_id),
                    "username": username
                }
            }
            
            print(f"🧠 Processing Telegram message with LangChain memory: {message[:50]}...")
            
            # Process through chain with automatic memory injection
            result = await asyncio.to_thread(
                self.chain_with_memory.invoke,
                chain_input,
                config
            )
            
            # Extract reply from result
            if isinstance(result, dict):
                reply = result.get("reply", "")
            else:
                reply = str(result)
            
            print(f"✅ Telegram reply generated: {reply[:50]}...")
            return reply
            
        except Exception as e:
            print(f"❌ Error in Telegram chain processing: {e}")
            return "Maaf, terjadi kesalahan dalam memproses pesan kamu. Coba lagi ya!"
    
    def get_conversation_stats(self, chat_id: str, username: str) -> Dict[str, Any]:
        session_id = f"tg_{chat_id}_{username}"
        
        try:
            history = self._get_session_history(chat_id=chat_id, username=username)
            messages = history.messages
            
            return {
                "session_id": session_id,
                "message_count": len(messages),
                "memory_type": "LangChain SQLChatMessageHistory",
                "database_path": self.memory_db_path,
                "last_messages": [
                    {"type": msg.type, "content": msg.content[:100]}
                    for msg in messages[-3:]  # Last 3 messages
                ]
            }
        except Exception as e:
            return {
                "session_id": session_id,
                "error": str(e),
                "message_count": 0
            }


# Global instance for singleton pattern
_telegram_chain = None

def get_telegram_chain() -> TelegramChainWrapper:
    """Get singleton TelegramChainWrapper instance."""
    global _telegram_chain
    if _telegram_chain is None:
        # Ensure data directory exists
        Path("data").mkdir(exist_ok=True)
        _telegram_chain = TelegramChainWrapper()
    return _telegram_chain


# Async wrapper function for webhook processing
async def process_telegram_with_memory(
    chat_id: str,
    username: str, 
    message: str,
    enable_monitoring: bool = True
) -> str:
    chain = get_telegram_chain()
    return await chain.process_message(
        chat_id=chat_id,
        username=username,
        message=message,
        enable_monitoring=enable_monitoring
    )