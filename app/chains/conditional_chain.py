"""
wrap existing router → rag → reply functions
with LangChain conditional execution pattern.
"""

from typing import Dict, Any, List, Callable, Optional
from langchain_core.runnables import Runnable
import time

from app.agents.router import supervisor_route
from app.agents.rag import retrieve_context  
from app.agents.reply import generate_reply


class InstagramConditionalChain(Runnable):
    """
    Simple conditional chain:
    Flow:
    1. Router decision (existing function)
    2. Conditional RAG (existing function) 
    3. Reply generation (existing function)
    4. Memory integration (simple wrapper)
    """
    
    def __init__(self, memory_window: int = 5, callbacks: Optional[List[Callable]] = None):
        super().__init__()
        self.memory_window = memory_window
        self.callbacks = callbacks or []
    
    def invoke(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute conditional chain with existing functions.
        """
        comment = inputs["comment"]
        post_id = inputs["post_id"] 
        comment_id = inputs["comment_id"]
        username = inputs["username"]
        
        # Initialize timing info
        timing_info = {}
        total_start = time.time()
        
        # Step 1: Get memory context first
        memory_start = time.time()
        memory_context = self._get_memory_context(post_id, comment_id)
        memory_duration = time.time() - memory_start
        timing_info["memory_time"] = round(memory_duration, 3)
        self._call_callbacks("memory", memory_duration)
        
        # Step 2: Router decision
        router_start = time.time()
        route = supervisor_route(comment, history_context=memory_context)
        router_duration = time.time() - router_start
        timing_info["router_time"] = round(router_duration, 3)
        self._call_callbacks("router", router_duration)
        
        # Step 3: Conditional RAG
        rag_start = time.time()
        context = ""
        if route in {"docs", "web", "all"}:
            context = retrieve_context(comment, mode=route)
        rag_duration = time.time() - rag_start
        timing_info["rag_time"] = round(rag_duration, 3)
        self._call_callbacks("rag", rag_duration)
        
        # Step 4: Reply generation
        reply_start = time.time()
        reply = generate_reply(
            comment=comment,
            post_id=post_id,
            comment_id=comment_id,
            username=username,
            context=context,
            history_context=memory_context
        )
        reply_duration = time.time() - reply_start
        timing_info["reply_time"] = round(reply_duration, 3)
        self._call_callbacks("reply", reply_duration)
        
        # Calculate total time
        total_duration = time.time() - total_start
        timing_info["total_time"] = round(total_duration, 3)
        self._call_callbacks("total", total_duration)
        
        # Return simple dictionary with timing info
        return {
            "reply": reply,
            "route_used": route,
            "processing_info": {
                "context_used": bool(context),
                "context_length": len(context),
                "memory_handled_by_conversation_service": True,
                "timing": timing_info
            }
        }
    
    def _get_memory_context(self, post_id: str, comment_id: str) -> str:
        # Get conversation history using centralized history service
        try:
            from app.services.history_service import ConversationHistoryService
            return ConversationHistoryService.get_history_context(post_id, comment_id)
            
        except Exception as e:
            print(f"WARNING: Memory context failed: {e}")
            return ""
    
    
    
    def _call_callbacks(self, step_name: str, duration: float) -> None:
        for callback in self.callbacks:
            try:
                callback(step_name, duration)
            except Exception as e:
                print(f"WARNING: Callback failed for step {step_name}: {e}")
    
    def add_callback(self, callback: Callable) -> None:
        self.callbacks.append(callback)
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            "memory_window": self.memory_window,
            "using_conversation_service": True,
            "callbacks_count": len(self.callbacks)
        }


# Singleton pattern for chain instance
_chain_instance = None

def get_chain(callbacks: Optional[List[Callable]] = None) -> InstagramConditionalChain:
    global _chain_instance
    if _chain_instance is None:
        _chain_instance = InstagramConditionalChain(memory_window=5, callbacks=callbacks)
    elif callbacks:
        for callback in callbacks:
            _chain_instance.add_callback(callback)
    return _chain_instance


# Simple factory function (deprecated - use get_chain instead)
def create_instagram_chain() -> InstagramConditionalChain:
    return InstagramConditionalChain(memory_window=5)


# Simple async wrapper for FastAPI compatibility
async def process_with_chain(
    comment: str,
    post_id: str, 
    comment_id: str,
    username: str,
    enable_monitoring: bool = True
) -> str:
    # Setup monitoring callbacks if enabled
    callbacks = []
    if enable_monitoring:
        try:
            from app.monitoring.callbacks import file_logger_callback, debug_callback
            callbacks = [file_logger_callback, debug_callback]
        except ImportError:
            print("WARNING: Monitoring callbacks not available")
    
    chain = get_chain(callbacks=callbacks)
    
    result = chain.invoke({
        "comment": comment,
        "post_id": post_id,
        "comment_id": comment_id,
        "username": username
    })
    
    return result["reply"]