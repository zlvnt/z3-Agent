"""
Router module for z3-Agent

Phase 1 Update:
- Added unified processor support (when use_unified_processor=true)
- Legacy supervisor_route kept for backward compatibility
- handle() function updated to use new flow when enabled
"""

from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, Optional

from functools import lru_cache
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from app.config import settings
from app.core.reply import generate_reply
from app.core.rag import retrieve_context, retrieve_context_with_quality


# Legacy supervisor prompt (kept for backward compatibility)
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


def _is_unified_processor_enabled() -> bool:
    """Check if unified processor is enabled in config."""
    try:
        from app.core.rag_config import load_rag_config
        config = load_rag_config("default")
        return getattr(config, 'use_unified_processor', False)
    except Exception:
        return False


def supervisor_route(user_input: str, history_context: str = "") -> str:
    """
    Legacy supervisor routing with business context and conversation history.

    NOTE: When use_unified_processor=true, this function is bypassed.
    Use process_with_unified() instead for the full unified flow.
    """
    success = True
    routing_mode = "direct"  # default

    try:
        msg = _SUPERVISOR_PROMPT.format_messages(
            user_input=user_input,
            history_context=history_context or "No previous conversation"
        )
        decision = _get_llm().invoke(msg).content.strip().lower()

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


def process_with_unified(
    user_input: str,
    history_context: str = ""
) -> Dict[str, Any]:
    """
    Process query using unified processor (Phase 1 flow).

    Returns:
        Dict with routing_decision, reformulated_query, context,
        quality_action, escalate, etc.
    """
    from app.core.unified_processor import process_query

    # Step 1: Unified processor
    processor_result = process_query(query=user_input, history=history_context)

    routing_decision = processor_result.get("routing_decision", "direct")
    reformulated_query = processor_result.get("reformulated_query", user_input)
    escalate = processor_result.get("escalate", False)
    escalation_reason = processor_result.get("escalation_reason", "")

    # Record metrics
    _record_routing_decision(routing_decision, True)

    result = {
        "routing_decision": routing_decision,
        "reformulated_query": reformulated_query,
        "resolved_query": processor_result.get("resolved_query", user_input),
        "escalate": escalate,
        "escalation_reason": escalation_reason,
        "context": "",
        "quality_action": "proceed",
        "quality_score": 0.0
    }

    # Early escalation
    if escalate:
        result["quality_action"] = "escalate"
        return result

    # Step 2: RAG with quality gate (if needed)
    if routing_decision in ["docs", "web", "all"]:
        rag_result = retrieve_context_with_quality(
            query=reformulated_query,
            mode=routing_decision
        )
        result["context"] = rag_result.context
        result["quality_action"] = rag_result.action
        result["quality_score"] = rag_result.top_score

    return result


def _record_routing_decision(routing_mode: str, success: bool = True) -> None:
    """Record routing decision for metrics."""
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
    """
    Handle Instagram comment - main entry point.

    Automatically uses unified processor when enabled,
    falls back to legacy flow otherwise.
    """
    # Get history context
    from app.services.history_service import ConversationHistoryService
    try:
        history_context = ConversationHistoryService.get_history_context(post_id, comment_id)
    except:
        history_context = ""

    # Check if unified processor is enabled
    if _is_unified_processor_enabled():
        return _handle_with_unified(
            comment=comment,
            post_id=post_id,
            comment_id=comment_id,
            username=username,
            history_context=history_context
        )
    else:
        return _handle_legacy(
            comment=comment,
            post_id=post_id,
            comment_id=comment_id,
            username=username,
            history_context=history_context
        )


def _handle_with_unified(
    comment: str,
    post_id: str,
    comment_id: str,
    username: str,
    history_context: str
) -> str:
    """Handle using unified processor (Phase 1 flow)."""

    # Process with unified flow
    result = process_with_unified(comment, history_context)

    # Check for escalation
    if result["escalate"] or result["quality_action"] == "escalate":
        # HITL escalation
        escalation_reason = result.get("escalation_reason", "Low retrieval quality")
        print(f"ESCALATION: {escalation_reason}")

        reply = (
            "Terima kasih atas pertanyaan Anda. "
            "Untuk memastikan Anda mendapat bantuan terbaik, "
            "saya akan menghubungkan Anda dengan tim Customer Service kami. "
            "Mohon tunggu sebentar."
        )
    else:
        # Generate reply
        reply = generate_reply(
            comment=comment,
            post_id=post_id,
            comment_id=comment_id,
            username=username,
            context=result["context"],
            history_context=history_context
        )

    # Flag for review if needed
    if result["quality_action"] == "proceed_with_flag":
        print(f"FLAG: Response flagged for review - score: {result['quality_score']:.2f}")

    print(f"INFO: Reply sent - mode: {result['routing_decision']}, unified=True")
    return reply


def _handle_legacy(
    comment: str,
    post_id: str,
    comment_id: str,
    username: str,
    history_context: str
) -> str:
    """Handle using legacy flow (backward compatibility)."""

    mode = supervisor_route(user_input=comment, history_context=history_context)

    context = ""
    if mode in {"docs", "web", "all"}:
        context = retrieve_context(comment, mode=mode)

    reply = generate_reply(
        comment=comment,
        post_id=post_id,
        comment_id=comment_id,
        username=username,
        context=context,
    )

    print(f"INFO: Reply sent - mode: {mode}, unified=False")
    return reply
