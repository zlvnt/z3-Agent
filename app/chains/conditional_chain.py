"""
Simple Conditional Chain implementation untuk Instagram AI Agent.

Minimal approach: wrap existing router → rag → reply functions
dengan LangChain conditional execution pattern.
"""

from typing import Dict, Any, List
from langchain.base import BaseChain
from langchain.memory import ConversationBufferWindowMemory

# Import existing functions - keep them as is
from app.agents.router import supervisor_route
from app.agents.rag import retrieve_context  
from app.agents.reply import generate_reply


class InstagramConditionalChain(BaseChain):
    """
    Simple conditional chain yang wrap existing functions.
    
    Flow:
    1. Router decision (existing function)
    2. Conditional RAG (existing function) 
    3. Reply generation (existing function)
    4. Memory integration (simple wrapper)
    """
    
    def __init__(self, memory_window: int = 5):
        super().__init__()
        self.memory_window = memory_window
        # Simple per-user memory storage
        self._user_memories: Dict[str, ConversationBufferWindowMemory] = {}
    
    @property
    def input_keys(self) -> List[str]:
        return ["comment", "post_id", "comment_id", "username"]
    
    @property
    def output_keys(self) -> List[str]:
        return ["reply", "route_used", "processing_info"]
    
    def _call(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute conditional chain dengan existing functions.
        Simple dictionary data flow - no complex models needed.
        """
        comment = inputs["comment"]
        post_id = inputs["post_id"] 
        comment_id = inputs["comment_id"]
        username = inputs["username"]
        
        # Step 1: Router decision (existing function)
        route = supervisor_route(comment)
        
        # Step 2: Conditional RAG (existing function)
        context = ""
        if route in {"docs", "web", "all"}:
            context = retrieve_context(comment, mode=route)
        
        # Step 3: Get memory context (simple wrapper)
        memory_context = self._get_memory_context(username, post_id, comment_id)
        
        # Step 4: Reply generation (existing function) 
        reply = generate_reply(
            comment=comment,
            post_id=post_id,
            comment_id=comment_id,
            username=username,
            context=context
        )
        
        # Step 5: Update memory (simple addition)
        self._update_memory(username, comment, reply)
        
        # Return simple dictionary
        return {
            "reply": reply,
            "route_used": route,
            "processing_info": {
                "context_used": bool(context),
                "context_length": len(context),
                "memory_updated": True
            }
        }
    
    def _get_memory_context(self, username: str, post_id: str, comment_id: str) -> str:
        """
        Simple memory wrapper around existing conversation system.
        No need to rebuild - just add LangChain compatibility.
        """
        try:
            # Get existing conversation history
            from app.services.conversation import get_comment_history
            history = get_comment_history(post_id, comment_id, limit=3)
            
            # Format untuk LangChain integration
            if history:
                lines = ["Riwayat Percakapan:"]
                for exchange in history:
                    lines.append(f"User: {exchange['comment']}")
                    lines.append(f"z3: {exchange['reply']}")
                return "\n".join(lines)
            
            return ""
            
        except Exception as e:
            print(f"WARNING: Memory context failed: {e}")
            return ""
    
    def _update_memory(self, username: str, user_msg: str, ai_msg: str) -> None:
        """
        Simple memory update - just add to LangChain memory for runtime.
        Existing conversation.py handles persistence.
        """
        try:
            # Get or create user memory
            if username not in self._user_memories:
                self._user_memories[username] = ConversationBufferWindowMemory(
                    k=self.memory_window,
                    return_messages=False
                )
            
            # Update LangChain memory (runtime cache)
            memory = self._user_memories[username]
            memory.chat_memory.add_user_message(user_msg)
            memory.chat_memory.add_ai_message(ai_msg)
            
            # Persistence handled by generate_reply() → conversation.py
            
        except Exception as e:
            print(f"WARNING: Memory update failed: {e}")
    
    def get_user_memory_context(self, username: str) -> str:
        """Get LangChain memory context untuk user"""
        if username in self._user_memories:
            return self._user_memories[username].buffer
        return ""
    
    def clear_user_memory(self, username: str) -> bool:
        """Clear user memory"""
        if username in self._user_memories:
            del self._user_memories[username]
            return True
        return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Simple stats"""
        return {
            "active_users": len(self._user_memories),
            "memory_window": self.memory_window,
            "total_messages": sum(
                len(mem.chat_memory.messages) 
                for mem in self._user_memories.values()
            )
        }


# Simple factory function
def create_instagram_chain() -> InstagramConditionalChain:
    """Create configured chain instance"""
    return InstagramConditionalChain(memory_window=5)


# Simple async wrapper untuk FastAPI compatibility
async def process_with_chain(
    comment: str,
    post_id: str, 
    comment_id: str,
    username: str
) -> str:
    """
    Simple async wrapper untuk existing chain.
    Drop-in replacement untuk router.handle
    """
    chain = create_instagram_chain()
    
    result = chain.run({
        "comment": comment,
        "post_id": post_id,
        "comment_id": comment_id,
        "username": username
    })
    
    return result["reply"]