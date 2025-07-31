from __future__ import annotations
from typing import Literal
import re


def retrieve_context(
    query: str,
    mode: Literal["docs", "web", "all"] = "docs",
    k_docs: int = 3, 
    k_web: int = 3,
    max_len: int = 2000,
    relevance_threshold: float = 0.8
) -> str:
    contexts = []

    if mode in {"docs", "all"}:
        from app.services.vector import get_retriever

        retriever = get_retriever()
        docs = retriever.get_relevant_documents(query, k=k_docs)
        
        # Apply simple relevance filtering (threshold 0.8)
        if docs:
            # Filter docs based on simple content relevance
            filtered_docs = []
            query_words = set(query.lower().split())
            
            for doc in docs:
                content_words = set(doc.page_content.lower().split())
                if query_words and content_words:
                    # Simple word overlap score
                    overlap = len(query_words.intersection(content_words))
                    relevance_score = overlap / len(query_words)
                    
                    if relevance_score >= relevance_threshold:
                        filtered_docs.append(doc)
            
            # Use filtered docs if any pass threshold, otherwise use all
            final_docs = filtered_docs if filtered_docs else docs
            
            context_docs = "\n".join(
                f"[Docs] { _safe_content(d.page_content.strip(), max_len) }"
                for d in final_docs if d.page_content.strip()
            )
            contexts.append(context_docs)
            print(f"DEBUG: RAG.docs - found: {len(docs)}, filtered: {len(final_docs)}")

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
        print("Usage: python -m app.agents.rag build")
