from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from app.config import settings
from app.services.logger import logger

PERSONA_PATH = getattr(settings, "PERSONALITY_PATH", "content/personality1.json")

def load() -> Dict[str, Any]:

    try:
        with open(PERSONA_PATH, encoding="utf-8") as f:
            data = json.load(f)
        return data
    except Exception as e:
        logger.warning("Failed to load personality JSON, using fallback", error=str(e))
        return {
            "identity": {"name": "Z3 Assistant", "role": "AI Customer Service"},
            "rules": {"reply_do": [], "reply_dont": []},
            "prompts": {"reply": "Kamu adalah AI Customer Service. Jawab singkat & ramah."}
        }

def persona_intro() -> str:
    p = load()
    identity = p.get("identity", {})
    template = p.get("prompts", {}).get("reply", "")
    return template.format(
        identity_name=identity.get("name", "Z3 Assistant"),
        identity_role=identity.get("role", "AI Customer Service")
    )

def rules_txt() -> str:
    p = load()
    do_ = "\n".join(p.get("rules", {}).get("reply_do", []))
    dont_ = "\n".join(f"JANGAN: {d}" for d in p.get("rules", {}).get("reply_dont", []))
    return f"{do_}\n{dont_}".strip()
