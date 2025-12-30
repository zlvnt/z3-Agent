"""
Core Chain for z3-Agent

Phase 1 Update:
- Uses UnifiedProcessor when use_unified_processor=true
- Falls back to legacy supervisor_route when disabled
- Handles quality gate results (proceed/flag/escalate)
- Supports HITL escalation flow
"""

from typing import Dict, Any
from langchain_core.runnables import Runnable

from app.core.reply import generate_telegram_reply


def _is_unified_processor_enabled() -> bool:
    """Check if unified processor is enabled in config."""
    try:
        from app.core.rag_config import load_rag_config
        config = load_rag_config("default")
        return getattr(config, 'use_unified_processor', False)
    except Exception:
        return False


class CoreChain(Runnable):
    """
    LangChain-based core chain for AI processing.

    Supports two modes:
    - Unified Processor (Phase 1): Single agent for routing + reformulation + escalation
    - Legacy: Separate supervisor_route + query_agent

    Mode is controlled by use_unified_processor config.
    """

    def __init__(self):
        super().__init__()
        self.use_unified = _is_unified_processor_enabled()
        mode_str = "Unified Processor" if self.use_unified else "Legacy"
        print(f"CoreChain initialized (Mode: {mode_str})")

    def invoke(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        text = inputs.get("text", "")
        history = inputs.get("history", "")

        if not text.strip():
            return {
                "reply": "I didn't receive any message to respond to.",
                "routing_decision": "direct",
                "escalated": False
            }

        if self.use_unified:
            return self._invoke_unified(text, history)
        else:
            return self._invoke_legacy(text, history)

    def _invoke_unified(self, text: str, history: str) -> Dict[str, Any]:
        """Process using unified processor (Phase 1 flow)."""
        try:
            # Step 1: Unified Processor (routing + reformulation + escalation check)
            from app.core.unified_processor import process_query

            processor_result = process_query(query=text, history=history)

            routing_decision = processor_result.get("routing_decision", "direct")
            reformulated_query = processor_result.get("reformulated_query", text)
            escalate_early = processor_result.get("escalate", False)
            escalation_reason = processor_result.get("escalation_reason", "")

            print(f"DEBUG: Processor result - routing: {routing_decision}, escalate: {escalate_early}")

            # Early escalation check (before RAG)
            if escalate_early:
                return self._handle_escalation(
                    original_query=text,
                    reason=escalation_reason,
                    stage="pre_rag"
                )

            # Step 2: Context retrieval with quality gate (if needed)
            context = ""
            quality_action = "proceed"
            quality_score = 0.0

            if routing_decision in ["docs", "web", "all"]:
                from app.core.rag import retrieve_context_with_quality

                # Use reformulated query for better retrieval
                rag_result = retrieve_context_with_quality(
                    query=reformulated_query,
                    mode=routing_decision
                )

                context = rag_result.context
                quality_action = rag_result.action
                quality_score = rag_result.top_score

                print(f"DEBUG: RAG result - action: {quality_action}, score: {quality_score:.2f}")

                # Quality gate check (post-RAG escalation)
                if quality_action == "escalate":
                    return self._handle_escalation(
                        original_query=text,
                        reason=f"Low retrieval quality (score: {quality_score:.2f})",
                        stage="post_rag",
                        context=context  # Include context as fallback
                    )

            # Step 3: Reply generation
            reply = generate_telegram_reply(
                comment=text,  # Use original for natural response
                context=context,
                history_context=history
            )

            # Flag for review if medium quality score
            flagged = quality_action == "proceed_with_flag"
            if flagged:
                print(f"FLAG: Response flagged for human review - score: {quality_score:.2f}")

            return {
                "reply": reply,
                "routing_decision": routing_decision,
                "reformulated_query": reformulated_query,
                "quality_score": quality_score,
                "flagged_for_review": flagged,
                "escalated": False
            }

        except Exception as e:
            print(f"ERROR: Unified processing error: {e}")
            return {
                "reply": "Mohon maaf, terjadi kendala teknis. Silakan coba lagi atau hubungi CS kami.",
                "routing_decision": "error",
                "escalated": False,
                "error": str(e)
            }

    def _invoke_legacy(self, text: str, history: str) -> Dict[str, Any]:
        """Process using legacy flow (supervisor_route + query_agent)."""
        try:
            from app.core.router import supervisor_route
            from app.core.rag import retrieve_context

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
                "routing_decision": routing_decision,
                "escalated": False
            }

        except Exception as e:
            print(f"ERROR: Legacy processing error: {e}")
            return {
                "reply": "Sorry, I encountered an issue processing your message. Please try again.",
                "routing_decision": "error",
                "escalated": False,
                "error": str(e)
            }

    def _handle_escalation(
        self,
        original_query: str,
        reason: str,
        stage: str,
        context: str = ""
    ) -> Dict[str, Any]:
        """
        Handle HITL escalation.

        Args:
            original_query: The user's original query
            reason: Why escalation is needed
            stage: "pre_rag" or "post_rag"
            context: Retrieved context (if any, for post_rag)

        Returns:
            Response dict with escalation info
        """
        print(f"ESCALATION: {stage} - {reason}")

        # Generate escalation message
        escalation_message = (
            "Terima kasih atas pertanyaan Anda. "
            "Untuk memastikan Anda mendapat bantuan terbaik, "
            "saya akan menghubungkan Anda dengan tim Customer Service kami. "
            "Mohon tunggu sebentar, mereka akan segera merespons."
        )

        # TODO: In production, implement actual HITL mechanism:
        # - Send to Telegram CS group
        # - Create ticket in ticketing system
        # - Log for human review queue

        return {
            "reply": escalation_message,
            "routing_decision": "escalate",
            "escalated": True,
            "escalation_reason": reason,
            "escalation_stage": stage,
            "original_query": original_query,
            "context_available": bool(context)
        }

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


def reset_core_chain() -> None:
    """Reset core chain instance (useful when config changes)."""
    global _core_chain
    _core_chain = None


# Helper function for TelegramChannel
async def process_message_with_core(text: str, history: str = "") -> str:
    """
    Process message through core chain.

    Returns only the reply string for backward compatibility.
    """
    chain = get_core_chain()
    inputs = {"text": text, "history": history}
    result = await chain.ainvoke(inputs)
    return result.get("reply", "Mohon maaf, terjadi kendala. Silakan coba lagi.")
