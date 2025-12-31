"""
RAG (Retrieval-Augmented Generation) Module for z3-Agent

Features:
- quality_gate() for reranker score evaluation
- retrieve_context_with_quality() for full pipeline with quality gate
- retrieve_context() for legacy compatibility
"""

from __future__ import annotations
from typing import Literal, Dict, Any, Tuple
from functools import lru_cache
from dataclasses import dataclass


@dataclass
class QualityGateResult:
    """Result from quality gate evaluation."""
    action: str  # "proceed", "proceed_with_flag", "escalate"
    top_score: float
    context: str
    reasoning: str


# Lazy-load reranker to avoid startup overhead
@lru_cache(maxsize=1)
def _get_reranker():
    """Get singleton reranker instance."""
    from app.core.reranker import BGEReranker
    from app.core.rag_config import load_rag_config

    try:
        rag_config = load_rag_config("default")
        return BGEReranker(
            model_name=rag_config.reranker_model,
            use_fp16=rag_config.reranker_use_fp16
        )
    except Exception as e:
        print(f"WARNING: Could not load reranker config, using defaults - error: {e}")
        return BGEReranker()


def quality_gate(top_score: float, config=None) -> Dict[str, Any]:
    """
    Evaluate retrieval quality based on reranker score.

    Phase 1 Implementation: Simple threshold-based quality gate.

    Args:
        top_score: Highest reranker score from retrieval
        config: RAG config (optional, will load if not provided)

    Returns:
        Dict with:
        - action: "proceed" | "proceed_with_flag" | "escalate"
        - reasoning: explanation of decision
    """
    if config is None:
        from app.core.rag_config import load_rag_config
        try:
            config = load_rag_config("default")
        except:
            config = None

    # Get thresholds from config or use defaults
    threshold_good = getattr(config, 'quality_gate_threshold_good', 0.5) if config else 0.5
    threshold_medium = getattr(config, 'quality_gate_threshold_medium', 0.0) if config else 0.0

    if top_score >= threshold_good:
        return {
            "action": "proceed",
            "reasoning": f"High confidence retrieval (score: {top_score:.2f} >= {threshold_good})"
        }
    elif top_score >= threshold_medium:
        return {
            "action": "proceed_with_flag",
            "reasoning": f"Medium confidence retrieval (score: {top_score:.2f}), flagged for review"
        }
    else:
        return {
            "action": "escalate",
            "reasoning": f"Low confidence retrieval (score: {top_score:.2f} < {threshold_medium}), escalate to HITL"
        }


