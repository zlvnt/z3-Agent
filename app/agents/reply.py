"""
Comment–reply (dan caption) generator.

• Ambil konteks dokumen via RAG
• Susun prompt dari template
• Panggil LLM (OpenRouter atau Gemini)
• Simpan percakapan ke store
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

from app.config import settings
from app.services.logger import logger
from app.services.conversation import add as save_conv
from app.agents.rag import retrieve_context


# ------------------ load prompt template ------------------
_REPLY_TEMPLATE = ChatPromptTemplate.from_template(
    Path("prompts/reply_template.txt").read_text(encoding="utf-8")
)

# ------------------ init LLM ------------------------------
_llm = ChatOpenAI(
    api_key=settings.OPENROUTER_API_KEY,
    model_name=settings.MODEL_NAME,
    temperature=0.7,
)


# ------------------ public API ----------------------------
def generate_reply(
    comment: str,
    post_id: str,
    comment_id: str,
    username: str,
) -> str:
    """
    Generate AI reply for a single Instagram comment.
    """
    context = retrieve_context(comment)

    prompt = _REPLY_TEMPLATE.format_messages(
        user=comment,
        context=context,
        username=username,
    )

    reply: str = _llm.predict_messages(prompt).content.strip()
    logger.info("LLM reply generated", comment_id=comment_id)

    # save conversation (async write not diperlukan; file kecil)
    save_conv(
        {
            "post_id": post_id,
            "comment_id": comment_id,
            "user": username,
            "comment": comment,
            "reply": reply,
        }
    )
    return reply
