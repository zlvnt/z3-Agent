from __future__ import annotations
from typing import Literal
from functools import lru_cache
import re


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


def retrieve_context(
    query: str,
    mode: Literal["docs", "web", "all"] = "docs",
    k_docs: int = 3,
    k_web: int = 3,
    max_len: int = 2000,
    relevance_threshold: float = 1.0  # BGE score threshold (changed from 0.8)
) -> str:
    """
    Retrieve context from docs/web with optional query reformulation.

    Flow:
    1. Query agent analyzes & reformulates query (if enabled)
    2. Retrieves documents using (possibly reformulated) query
    3. Reranks documents (if enabled)
    4. Returns formatted context
    """
    contexts = []
    original_query = query  # Keep original for logging

    # Step 0: Query agent analysis & reformulation (if enabled)
    agent_result = None
    if mode in {"docs", "all"}:
        from app.core.rag_config import load_rag_config

        try:
            rag_config = load_rag_config("default")
            use_query_agent = getattr(rag_config, 'use_query_agent', False)

            if use_query_agent:
                from app.core.query_agent import analyze_query
                agent_result = analyze_query(query)

                # Use reformulated query if needed
                if agent_result.get("needs_reformulation", False):
                    query = agent_result["reformulated_query"]
                    print(f"DEBUG: Query reformulated: '{original_query}' → '{query}'")
                    print(f"DEBUG: Reformulation reason: {agent_result.get('reformulation_reasoning', 'N/A')}")
                else:
                    print(f"DEBUG: Query NOT reformulated (agent decided no need)")
        except Exception as e:
            print(f"WARNING: Query agent failed, using original query - error: {e}")

    if mode in {"docs", "all"}:
        from app.services.vector import get_retriever
        from app.core.rag_config import load_rag_config

        # Load RAG config
        try:
            rag_config = load_rag_config("default")
        except Exception as e:
            print(f"WARNING: Could not load RAG config, using defaults - error: {e}")
            rag_config = None

        retriever = get_retriever()
        # Note: k is now controlled by config in get_retriever(), not here
        docs = retriever.get_relevant_documents(query)

        # Apply reranking if enabled, otherwise use word overlap filtering
        if docs:
            use_reranker = rag_config.use_reranker if rag_config else True

            if use_reranker:
                # Use BGE cross-encoder reranker (research-validated: +5.7% precision)
                print(f"DEBUG: RAG.docs - retrieved {len(docs)} candidates, reranking...")
                reranker = _get_reranker()
                reranker_top_k = rag_config.reranker_top_k if rag_config else 3
                threshold = rag_config.relevance_threshold if rag_config else 1.0

                # Rerank with scores
                reranked_with_scores = reranker.rerank_with_scores(
                    query=query,
                    documents=docs,
                    top_k=len(docs)  # Get all with scores for filtering
                )

                # Filter by threshold
                filtered_docs = [
                    doc for doc, score in reranked_with_scores
                    if score >= threshold
                ]

                # Adaptive fallback: if no docs pass threshold, use top chunks
                if not filtered_docs and rag_config and rag_config.enable_adaptive_fallback:
                    if reranked_with_scores:
                        top_score = reranked_with_scores[0][1]
                        if top_score >= 0.3:
                            filtered_docs = [doc for doc, _ in reranked_with_scores[:2]]
                        elif top_score >= 0.2:
                            filtered_docs = [doc for doc, _ in reranked_with_scores[:1]]
                        else:
                            filtered_docs = [doc for doc, _ in reranked_with_scores[:1]]
                        print(f"DEBUG: RAG.docs - adaptive fallback activated (top_score={top_score:.2f})")

                # Final docs: use filtered if any, otherwise use top reranked
                final_docs = filtered_docs[:reranker_top_k] if filtered_docs else [doc for doc, _ in reranked_with_scores[:reranker_top_k]]

                print(f"DEBUG: RAG.docs - reranked: {len(docs)} → filtered by threshold: {len(filtered_docs)} → final: {len(final_docs)}")

            else:
                # Fallback to simple word overlap filtering (legacy)
                print(f"DEBUG: RAG.docs - using word overlap filtering (reranker disabled)")
                filtered_docs = []
                query_words = set(query.lower().split())

                for doc in docs:
                    content_words = set(doc.page_content.lower().split())
                    if query_words and content_words:
                        overlap = len(query_words.intersection(content_words))
                        relevance_score = overlap / len(query_words)

                        if relevance_score >= relevance_threshold:
                            filtered_docs.append(doc)

                final_docs = filtered_docs if filtered_docs else docs
                print(f"DEBUG: RAG.docs - word overlap: {len(docs)} → {len(final_docs)}")

            # Build context string
            context_docs = "\n".join(
                f"[Docs] { _safe_content(d.page_content.strip(), max_len) }"
                for d in final_docs if d.page_content.strip()
            )
            contexts.append(context_docs)

    if mode in {"web", "all"}:
        from app.services.search import search_web

        snippets = search_web(query, k=k_web)
        if snippets:
            context_web = "\n".join(
                f"[Web] { _safe_content(s.strip(), max_len) }"
                for s in snippets if s.strip()
            )
            contexts.append(context_web)
        print(f"DEBUG: RAG.web - found: {len(snippets)}")

    if not contexts:
        print(f"WARNING: No RAG context found - query: {query}, mode: {mode}")
        return ""
    return "\n\n".join(contexts)

def rebuild_index() -> None:
    from app.services.vector import build_index
    build_index()

def _safe_content(text: str, max_len: int = 2_000) -> str:
    return text if len(text) <= max_len else text[: max_len - 1] + "…"

if __name__ == "__main__":
    import sys

    if len(sys.argv) >= 2 and sys.argv[1] in {"build", "rebuild"}:
        print("🔄  Rebuilding vector index …")
        rebuild_index()
        print("✅  Done!")
    else:
        print("Usage: python -m app.core.rag build")