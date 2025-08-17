"""
Instagram core chain - copy of TelegramCoreChain adapted for Instagram parameters.
"""

from typing import Dict, Any
from langchain_core.runnables import Runnable

from app.core.router import supervisor_route
from app.core.rag import retrieve_context  
from app.core.reply import generate_reply


class InstagramCoreChain(Runnable):
    """
    Instagram-specific core chain with proper Instagram parameters.
    """
    
    def __init__(self):
        super().__init__()
        print("🧠 InstagramCoreChain initialized")
    
    def invoke(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute Instagram AI processing pipeline."""
        comment = inputs.get("comment", "")
        post_id = inputs.get("post_id", "")
        comment_id = inputs.get("comment_id", "")
        username = inputs.get("username", "")
        history = inputs.get("history", "")
        
        if not comment.strip():
            return {"reply": "I didn't receive any message to respond to."}
        
        try:
            # Step 1: Route decision
            routing_decision = supervisor_route(
                user_input=comment,
                history_context=history
            )
            
            # Step 2: Context retrieval (if needed)
            context = ""
            if routing_decision in ["docs", "web", "all"]:
                context = retrieve_context(
                    query=comment,
                    mode=routing_decision
                )
            
            # Step 3: Reply generation (Instagram-specific)
            reply = generate_reply(
                comment=comment,
                post_id=post_id,
                comment_id=comment_id,
                username=username,
                context=context,
                history_context=history
            )
            
            return {
                "reply": reply,
                "routing_decision": routing_decision
            }
            
        except Exception as e:
            print(f"❌ Instagram core processing error: {e}")
            return {"reply": "Sorry, I encountered an issue processing your message. Please try again."}
    
    async def ainvoke(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Async version - delegates to sync invoke."""
        return self.invoke(inputs)


# Global instance
_instagram_core_chain = None

def get_instagram_core_chain() -> InstagramCoreChain:
    """Get global InstagramCoreChain instance."""
    global _instagram_core_chain
    if _instagram_core_chain is None:
        _instagram_core_chain = InstagramCoreChain()
    return _instagram_core_chain


# Helper function for InstagramChannel
async def process_instagram_message_with_core(
    comment: str, 
    post_id: str,
    comment_id: str, 
    username: str,
    history: str = ""
) -> str:
    """Process Instagram message through core chain."""
    chain = get_instagram_core_chain()
    inputs = {
        "comment": comment,
        "post_id": post_id,
        "comment_id": comment_id,
        "username": username,
        "history": history
    }
    result = await chain.ainvoke(inputs)
    return result.get("reply", "Sorry, I couldn't generate a response.")