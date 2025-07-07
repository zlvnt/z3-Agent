from __future__ import annotations
from typing import Literal

from app.services.vector import get_retriever
from app.services.search import search_web
from app.services.logger import logger

def retrieve_context(
    query: str,
    mode: Literal["docs", "web", "all"] = "docs",
    k_docs: int = 4,
    k_web: int = 3,
    max_len: int = 2000
) -> str:
    contexts = []

    if mode in {"docs", "all"}:
        retriever = get_retriever()
        docs = retriever.get_relevant_documents(query, k=k_docs)
        if docs:
            context_docs = "\n".join(
                f"[Docs] { _safe_content(d.page_content.strip(), max_len) }"
                for d in docs if d.page_content.strip()
            )
            contexts.append(context_docs)
        logger.debug("RAG.docs", found=len(docs))

    if mode in {"web", "all"}:
        snippets = search_web(query, k=k_web)
        if snippets:
            context_web = "\n".join(
                f"[Web] { _safe_content(s.strip(), max_len) }"
                for s in snippets if s.strip()
            )
            contexts.append(context_web)
        logger.debug("RAG.web", found=len(snippets))

    if not contexts:
        logger.warning("No RAG context found", query=query, mode=mode)
        return ""
    return "\n\n".join(contexts)

# ─────────────────────────────────────────────────────── #
#  Utility/Dev: On-demand build index & safe content      #
# ─────────────────────────────────────────────────────── #

def rebuild_index() -> None:
    """
    Bangun ulang vector-store dari folder `settings.DOCS_DIR`.
    Dipanggil manual (CLI) tiap kali dokumen diganti.
    """
    from app.services.vector import build_index  # lazy import agar tidak circular
    build_index()

def _safe_content(text: str, max_len: int = 2_000) -> str:
    """
    Hindari prompt terlalu panjang: potong doc ke max_len karakter.
    """
    return text if len(text) <= max_len else text[: max_len - 1] + "…"

# ─────────────────────────────────────────────────────── #
#  CLI helper: python -m app.agents.rag build             #
# ─────────────────────────────────────────────────────── #
if __name__ == "__main__":
    import sys

    if len(sys.argv) >= 2 and sys.argv[1] in {"build", "rebuild"}:
        print("🔄  Rebuilding vector index …")
        rebuild_index()
        print("✅  Done!")
    else:
        print("Usage: python -m app.agents.rag build")
