from __future__ import annotations
from pathlib import Path
from typing import Any, Optional

from functools import lru_cache
from langchain_core.prompts import ChatPromptTemplate
print(">> imported app.agent reply")
from langchain_google_genai import ChatGoogleGenerativeAI
print(">> imported app.agent reply google_genai")

from app.config import settings
from app.services.logger import logger
from app.services.conversation import add as save_conv, get_comment_history
from app.prompt.personality import persona_intro, rules_txt

# Load
_REPLY_TEMPLATE = ChatPromptTemplate.from_template(
    Path(settings.REPLY_PROMPT_PATH).read_text(encoding="utf-8")
)

@lru_cache(maxsize=1)
def _get_llm() -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(
        model=settings.MODEL_NAME,
        temperature=0.7,
        google_api_key=settings.GEMINI_API_KEY,
    )

def _build_history_context(
    post_id: str,
    comment_id: str,
    limit: int = 5
) -> str:
    history = get_comment_history(post_id, comment_id)
    if not history:
        return ""
    slices = history[-limit:]
    ctx_lines = ["Riwayat Percakapan Sebelumnya:"]
    for h in slices:
        ctx_lines.append(f"{h['user']}: {h['comment']}")
        ctx_lines.append(f"z3: {h['reply']}")
    return "\n".join(ctx_lines)

def generate_reply(
    comment: str,
    post_id: str,
    comment_id: str,
    username: str,
    context: Optional[str] = ""
) -> str:
    try:
        history_context = _build_history_context(post_id, comment_id, limit=5)
        context_final = "\n".join([history_context, context or ""]).strip()

        messages = _REPLY_TEMPLATE.format_messages(
            persona_intro=persona_intro(),
            rules=rules_txt(),
            comment=comment,
            context=context_final,
        )
        ai_msg = _get_llm().invoke(messages)
        reply = ai_msg.content.strip()
        print(f"INFO: Generated reply from LLM - comment_id: {comment_id}")
    except Exception as e:
        print(f"ERROR: LLM reply failed - error: {e}")
        reply = "Maaf, sistem gagal membuat balasan otomatis."

    # Simpan
    save_conv(
        post_id, comment_id, {
            "user": username,
            "comment": comment,
            "reply": reply,
        }
    )
    return reply
