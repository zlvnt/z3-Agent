"""
RAG Test Endpoint - Step-by-step RAG pipeline debugging interface.

Exposes each RAG step individually:
1. Unified Processor (routing + reformulation)
2. Raw document retrieval
3. Reranking with per-document scores
4. Quality gate evaluation
"""

import time
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter()


# --- Request/Response Models ---

class RAGTestRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=4096)
    mode: str = Field(default="docs", pattern="^(docs|web|all)$")
    k_docs: int = Field(default=7, ge=1, le=50)
    use_reranker: bool = True
    reranker_top_k: int = Field(default=3, ge=1, le=20)
    skip_unified_processor: bool = False


class DocumentResult(BaseModel):
    content: str
    source: Optional[str] = None
    reranker_score: Optional[float] = None


class RAGTestResponse(BaseModel):
    # Step 1: Unified Processor
    unified_processor: Optional[dict] = None

    # Step 2: Raw retrieved documents
    raw_documents: list[DocumentResult] = []

    # Step 3: Reranked documents with scores
    reranked_documents: list[DocumentResult] = []

    # Step 4: Quality Gate
    quality_gate: Optional[dict] = None

    # Meta
    final_context: str = ""
    config_used: dict = {}
    processing_time_ms: float = 0.0
    error: Optional[str] = None


# --- Endpoint ---

@router.post("/rag/test", response_model=RAGTestResponse)
async def test_rag(request: RAGTestRequest):
    """Test RAG pipeline step-by-step with full visibility into each stage."""
    start_time = time.time()

    try:
        from app.core.rag_config import load_rag_config
        rag_config = load_rag_config("default")
    except Exception as e:
        rag_config = None

    search_query = request.query
    up_result = None

    # --- Step 1: Unified Processor ---
    if not request.skip_unified_processor:
        try:
            from app.core.unified_processor import process_query
            up_result = process_query(query=request.query, history="")
            # Use reformulated query for RAG if routing is docs
            if up_result.get("routing_decision") in ("docs", "web", "all"):
                search_query = up_result.get("reformulated_query", request.query)
        except Exception as e:
            up_result = {"error": str(e)}

    # --- Step 2: Raw Document Retrieval ---
    raw_documents = []
    raw_docs_objects = []

    if request.mode in ("docs", "all"):
        try:
            from app.services.vector import get_retriever
            retriever = get_retriever()
            raw_docs_objects = retriever.get_relevant_documents(search_query)

            for doc in raw_docs_objects:
                raw_documents.append(DocumentResult(
                    content=doc.page_content[:500],
                    source=doc.metadata.get("source", "unknown"),
                ))
        except Exception as e:
            return RAGTestResponse(
                unified_processor=up_result,
                error=f"Retrieval failed: {e}",
                processing_time_ms=round((time.time() - start_time) * 1000, 2),
            )

    # --- Step 3: Reranking ---
    reranked_documents = []
    top_score = -10.0

    if raw_docs_objects and request.use_reranker:
        try:
            from app.core.rag import _get_reranker
            reranker = _get_reranker()
            reranked_with_scores = reranker.rerank_with_scores(
                query=search_query,
                documents=raw_docs_objects,
                top_k=len(raw_docs_objects),
            )

            if reranked_with_scores:
                top_score = reranked_with_scores[0][1]

            for doc, score in reranked_with_scores:
                reranked_documents.append(DocumentResult(
                    content=doc.page_content[:500],
                    source=doc.metadata.get("source", "unknown"),
                    reranker_score=round(score, 4),
                ))
        except Exception as e:
            reranked_documents = [DocumentResult(content=f"Reranker error: {e}")]
    elif raw_docs_objects:
        top_score = 0.5

    # --- Step 4: Quality Gate ---
    gate_result = None
    if raw_docs_objects:
        try:
            from app.core.rag import quality_gate
            gate_result = quality_gate(top_score, rag_config)
            gate_result["top_score"] = round(top_score, 4)
        except Exception as e:
            gate_result = {"error": str(e)}

    # --- Build final context ---
    if reranked_documents:
        top_k = request.reranker_top_k
        final_docs = reranked_documents[:top_k]
    elif raw_documents:
        final_docs = raw_documents
    else:
        final_docs = []

    final_context = "\n\n".join(
        f"[Docs] {d.content}" for d in final_docs if d.content
    )

    # --- Config used ---
    config_used = {}
    if rag_config:
        config_used = {
            "embedding_model": rag_config.embedding_model,
            "retrieval_k": rag_config.retrieval_k,
            "use_reranker": request.use_reranker,
            "reranker_model": rag_config.reranker_model,
            "reranker_top_k": request.reranker_top_k,
            "quality_gate_threshold_good": rag_config.quality_gate_threshold_good,
            "quality_gate_threshold_medium": rag_config.quality_gate_threshold_medium,
            "relevance_threshold": rag_config.relevance_threshold,
        }

    return RAGTestResponse(
        unified_processor=up_result,
        raw_documents=raw_documents,
        reranked_documents=reranked_documents,
        quality_gate=gate_result,
        final_context=final_context,
        config_used=config_used,
        processing_time_ms=round((time.time() - start_time) * 1000, 2),
    )
