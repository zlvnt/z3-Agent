from __future__ import annotations
from pathlib import Path
from typing import Any, Optional

from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage

from app.config import settings
from app.services.logger import logger
from app.services.conversation import add as save_conv

# Load
_REPLY_TEMPLATE = ChatPromptTemplate.from_template(
    Path("content/reply-prompt.txt").read_text(encoding="utf-8")
)

# Inisialisasi model Gemini
_llm = ChatGoogleGenerativeAI(
    model=settings.MODEL_NAME,  # harus cocok dengan .env
    temperature=0.7,
    google_api_key=settings.GEMINI_API_KEY,  # opsional jika tidak via ENV
)

def generate_reply(
    comment: str,
    post_id: str,
    comment_id: str,
    username: str,
    context: Optional[str] = ""
) -> str:
    """
    Generate AI reply. Jika ada context, disuntik ke prompt.
    """
    # Format pesan untuk LLM
    messages = _REPLY_TEMPLATE.format_messages(
        user=comment,
        username=username,
        context=context or ""
    )

    # Kirim ke Gemini
    ai_msg = _llm.invoke(messages)
    reply = ai_msg.content.strip()
    logger.info("Generated reply from LLM", comment_id=comment_id)

    # Simpan percakapan
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
