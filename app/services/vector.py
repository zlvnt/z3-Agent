from __future__ import annotations
from pathlib import Path
from typing import List

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain_community.vectorstores.faiss import FAISS
from langchain_community.document_loaders import DirectoryLoader, UnstructuredMarkdownLoader, UnstructuredPDFLoader
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from app.config import settings
from app.services.logger import logger

_DOCS_DIR = Path(settings.DOCS_DIR)
_VEC_DIR = Path(settings.VECTOR_DIR)
_MODEL = settings.MODEL_NAME

_RETRIEVER: FAISS | None = None    # cache singleton

def get_retriever() -> FAISS:
    global _RETRIEVER
    if _RETRIEVER is not None:
        return _RETRIEVER.as_retriever(search_kwargs={"k": 4})

    if (_VEC_DIR / "index.faiss").exists():
        try:
            embeddings = GoogleGenerativeAIEmbeddings(model=_MODEL, google_api_key=settings.GEMINI_API_KEY)
            vectordb = FAISS.load_local(str(_VEC_DIR), embeddings)
            logger.info("FAISS index loaded", path=_VEC_DIR)
            _RETRIEVER = vectordb
        except Exception as e:
            logger.error("Failed to load FAISS index", error=str(e))
            _RETRIEVER = None
    else:
        logger.warning("Vector index not found, building…")
        build_index()
        return get_retriever()
    return _RETRIEVER.as_retriever(search_kwargs={"k": 4})

def build_index() -> None:
    logger.info("Building vector index from docs", docs_dir=_DOCS_DIR)
    docs = _load_raw_docs()
    split_docs = _split_docs(docs)
    embeddings = GoogleGenerativeAIEmbeddings(model=_MODEL, google_api_key=settings.GEMINI_API_KEY)
    vectordb = FAISS.from_documents(split_docs, embeddings)

    _VEC_DIR.mkdir(parents=True, exist_ok=True)
    vectordb.save_local(str(_VEC_DIR))
    logger.info("Vector index saved", path=_VEC_DIR, total=len(split_docs))

def _load_raw_docs() -> List[Document]:
    loaders = [
        DirectoryLoader(str(_DOCS_DIR), glob="**/*.md", loader_cls=UnstructuredMarkdownLoader),
        DirectoryLoader(str(_DOCS_DIR), glob="**/*.pdf", loader_cls=UnstructuredPDFLoader),
        DirectoryLoader(str(_DOCS_DIR), glob="**/*.txt"),   # fallback TextLoader
    ]
    docs: List[Document] = []
    for loader in loaders:
        try:
            docs.extend(loader.load())
        except Exception as e:
            logger.warning("Doc load failed", loader=str(loader), error=str(e))
    logger.info("Docs loaded", total=len(docs))
    return docs

def _split_docs(docs: List[Document]) -> List[Document]:
    splitter = RecursiveCharacterTextSplitter(chunk_size=700, chunk_overlap=100)
    return splitter.split_documents(docs)
