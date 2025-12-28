from __future__ import annotations
from functools import lru_cache
from pathlib import Path
from typing import List, TYPE_CHECKING

from langchain.schema import Document

if TYPE_CHECKING: 
    from langchain_community.vectorstores.faiss import FAISS

from app.config import settings

_DOCS_DIR = Path(settings.DOCS_DIR)
_VEC_DIR = Path(settings.VECTOR_DIR)

def _index_exists() -> bool:
    return (_VEC_DIR / "index.faiss").exists()

@lru_cache(maxsize=1)
def _get_embeddings():
    """Get embedding model with smart fallback support"""
    # Load RAG config for embedding model setting
    from app.core.rag_config import load_rag_config
    try:
        rag_config = load_rag_config("default")
        model_name = rag_config.embedding_model
    except Exception as e:
        print(f"WARNING: Could not load RAG config, using default - error: {e}")
        # Fallback uses research-validated MPNet model (not legacy MiniLM)
        # This ensures better embeddings even if config loading fails
        model_name = 'sentence-transformers/paraphrase-multilingual-mpnet-base-v2'

    # Try HuggingFace embeddings first (best for customer service)
    try:
        from langchain_huggingface import HuggingFaceEmbeddings
        print(f"INFO: Using HuggingFace embeddings - model: {model_name}")
        return HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs={'device': 'cpu'},  # Use CPU for compatibility
            encode_kwargs={'normalize_embeddings': True}  # Better similarity scores
        )
    except Exception as e:
        print(f"WARNING: HuggingFace embeddings failed, falling back to Gemini - error: {e}")

    # Fallback to Gemini embeddings
    from langchain_google_genai import GoogleGenerativeAIEmbeddings
    print(f"INFO: Using Gemini embeddings - model: {settings.MODEL_NAME}")
    return GoogleGenerativeAIEmbeddings(
        model=settings.MODEL_NAME, google_api_key=settings.GEMINI_API_KEY
    )

@lru_cache(maxsize=1)
def _load_vectordb() -> "FAISS":
    from langchain_community.vectorstores.faiss import FAISS
    vectordb = FAISS.load_local(
        str(_VEC_DIR), 
        _get_embeddings(),
        allow_dangerous_deserialization=True  # Safe because we created the files
    )
    print(f"INFO: FAISS index loaded - path: {_VEC_DIR}")
    return vectordb

def get_retriever() -> "FAISS":
    try:
        vectordb = _load_vectordb()
    except Exception as e:
        if _index_exists():
            print(f"ERROR: Failed to load FAISS index - error: {e}")
            raise
        print("WARNING: Vector index not found, building…")
        build_index()
        _load_vectordb.cache_clear()
        vectordb = _load_vectordb()

    # Load retrieval_k from RAG config
    from app.core.rag_config import load_rag_config
    try:
        rag_config = load_rag_config("default")
        retrieval_k = rag_config.retrieval_k
    except Exception as e:
        print(f"WARNING: Could not load RAG config for retrieval_k, using default k=7 - error: {e}")
        retrieval_k = 7

    print(f"INFO: Retriever configured with k={retrieval_k}")
    return vectordb.as_retriever(search_kwargs={"k": retrieval_k})

def build_index() -> None:
    print(f"INFO: Building vector index from docs - docs_dir: {_DOCS_DIR}")
    docs = _load_raw_docs()
    split_docs = _split_docs(docs)
    from langchain_community.vectorstores.faiss import FAISS

    vectordb = FAISS.from_documents(split_docs, _get_embeddings())

    _VEC_DIR.mkdir(parents=True, exist_ok=True)
    vectordb.save_local(str(_VEC_DIR))
    print(f"INFO: Vector index saved - path: {_VEC_DIR}, total: {len(split_docs)}")

def _load_raw_docs() -> List[Document]:
    from langchain_community.document_loaders import (
        DirectoryLoader,
        TextLoader,
    )

    # Use simple TextLoader for all file types (more reliable)
    loaders = [
        DirectoryLoader(str(_DOCS_DIR), glob="**/*.md", loader_cls=TextLoader),
        DirectoryLoader(str(_DOCS_DIR), glob="**/*.txt", loader_cls=TextLoader),
    ]
    docs: List[Document] = []
    for loader in loaders:
        try:
            docs.extend(loader.load())
        except Exception as e:
            print(f"WARNING: Doc load failed - loader: {loader}, error: {e}")
    print(f"INFO: Docs loaded - total: {len(docs)}")
    return docs

def _split_docs(docs: List[Document]) -> List[Document]:
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from app.core.rag_config import load_rag_config

    # Load chunking config
    try:
        rag_config = load_rag_config("default")
        chunk_size = rag_config.chunk_size
        chunk_overlap = rag_config.chunk_overlap
    except Exception as e:
        print(f"WARNING: Could not load RAG config for chunking, using defaults - error: {e}")
        chunk_size = 500
        chunk_overlap = 50

    print(f"INFO: Using RecursiveCharacterTextSplitter - chunk_size={chunk_size}, overlap={chunk_overlap}")
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    split_docs = splitter.split_documents(docs)
    print(f"INFO: Document splitting complete - total chunks: {len(split_docs)}")
    return split_docs
