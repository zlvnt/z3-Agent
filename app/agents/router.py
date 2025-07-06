"""
LLM-based Supervisor Agent (Gemini).

Menentukan route: direct, rag, websearch.
"""

from __future__ import annotations
from pathlib import Path
from typing import Any

from langchain.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from app.config import settings
from app.services.logger import logger
from app.agents.reply import generate_reply
from app.agents.rag import retrieve_context
from app.services.search import search_web

#LOAD
_SUPPROMPT = ChatPromptTemplate.from_template(
    Path("content/supervisor-prompt.txt").read_text(encoding="utf-8")
)

# --- Inisialisasi Gemini LLM ---
_llm = ChatGoogleGenerativeAI(
    model=settings.MODEL_NAME,      # e.g. "gemini-pro"
    temperature=0,                  # deterministik
)

def supervisor_route(user_input: str) -> str:
    msg = _SUPPROMPT.format_messages(user_input=user_input)
    decision = _llm.invoke(msg).content.strip().lower()
    logger.info("Supervisor route selected", route=decision)
    if decision.startswith(("internal_doc", "rag")):
        return "rag"
    if decision.startswith(("web_search", "websearch")):
        return "websearch"
    return "direct"

def handle(
    comment: str,
    post_id: str,
    comment_id: str,
    username: str,
    **kwargs: Any,
) -> str:
    route = supervisor_route(comment)
    logger.debug("Route decision", route=route)

    if route == "direct":
        reply = generate_reply(comment, post_id, comment_id, username)
    elif route == "rag":
        context = retrieve_context(comment)
        reply = generate_reply(comment, post_id, comment_id, username, context=context)
    elif route == "websearch":
        urls = search_web(comment)
        reply = f"Saya menemukan: {urls[0] if urls else 'tidak ada hasil'}"
    else:
        reply = "Maaf, sistem tidak bisa memproses komentar ini."

    logger.info("Reply sent", route=route)
    return reply
