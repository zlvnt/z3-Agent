from __future__ import annotations
from pathlib import Path
from typing import Any

from functools import lru_cache
from langchain_core.prompts import ChatPromptTemplate
print(">> imported app.agent router")
from langchain_google_genai import ChatGoogleGenerativeAI
print(">> imported app.agent router google_genai")

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
    # logger.info("Supervisor decided route", route=decision)
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
    """
    @deprecated - Use app.chains.process_with_chain instead
    
    This function provides manual orchestration of router → rag → reply flow.
    It is being replaced by the True Chain implementation in app.chains.conditional_chain.
    
    Migration path:
    OLD: from app.agents.router import handle
    NEW: from app.chains.conditional_chain import process_with_chain
    
    The new chain implementation provides:
    - Better performance (singleton pattern)
    - Built-in monitoring & timing
    - Simplified memory management
    - Same functionality with improved architecture
    
    This function will be removed in a future version.
    """
    mode = supervisor_route(comment)
    # logger.debug("Route decision", mode=mode)

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

    print(f"INFO: Reply sent - mode: {mode}")
    return reply
