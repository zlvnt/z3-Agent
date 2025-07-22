"""
Hybrid Memory Integration Strategy.

Combines:
- LangChain ConversationBufferWindowMemory (runtime cache)
- Existing JSON persistence (long-term storage)
- Per-user memory management
"""

from __future__ import annotations
from typing import Dict, Optional, Any
import json
from datetime import datetime, timedelta

from langchain.memory import ConversationBufferWindowMemory
from langchain.schema import BaseMessage, HumanMessage, AIMessage

from app.chains.models import MemoryState
from app.services.conversation import add as save_conv, get_comment_history
from app.services.logger import logger


class MemoryManager:
    """
    Hybrid memory management untuk Instagram AI Agent.
    
    Strategy:
    - LangChain memory untuk runtime efficiency
    - JSON persistence untuk durability  
    - Per-user isolation
    - Automatic cleanup
    """
    
    def __init__(self, window_size: int = 5, cleanup_hours: int = 24):
        self.window_size = window_size
        self.cleanup_hours = cleanup_hours
        
        # Per-user LangChain memories
        self._user_memories: Dict[str, ConversationBufferWindowMemory] = {}
        
        # Per-user state tracking
        self._user_states: Dict[str, MemoryState] = {}
        
        print(f"INFO: MemoryManager initialized - window: {window_size}, cleanup: {cleanup_hours}h")
    
    def get_user_memory(self, user_id: str) -> ConversationBufferWindowMemory:
        """
        Get atau create LangChain memory untuk user.
        Loads from JSON persistence if first time.
        """
        if user_id not in self._user_memories:
            # Create new LangChain memory
            memory = ConversationBufferWindowMemory(
                k=self.window_size,
                return_messages=True,
                memory_key="chat_history"
            )
            
            # Load existing conversation history from JSON
            self._initialize_memory_from_json(user_id, memory)
            
            self._user_memories[user_id] = memory
            
            print(f"INFO: Created new memory for user: {user_id}")
        
        return self._user_memories[user_id]
    
    def _initialize_memory_from_json(
        self, 
        user_id: str, 
        memory: ConversationBufferWindowMemory
    ) -> None:
        """Initialize LangChain memory dari existing JSON data"""
        try:
            # Extract post_id from user_id (format: username_postid)
            if "_" in user_id:
                username, post_id = user_id.rsplit("_", 1)
                
                # Get recent history from JSON persistence
                # Note: get_comment_history expects post_id and comment_id
                # For memory initialization, we'll get general history
                from app.services.conversation import history
                recent_history = history(post_id=post_id, limit=self.window_size * 2)
                
                # Convert to LangChain messages
                for exchange in recent_history[-self.window_size:]:
                    if "comment" in exchange and "reply" in exchange:
                        memory.chat_memory.add_user_message(exchange["comment"])
                        memory.chat_memory.add_ai_message(exchange["reply"])
                
                print(f"INFO: Loaded {len(recent_history)} historical exchanges untuk user: {user_id}")
        
        except Exception as e:
            print(f"WARNING: Failed to load history untuk user {user_id}: {e}")
            # Continue dengan empty memory
    
    def add_exchange(
        self,
        user_id: str,
        post_id: str,
        comment_id: str,
        user_message: str,
        ai_message: str,
        username: str
    ) -> None:
        """
        Add conversation exchange to both memory systems.
        """
        # Update LangChain memory
        memory = self.get_user_memory(user_id)
        memory.chat_memory.add_user_message(user_message)
        memory.chat_memory.add_ai_message(ai_message)
        
        # Update JSON persistence (existing system)
        save_conv(post_id, comment_id, {
            "user": username,
            "comment": user_message,
            "reply": ai_message,
            "timestamp": datetime.now().isoformat()
        })
        
        # Update user state
        if user_id not in self._user_states:
            self._user_states[user_id] = MemoryState(
                user_id=user_id,
                context_window=self.window_size
            )
        
        self._user_states[user_id].add_exchange(user_message, ai_message)
        
        print(f"INFO: Memory updated untuk user: {user_id}")
    
    def get_formatted_history(
        self, 
        user_id: str,
        post_id: str,
        comment_id: str,
        format_style: str = "instagram"
    ) -> str:
        """
        Get formatted conversation history untuk LLM context.
        
        Combines:
        - LangChain memory (recent exchanges)
        - JSON persistence (specific comment thread)
        """
        try:
            # Get LangChain memory context
            memory = self.get_user_memory(user_id)
            langchain_context = memory.buffer
            
            # Get specific comment thread history dari JSON
            thread_history = get_comment_history(post_id, comment_id, limit=3)
            
            # Format untuk Instagram context
            if format_style == "instagram":
                return self._format_instagram_style(langchain_context, thread_history)
            else:
                return self._format_simple(langchain_context)
        
        except Exception as e:
            print(f"WARNING: Failed to get formatted history: {e}")
            return ""
    
    def _format_instagram_style(
        self, 
        langchain_context: str, 
        thread_history: list
    ) -> str:
        """Format history untuk Instagram customer service context"""
        lines = []
        
        # Add thread-specific history first (more relevant)
        if thread_history:
            lines.append("Riwayat Thread Ini:")
            for exchange in thread_history[-3:]:  # Last 3 exchanges
                lines.append(f"User: {exchange['comment']}")
                lines.append(f"z3: {exchange['reply']}")
        
        # Add general conversation context if available
        if langchain_context and len(lines) < 10:  # Avoid too much context
            lines.append("\nKontext Percakapan:")
            lines.append(langchain_context)
        
        return "\n".join(lines) if lines else ""
    
    def _format_simple(self, langchain_context: str) -> str:
        """Simple formatting dari LangChain memory"""
        return langchain_context if langchain_context else ""
    
    def clear_user_memory(self, user_id: str) -> bool:
        """Clear memory untuk specific user"""
        try:
            if user_id in self._user_memories:
                del self._user_memories[user_id]
            
            if user_id in self._user_states:
                del self._user_states[user_id]
            
            print(f"INFO: Cleared memory untuk user: {user_id}")
            return True
        
        except Exception as e:
            print(f"ERROR: Failed to clear memory for {user_id}: {e}")
            return False
    
    def cleanup_old_memories(self) -> None:
        """
        Clean up old memories to prevent memory leaks.
        Called periodically or on memory pressure.
        """
        cutoff_time = datetime.now() - timedelta(hours=self.cleanup_hours)
        users_to_remove = []
        
        for user_id, state in self._user_states.items():
            if state.last_updated < cutoff_time:
                users_to_remove.append(user_id)
        
        for user_id in users_to_remove:
            self.clear_user_memory(user_id)
        
        if users_to_remove:
            print(f"INFO: Cleaned up {len(users_to_remove)} old memories")
    
    def get_active_users_count(self) -> int:
        """Get number of active users dengan memory"""
        return len(self._user_memories)
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory system statistics"""
        total_messages = 0
        for memory in self._user_memories.values():
            total_messages += len(memory.chat_memory.messages)
        
        return {
            "active_users": len(self._user_memories),
            "total_messages": total_messages,
            "window_size": self.window_size,
            "cleanup_hours": self.cleanup_hours,
            "user_states": len(self._user_states)
        }
    
    def export_user_memory(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Export user memory untuk debugging atau migration"""
        if user_id not in self._user_memories:
            return None
        
        memory = self._user_memories[user_id]
        state = self._user_states.get(user_id)
        
        return {
            "user_id": user_id,
            "messages": [
                {
                    "type": type(msg).__name__,
                    "content": msg.content
                }
                for msg in memory.chat_memory.messages
            ],
            "state": state.dict() if state else None,
            "exported_at": datetime.now().isoformat()
        }