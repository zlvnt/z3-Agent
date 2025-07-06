"""
Supervisor Agent berbasis LLM:
Menentukan route (direct, rag, websearch) menggunakan prompt supervisor LLM.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

from app.config import settings
from app.services.logger import logger
from app.agents.reply import generate_reply
from app.agents.rag import retrieve_context
from app.services.search import search_web

# Load prompt supervisor (isi sesuai dengan use case kamu)
_SUPERVISOR_PROMPT = ChatPromptTemplate.from_template(
    Path("prompts/supervisor_template.txt").read_text(encoding="utf-8")
)

_llm = ChatOpenAI(
    api_key=settings.OPENROUTER_API_KEY,
    model_name=settings.MODEL_NAME,
    temperature=0,        # No randomness: routing must be deterministic
)

def supervisor_route(user_input: str) -> str:
    """
    Meminta LLM menentukan route: direct, rag, atau websearch.
    Return route string.
    """
    prompt = _SUPERVISOR_PROMPT.format_messages(user_input=user_input)
    decision = _llm.predict_messages(prompt).content.strip().lower()
    logger.info("Supervisor decided route", route=decision)
    if decision.startswith("internal_doc") or decision.startswith("rag"):
        return "rag"
    if decision.startswith("web_search") or decision.startswith("websearch"):
        return "websearch"
    return "direct"

def handle(
    comment: str,
    post_id: str,
    comment_id: str,
    username: str,
    **kwargs: Any,
) -> str:
    """
    Orkestrasi utama: supervisor memilih route, lalu panggil agent yang tepat.
    """
    # 1. Supervisor memilih route
    route = supervisor_route(comment)

    # 2. Eksekusi agent sesuai route
    if route == "direct":
        reply = generate_reply(
            comment=comment,
            post_id=post_id,
            comment_id=comment_id,
            username=username,
        )
    elif route == "rag":
        context = retrieve_context(comment)
        reply = generate_reply(
            comment=comment,
            post_id=post_id,
            comment_id=comment_id,
            username=username,
            context=context,   # kalau reply.py sudah siap menerima context
        )
    elif route == "websearch":
        urls = search_web(comment)
        reply = f"Saya menemukan informasi berikut: {urls[0] if urls else 'Maaf, tidak ditemukan.'}"
    else:
        reply = "Maaf, sistem tidak dapat menentukan cara menjawab komentar ini."
    logger.info("Final reply", route=route, reply=reply)
    return reply
