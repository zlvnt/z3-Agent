import time
from datetime import datetime
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.config import settings
from app.core.chain import process_message_with_core_full
from app.channels.telegram.memory import get_telegram_memory
from app.monitoring.enhanced_metrics import get_enhanced_metrics_instance
from app.monitoring.request_logger import log_user_request

router = APIRouter()


# --- Request/Response Models ---

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4096)
    session_id: str = Field(default="web_default", max_length=100)


class ChatResponse(BaseModel):
    reply: str
    routing_decision: str
    escalated: bool
    reformulated_query: Optional[str] = None
    quality_score: Optional[float] = None
    flagged_for_review: Optional[bool] = None
    escalation_reason: Optional[str] = None
    escalation_stage: Optional[str] = None
    error: Optional[str] = None
    session_id: str
    agent_mode: str
    processing_time_ms: float
    timestamp: str


# --- Endpoints ---

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Direct chat endpoint for web testing interface."""
    start_time = time.time()

    session_id = f"web_{request.session_id}"

    # Get conversation history
    memory = get_telegram_memory()
    history = memory.get_history(session_id)

    # Process through core chain
    result = await process_message_with_core_full(
        text=request.message,
        history=history,
    )

    # Save interaction to memory
    reply = result.get("reply", "")
    memory.save_interaction(
        session_id=session_id,
        user_message=request.message,
        bot_reply=reply,
    )

    # Record metrics
    duration = time.time() - start_time
    success = result.get("routing_decision") != "error"
    metrics = get_enhanced_metrics_instance()
    metrics.record_channel_request("web", duration, success, request.session_id)

    routing_decision = result.get("routing_decision", "unknown")
    if routing_decision:
        metrics.record_routing_decision(routing_decision, success)

    # Log request
    log_user_request(
        channel="web",
        username=request.session_id,
        query=request.message,
        routing_mode=routing_decision,
        duration=duration,
        success=success,
        error_message=result.get("error"),
    )

    return ChatResponse(
        reply=reply,
        routing_decision=routing_decision,
        escalated=result.get("escalated", False),
        reformulated_query=result.get("reformulated_query"),
        quality_score=result.get("quality_score"),
        flagged_for_review=result.get("flagged_for_review"),
        escalation_reason=result.get("escalation_reason"),
        escalation_stage=result.get("escalation_stage"),
        error=result.get("error"),
        session_id=request.session_id,
        agent_mode=settings.AGENT_MODE,
        processing_time_ms=round(duration * 1000, 2),
        timestamp=datetime.now().isoformat(),
    )


@router.get("/config")
async def get_config():
    """Return current agent configuration (no secrets)."""
    return {
        "agent_mode": settings.AGENT_MODE,
        "model_name": settings.MODEL_NAME,
        "embedding_model": settings.EMBEDDING_MODEL,
        "use_reranker": settings.USE_RERANKER,
        "reranker_model": settings.RERANKER_MODEL,
        "reranker_top_k": settings.RERANKER_TOP_K,
        "retrieval_k": settings.RETRIEVAL_K,
        "chunk_size": settings.CHUNK_SIZE,
        "chunk_overlap": settings.CHUNK_OVERLAP,
        "quality_gate_threshold_good": settings.QUALITY_GATE_THRESHOLD_GOOD,
        "quality_gate_threshold_medium": settings.QUALITY_GATE_THRESHOLD_MEDIUM,
        "use_unified_processor": settings.USE_UNIFIED_PROCESSOR,
        "reply_temperature": settings.REPLY_TEMPERATURE,
        "unified_processor_temperature": settings.UNIFIED_PROCESSOR_TEMPERATURE,
        "relevance_threshold": settings.RELEVANCE_THRESHOLD,
        "enable_adaptive_fallback": settings.ENABLE_ADAPTIVE_FALLBACK,
    }
