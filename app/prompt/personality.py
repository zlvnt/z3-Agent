from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from app.config import settings

PERSONA_PATH = settings.PERSONALITY_PATH

def load() -> Dict[str, Any]:

    try:
        with open(PERSONA_PATH, encoding="utf-8") as f:
            data = json.load(f)
        return data
    except Exception as e:
        print(f"WARNING: Failed to load personality JSON, using fallback - error: {e}")
        return {}

def persona_intro() -> str:
    p = load()
    identity = p.get("identity", {})
    template = p.get("prompts", {}).get("reply", "")
    return template.format(
        identity_name=identity.get("name", ""),
        identity_role=identity.get("role", "")
    )

def rules_txt() -> str:
    p = load()
    do_ = "\n".join(p.get("rules", {}).get("reply_do", []))
    dont_ = "\n".join(f"JANGAN: {d}" for d in p.get("rules", {}).get("reply_dont", []))
    return f"{do_}\n{dont_}".strip()