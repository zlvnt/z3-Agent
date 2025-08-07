from __future__ import annotations
from typing import Optional
import json

from functools import lru_cache
from langchain_core.prompts import ChatPromptTemplate
print(">> imported app.agent reply")
from langchain_google_genai import ChatGoogleGenerativeAI
print(">> imported app.agent reply google_genai")

from app.config import settings
from app.services.conversation import add as save_conv

# Load from professional customer service JSON config
def _get_reply_template():
    try:
        with open("content/reply_config1.json", encoding="utf-8") as f:
            config = json.load(f)
        return config.get("reply_template", "{persona_intro}\n\n{rules}\n\nUser: \"{comment}\"\n\nInformasi tambahan (bisa internal docs atau web):\n{context}\n\nJawaban Admin AI:")
    except Exception as e:
        print(f"WARNING: Failed to load reply config1, using fallback: {e}")
        return "{persona_intro}\n\n{rules}\n\nUser: \"{comment}\"\n\nInformasi tambahan (bisa internal docs atau web):\n{context}\n\nJawaban Admin AI:"

def _format_optimized_template(comment: str, context: str, history: str = "") -> dict:
    """Format optimized customer service template"""
    try:
        with open("content/reply_config1.json", encoding="utf-8") as f:
            config = json.load(f)
        
        identity = config.get("identity", {})
        service_guidelines = config.get("service_guidelines", [])
        
        # Format service guidelines array jadi string
        guidelines_text = "Guidelines:\n" + "\n".join([f"- {guideline}" for guideline in service_guidelines])
        
        # Format context and history
        formatted_context = context.strip() if context.strip() else "No additional information available."
        formatted_history = history.strip() if history.strip() else "No previous interaction."
        
        return {
            "comment": comment,
            "context": formatted_context,
            "history": formatted_history,
            "identity_name": identity.get("name", "z3"),
            "company": identity.get("company", "Instagram Business Account"),
            "service_guidelines": guidelines_text
        }
    except Exception as e:
        print(f"WARNING: Failed to format optimized template: {e}")
        return {
            "comment": comment,
            "context": context or "No additional information available.",
            "history": history or "No previous interaction.",
            "identity_name": "z3",
            "company": "Instagram Business Account",
            "service_guidelines": "Guidelines:\n- Provide excellent customer service"
        }

_REPLY_TEMPLATE = ChatPromptTemplate.from_template(_get_reply_template())

@lru_cache(maxsize=1)
def _get_llm() -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(
        model=settings.MODEL_NAME,
        temperature=0.7,
        google_api_key=settings.GEMINI_API_KEY,
    )


def generate_reply(
    comment: str,
    post_id: str,
    comment_id: str,
    username: str,
    context: Optional[str] = "",
    history_context: Optional[str] = None
) -> str:
    try:
        # Use passed history_context or build internally as fallback
        if history_context is None:
            from app.services.history_service import ConversationHistoryService
            history_context = ConversationHistoryService.get_optimized_history_for_reply(post_id, comment_id)
        
        # Use optimized customer service template
        template_vars = _format_optimized_template(
            comment=comment,
            context=context or "",
            history=history_context
        )

        messages = _REPLY_TEMPLATE.format_messages(**template_vars)
        
        # Show final prompt before LLM generation
        print(f"🔍 FINAL PROMPT TO LLM:")
        print(f"{'='*60}")
        print(messages[0].content)
        print(f"{'='*60}")
        
        ai_msg = _get_llm().invoke(messages)
        reply = ai_msg.content.strip()
        print(f"INFO: Generated professional CS reply - comment_id: {comment_id}")
    except Exception as e:
        print(f"ERROR: Professional CS reply failed - error: {e}")
        reply = "Maaf, ada kendala teknis sementara. Tim kami akan segera membantu Anda. Terima kasih atas pengertiannya! 🙏"

    # Simpan
    save_conv(
        post_id, comment_id, {
            "user": username,
            "comment": comment,
            "reply": reply,
        }
    )
    return reply


def generate_telegram_reply(
    comment: str,
    context: Optional[str] = "",
    history_context: Optional[str] = ""
) -> str:
    try:
        # Use same template system as Instagram but without Instagram-specific logic
        template_vars = _format_optimized_template(
            comment=comment,
            context=context or "",
            history=history_context or ""
        )

        messages = _REPLY_TEMPLATE.format_messages(**template_vars)
        
        # Show final prompt for debugging
        print(f"🔍 TELEGRAM FINAL PROMPT TO LLM:")
        print(f"{'='*60}")
        print(messages[0].content)
        print(f"{'='*60}")
        
        ai_msg = _get_llm().invoke(messages)
        reply = ai_msg.content.strip()
        print(f"INFO: Generated Telegram reply")
        
    except Exception as e:
        print(f"ERROR: Telegram reply generation failed - error: {e}")
        reply = "Sorry, I encountered an issue processing your message. Please try again."

    # NO save_conv() call - Telegram uses its own memory system
    return reply
