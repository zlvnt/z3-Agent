"""
Core Chain for z3-Agent

Simplified architecture:
- Social Mode: Casual replies only (no RAG)
- CS Mode: Unified Processor with quality gates and escalation
- Handles quality gate results (proceed/flag/escalate)
- Supports HITL escalation flow
"""

from typing import Dict, Any
from langchain_core.runnables import Runnable

from app.core.reply import generate_telegram_reply, generate_social_reply
from app.config import settings


class CoreChain(Runnable):
    """
    LangChain-based core chain for AI processing.

    Supports two agent modes:
    1. Social Mode (AGENT_MODE=social):
       - Casual social media replies
       - No RAG, no escalation, no quality gates
       - Direct reply generation only

    2. CS Mode (AGENT_MODE=cs):
       - Unified Processor for routing + reformulation + escalation
       - Full RAG pipeline with quality gates
       - HITL escalation support

    Mode is controlled by AGENT_MODE config (social/cs).
    """

    def __init__(self):
        super().__init__()
        agent_mode = settings.AGENT_MODE.lower()

        if agent_mode == "social":
            print(f"CoreChain initialized (Agent Mode: SOCIAL - casual replies only)")
        else:
            print(f"CoreChain initialized (Agent Mode: CS - Unified Processor)")

    def invoke(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        text = inputs.get("text", "")
        history = inputs.get("history", "")

        if not text.strip():
            return {
                "reply": "I didn't receive any message to respond to.",
                "routing_decision": "direct",
                "escalated": False
            }

        # Check agent mode
        agent_mode = settings.AGENT_MODE.lower()

        if agent_mode == "social":
            return self._invoke_social(text, history)
        elif agent_mode == "cs":
            return self._invoke_unified(text, history)
        else:
            print(f"WARNING: Unknown AGENT_MODE '{agent_mode}', defaulting to social")
            return self._invoke_social(text, history)

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

    def _invoke_social(self, text: str, history: str) -> Dict[str, Any]:
        """
        Process using social mode (casual replies, no RAG).

        Social mode flow:
        - Skip unified processor (no routing)
        - Skip RAG retrieval (no docs/web search)
        - Skip quality gates
        - Skip escalation
        - Direct casual reply generation
        """
        try:
            # Generate casual reply (no context, just history)
            reply = generate_social_reply(
                comment=text,
                history_context=history
            )

            return {
                "reply": reply,
                "routing_decision": "social",
                "mode": "social",
                "escalated": False
            }

        except Exception as e:
            print(f"ERROR: Social mode processing error: {e}")
            return {
                "reply": "Halo! Maaf ada sedikit gangguan. Coba lagi ya!",
                "routing_decision": "error",
                "mode": "social",
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

        # =================================================================
        # TODO: HITL Implementation (Phase 2)
        # =================================================================
        # Current: User gets escalation message, but no actual handoff
        #
        # To implement:
        # 1. Telegram CS Group Notification
        #    - Send alert to CS group with user query + context
        #    - Include chat_id for CS to respond directly
        #
        # 2. Ticketing System Integration
        #    - Create ticket in Zendesk/Freshdesk/custom system
        #    - Include escalation_reason, original_query, context
        #
        # 3. Database Logging
        #    - Log to escalation_queue table
        #    - Track: timestamp, user_id, query, reason, status
        #    - Dashboard untuk CS melihat pending escalations
        #
        # 4. Response Flow
        #    - Option A: Bot bilang "CS akan menghubungi dalam X menit"
        #    - Option B: Transfer langsung ke live chat CS
        # =================================================================

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


async def process_message_with_core_full(text: str, history: str = "") -> Dict[str, Any]:
    """
    Process message through core chain, returning full result dict.

    Includes escalation metadata (escalated, escalation_reason, etc.)
    Used by TelegramChannel for HITL escalation handling.
    """
    chain = get_core_chain()
    inputs = {"text": text, "history": history}
    return await chain.ainvoke(inputs)
