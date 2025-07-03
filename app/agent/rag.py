"""
Retrieval-Augmented Generation (RAG) helpers.

Tugas modul ini:
1. Membangun / memuat vector-store (FAISS / Pinecone / Chroma) via services.vector.
2. Menyediakan fungsi `retrieve_context()` yang merangkum dokumen relevan
   ke bentuk string siap disuntikkan ke prompt LLM.
"""

from __future__ import annotations

from typing import List

from app.config import settings
from app.services.vector import get_retriever           # singleton factory
from app.services.logger import logger

# --------------------------------------------------------------------------- #
# Public helpers                                                              #
# --------------------------------------------------------------------------- #
def retrieve_context(query: str, k: int = 4) -> str:
    """
    Ambil `k` dokumen terdekat terhadap `query` dan gabungkan isinya.
    Result dipakai oleh agent reply/caption sebagai konteks.

    Returns
    -------
    str : gabungan dokumen, dipisah garis kosong.
    """
    retriever = get_retriever()
    docs = retriever.get_relevant_documents(query, k=k)      # type: ignore[attr-defined]
    joined = "\n\n".join(_safe_content(doc.page_content) for doc in docs)
    logger.debug("RAG retrieved docs", total=len(docs))
    return joined


# --------------------------------------------------------------------------- #
# Optional: On-demand build / refresh index                                   #
# --------------------------------------------------------------------------- #
def rebuild_index() -> None:
    """
    Bangun ulang vector-store dari folder `settings.DOCS_DIR`.
    Dipanggil manual (CLI) tiap kali dokumen mentah diganti.
    """
    from app.services.vector import build_index  # lazy import agar tidak melingkar
    build_index()


# --------------------------------------------------------------------------- #
# Internal util                                                               #
# --------------------------------------------------------------------------- #
def _safe_content(text: str, max_len: int = 2_000) -> str:
    """
    Hindari prompt terlalu panjang: potong doc ke max_len karakter.
    """
    return text if len(text) <= max_len else text[: max_len - 1] + "…"


# --------------------------------------------------------------------------- #
# CLI helper: `python -m app.agents.rag build`                                #
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    import sys

    if len(sys.argv) >= 2 and sys.argv[1] in {"build", "rebuild"}:
        print("🔄  Rebuilding vector index …")
        rebuild_index()
        print("✅  Done!")
    else:
        print("Usage: python -m app.agents.rag build")
