"""
Vector-store helper (FAISS default – mudah diganti Pinecone/Chroma).

Env vars yg dipakai
───────────────────
DOCS_DIR     : lokasi file mentah   (default 'docs')
VECTOR_DIR   : lokasi index FAISS   (default 'data/vector_store')
EMB_MODEL    : nama model OpenRouter (default 'mixedbread-ai/mxbai-embed-large')

Functions
─────────
- get_retriever()      ⇒ Singleton `VectorStoreRetriever`
- build_index()        ⇒ Bangun ulang index dari DOCS_DIR
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import List

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain.vectorstores.faiss import FAISS
from langchain.document_loaders import DirectoryLoader, UnstructuredMarkdownLoader, UnstructuredPDFLoader
from langchain.embeddings import OpenAIEmbeddings  # pakai OpenRouter key
from app.config import settings
from app.services.logger import logger

_DOCS_DIR = Path(os.getenv("DOCS_DIR", "docs"))
_VEC_DIR  = Path(os.getenv("VECTOR_DIR", "data/vector_store"))
_MODEL    = os.getenv("EMB_MODEL", "mixedbread-ai/mxbai-embed-large")

_RETRIEVER: FAISS | None = None    # cache singleton


# ────────────────────────────── public api ──────────────────────────────
def get_retriever() -> FAISS:
    global _RETRIEVER
    if _RETRIEVER is None:
        _RETRIEVER = _load_or_build()
    return _RETRIEVER.as_retriever(search_kwargs={"k": 4})


def build_index() -> None:
    """(Re)build index from DOCS_DIR → save to VECTOR_DIR"""
    logger.info("Building vector index …")
    texts = _load_raw_docs()
    docs  = _split_docs(texts)

    embeddings = OpenAIEmbeddings(openai_api_key=settings.OPENROUTER_API_KEY, model=_MODEL)
    vectordb   = FAISS.from_documents(docs, embeddings)

    _VEC_DIR.mkdir(parents=True, exist_ok=True)
    vectordb.save_local(str(_VEC_DIR))
    logger.info("Vector index saved", path=_VEC_DIR, total=len(docs))


# ───────────────────────────── internal util ────────────────────────────
def _load_or_build() -> FAISS:
    if (_VEC_DIR / "index.faiss").exists():
        logger.debug("Loading existing FAISS index", path=_VEC_DIR)
        embeddings = OpenAIEmbeddings(openai_api_key=settings.OPENROUTER_API_KEY, model=_MODEL)
        return FAISS.load_local(str(_VEC_DIR), embeddings)
    build_index()
    return _load_or_build()


def _load_raw_docs() -> List[Document]:
    loaders = [
        DirectoryLoader(str(_DOCS_DIR), glob="**/*.md",  loader_cls=UnstructuredMarkdownLoader),
        DirectoryLoader(str(_DOCS_DIR), glob="**/*.pdf", loader_cls=UnstructuredPDFLoader),
        DirectoryLoader(str(_DOCS_DIR), glob="**/*.txt"),   # default TextLoader
    ]
    docs: List[Document] = []
    for ld in loaders:
        docs.extend(ld.load())
    logger.info("Docs loaded", total=len(docs))
    return docs


def _split_docs(docs: List[Document]) -> List[Document]:
    splitter = RecursiveCharacterTextSplitter(chunk_size=700, chunk_overlap=100)
    return splitter.split_documents(docs)
