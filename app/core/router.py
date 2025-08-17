from __future__ import annotations
from pathlib import Path
from typing import Any

from functools import lru_cache
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from app.config import settings
from app.core.reply import generate_reply
from app.core.rag import retrieve_context

# Pr
_SUPERVISOR_PROMPT = ChatPromptTemplate.from_template(
    Path(settings.SUPERVISOR_PROMPT_PATH).read_text(encoding="utf-8")
)

@lru_cache(maxsize=1)
def _get_llm() -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(
        model=settings.MODEL_NAME,
        temperature=0,
        google_api_key=settings.GEMINI_API_KEY,
    )

def supervisor_route(user_input: str, history_context: str = "") -> str:
    """
    Enhanced supervisor routing with business context and conversation history
    """
    success = True
    routing_mode = "direct"  # default
    
    try:
        msg = _SUPERVISOR_PROMPT.format_messages(
            user_input=user_input,
            history_context=history_context or "No previous conversation"
        )
        decision = _get_llm().invoke(msg).content.strip().lower()
        
        # Debug logging untuk monitoring
        print(f"DEBUG: Supervisor decision: '{decision}' for query: '{user_input[:50]}...'")
        
        # Map supervisor decision ke internal routing
        if decision.startswith(("internal_doc", "rag")):
            routing_mode = "docs"
        elif decision.startswith(("web_search", "websearch")):
            routing_mode = "web"
        elif decision.startswith("all"):
            routing_mode = "all"
        else:
            routing_mode = "direct"
            
    except Exception as e:
        success = False
        print(f"ERROR: Supervisor routing failed: {e}")
        routing_mode = "direct"  # fallback
    
    # Record routing metrics
    _record_routing_decision(routing_mode, success)
    
    return routing_mode


def _record_routing_decision(routing_mode: str, success: bool = True) -> None:
    """Record routing decision for metrics"""
    try:
        from app.monitoring.enhanced_metrics import get_enhanced_metrics_instance
        metrics = get_enhanced_metrics_instance()
        metrics.record_routing_decision(routing_mode, success)
    except Exception as e:
        print(f"WARNING: Routing metrics recording failed: {e}")

def handle(
    comment: str,
    post_id: str,
    comment_id: str,
    username: str,
    **kwargs: Any,
) -> str:

    # For legacy compatibility - get basic history context
    from app.services.history_service import ConversationHistoryService
    try:
        history_context = ConversationHistoryService.get_history_context(post_id, comment_id)
    except:
        history_context = ""
    
    mode = supervisor_route(user_input=comment, history_context=history_context)
    # logger.debug("Route decision", mode=mode)
    context = ""
    if mode in {"docs", "web", "all"}:
        context = retrieve_context(comment, mode=mode)
    # mode=="direct" → context kosong

    reply = generate_reply(
        comment=comment,
        post_id=post_id,
        comment_id=comment_id,
        username=username,
        context=context,
    )

    print(f"INFO: Reply sent - mode: {mode}")
    return reply
