"""
Simple core chain for Telegram.

"""

from typing import Dict, Any
from langchain_core.runnables import Runnable

from app.core.router import supervisor_route
from app.core.rag import retrieve_context  
from app.core.reply import generate_reply, generate_telegram_reply


class CoreChain(Runnable):
    """
    Simple LangChain-based core chain for Telegram AI processing.

    """
    
    def __init__(self):
        super().__init__()
        print("🧠 CoreChain initialized")
    
    def invoke(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        text = inputs.get("text", "")
        history = inputs.get("history", "")
        
        if not text.strip():
            return {"reply": "I didn't receive any message to respond to."}
        
        try:
            # Step 1: Route decision
            routing_decision = supervisor_route(
                user_input=text,
                history_context=history
            )
            
            # Step 2: Context retrieval (if needed)
            context = ""
            if routing_decision in ["docs", "web", "all"]:
                context = retrieve_context(
                    query=text,
                    mode=routing_decision
                )
            
            # Step 3: Reply generation
            reply = generate_telegram_reply(
                comment=text,
                context=context,
                history_context=history
            )
            
            return {
                "reply": reply,
                "routing_decision": routing_decision
            }
            
        except Exception as e:
            print(f"❌ Core processing error: {e}")
            return {"reply": "Sorry, I encountered an issue processing your message. Please try again."}
    
    async def ainvoke(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Async version - delegates to sync invoke."""
        return self.invoke(inputs)


# Global instance
_core_chain = None

def get_core_chain() -> CoreChain:
    """Get global CoreChain instance."""
    global _core_chain
    if _core_chain is None:
        _core_chain = CoreChain()
    return _core_chain


# Helper function for TelegramChannel
async def process_message_with_core(text: str, history: str = "") -> str:
    chain = get_core_chain()
    inputs = {"text": text, "history": history}
    result = await chain.ainvoke(inputs)
    return result.get("reply", "Sorry, I couldn't generate a response.")