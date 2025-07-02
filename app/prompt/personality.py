from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from app.config import settings

_PATH = Path(settings.PERSONALITY_PATH)

def load() -> Dict[str, Any]:
    if not _PATH.exists():
        _PATH.write_text(json.dumps({"prompts": {}, "posts": []}, indent=2))
    return json.loads(_PATH.read_text())

def prompt(kind: str = "caption") -> str:
    return load().get("prompts", {}).get(kind, "")

def post_by_id(post_id: str) -> Dict[str, Any] | None:
    for post in load().get("posts", []):
        if post.get("post_id") == post_id:
            return post
    return None

def caption_by_post_id(post_id: str) -> str:
    post = post_by_id(post_id)
    return post.get("caption", "") if post else ""
