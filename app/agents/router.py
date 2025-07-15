from __future__ import annotations
from pathlib import Path
from typing import Any

from functools import lru_cache
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from app.config import settings
from app.services.logger import logger
from app.agents.reply import generate_reply
from app.agents.rag import retrieve_context

# Pr
_SUPERVISOR_PROMPT = ChatPromptTemplate.from_template(
    Path(settings.SUPERVISOR_PROMPT_PATH).read_text(encoding="utf-8")
)

@lru_cache(maxsize=1)
def _get_llm() -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(
        model=settings.MODEL_NAME,
        temperature=0,
        google_api_key=settings.GEMINI_API_KEY,
    )

def supervisor_route(user_input: str) -> str:
    msg = _SUPERVISOR_PROMPT.format_messages(user_input=user_input)
    decision = _get_llm().invoke(msg).content.strip().lower()
    logger.info("Supervisor decided route", route=decision)
    if decision.startswith(("internal_doc", "rag")):
        return "docs"
    if decision.startswith(("web_search", "websearch")):
        return "web"
    if decision.startswith("all"):
        return "all"
    return "direct"

def handle(
    comment: str,
    post_id: str,
    comment_id: str,
    username: str,
    **kwargs: Any,
) -> str:
    mode = supervisor_route(comment)
    logger.debug("Route decision", mode=mode)

    context = ""
    if mode in {"docs", "web", "all"}:
        context = retrieve_context(comment, mode=mode)
    # mode=="direct" → context kosong

    reply = generate_reply(
        comment=comment,
        post_id=post_id,
        comment_id=comment_id,
        username=username,
        context=context,
    )

    logger.info("Reply sent", mode=mode)
    return reply