def retrieve_context_with_quality(
    query: str,
    mode: Literal["docs", "web", "all"] = "docs",
    k_docs: int = 3,
    k_web: int = 3,
    max_len: int = 2000,
) -> QualityGateResult:
    """
    Retrieve context and evaluate quality.

    This is the main function for Phase 1 RAG with quality gate.
    Query reformulation should be done BEFORE calling this (by UnifiedProcessor).

    Args:
        query: The query to search (should be pre-reformulated if needed)
        mode: Retrieval mode
        k_docs: Number of docs to retrieve
        k_web: Number of web results
        max_len: Max length per context item

    Returns:
        QualityGateResult with action, score, context, and reasoning
    """
    from app.core.rag_config import load_rag_config

    # Load config
    try:
        rag_config = load_rag_config("default")
    except Exception as e:
        print(f"WARNING: Could not load RAG config: {e}")
        rag_config = None

    contexts = []
    top_score = -10.0  # Default very low score

    # Docs retrieval
    if mode in {"docs", "all"}:
        from app.services.vector import get_retriever

        retriever = get_retriever()
        docs = retriever.get_relevant_documents(query)

        if docs:
            use_reranker = rag_config.use_reranker if rag_config else True

            if use_reranker:
                reranker = _get_reranker()
                reranker_top_k = rag_config.reranker_top_k if rag_config else 3
                threshold = rag_config.relevance_threshold if rag_config else 1.0

                # Rerank with scores
                reranked_with_scores = reranker.rerank_with_scores(
                    query=query,
                    documents=docs,
                    top_k=len(docs)
                )

                # Get top score for quality gate
                if reranked_with_scores:
                    top_score = reranked_with_scores[0][1]

                # Filter by threshold
                filtered_docs = [
                    doc for doc, score in reranked_with_scores
                    if score >= threshold
                ]

                # Adaptive fallback
                if not filtered_docs and rag_config and rag_config.enable_adaptive_fallback:
                    if reranked_with_scores:
                        threshold_high = getattr(rag_config, 'adaptive_fallback_threshold_high', 0.3)
                        threshold_low = getattr(rag_config, 'adaptive_fallback_threshold_low', 0.2)

                        if top_score >= threshold_high:
                            filtered_docs = [doc for doc, _ in reranked_with_scores[:2]]
                        elif top_score >= threshold_low:
                            filtered_docs = [doc for doc, _ in reranked_with_scores[:1]]
                        else:
                            filtered_docs = [doc for doc, _ in reranked_with_scores[:1]]

                final_docs = filtered_docs[:reranker_top_k] if filtered_docs else [doc for doc, _ in reranked_with_scores[:reranker_top_k]]

            else:
                # Legacy word overlap filtering
                filtered_docs = []
                query_words = set(query.lower().split())
                relevance_threshold = rag_config.relevance_threshold if rag_config else 0.8

                for doc in docs:
                    content_words = set(doc.page_content.lower().split())
                    if query_words and content_words:
                        overlap = len(query_words.intersection(content_words))
                        relevance_score = overlap / len(query_words)
                        if relevance_score >= relevance_threshold:
                            filtered_docs.append(doc)

                final_docs = filtered_docs if filtered_docs else docs
                top_score = 0.5  # Default medium score for non-reranker

            # Build context string
            context_docs = "\n".join(
                f"[Docs] {_safe_content(d.page_content.strip(), max_len)}"
                for d in final_docs if d.page_content.strip()
            )
            if context_docs:
                contexts.append(context_docs)

    # Web retrieval
    if mode in {"web", "all"}:
        from app.services.search import search_web

        snippets = search_web(query, k=k_web)
        if snippets:
            context_web = "\n".join(
                f"[Web] {_safe_content(s.strip(), max_len)}"
                for s in snippets if s.strip()
            )
            contexts.append(context_web)
            # Web search doesn't have reranker score, assume medium quality
            if mode == "web":
                top_score = 0.5

    # Combine contexts
    context = "\n\n".join(contexts) if contexts else ""

    if not context:
        print(f"WARNING: No RAG context found - query: {query}, mode: {mode}")

    # Quality gate evaluation
    gate_result = quality_gate(top_score, rag_config)

    return QualityGateResult(
        action=gate_result["action"],
        top_score=top_score,
        context=context,
        reasoning=gate_result["reasoning"]
    )


def retrieve_context(
    query: str,
    mode: Literal["docs", "web", "all"] = "docs",
    k_docs: int = 3,
    k_web: int = 3,
    max_len: int = 2000,
    relevance_threshold: float = 1.0
) -> str:
    """
    Legacy function for backward compatibility.

    NOTE: For new code, use retrieve_context_with_quality() instead.
    """
    result = retrieve_context_with_quality(
        query=query,
        mode=mode,
        k_docs=k_docs,
        k_web=k_web,
        max_len=max_len
    )
    return result.context


def rebuild_index() -> None:
    """Rebuild the FAISS vector index."""
    from app.services.vector import build_index
    build_index()


def _safe_content(text: str, max_len: int = 2_000) -> str:
    """Truncate text to max length."""
    return text if len(text) <= max_len else text[:max_len - 1] + "..."


if __name__ == "__main__":
    import sys

    if len(sys.argv) >= 2 and sys.argv[1] in {"build", "rebuild"}:
        print("Rebuilding vector index...")
        rebuild_index()
        print("Done!")
    else:
        print("Usage: python -m app.core.rag build")
