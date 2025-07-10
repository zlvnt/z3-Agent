from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from app.config import settings
from app.services.logger import logger

_PATH = Path(settings.CONVERSATIONS_PATH)

def _load() -> Dict[str, Dict[str, List[dict]]]:
    if not _PATH.exists():
        logger.info("Conversations file not found", path=str(_PATH))
        return {}
    try:
        data = json.loads(_PATH.read_text(encoding="utf-8"))
        conversations = data.get("conversations", data)
        logger.debug("Conversations loaded", total=len(conversations))
        return conversations
    except Exception as e:
        logger.warning("Failed to load conversations", error=str(e))
        return {}

def _save(data: dict) -> None:
    _PATH.write_text(json.dumps({"conversations": data}, ensure_ascii=False, indent=2), encoding="utf-8")

def add(entry: Dict[str, Any]) -> None:
    convos = _load()
    convos.append(entry)
    _save(convos)

def add(post_id: str, comment_id: str, entry: dict) -> None:
    data = _load()
    if post_id not in data:
        data[post_id] = {}
    if comment_id not in data[post_id]:
        data[post_id][comment_id] = []
    data[post_id][comment_id].append(entry)
    _save(data)

def get_comment_history(post_id: str, comment_id: str, limit: int = 5) -> List[dict]:
    data = _load()
    try:
        history = data[post_id][comment_id]
        return history[-limit:]
    except Exception:
        return []
    
def history(post_id: str = None, comment_id: str = None, limit: int = 50) -> List[dict]:
    data = _load()
    result = []
    if post_id and comment_id:
        result = data.get(post_id, {}).get(comment_id, [])[-limit:]
    elif post_id:
        for cid in data.get(post_id, {}):
            result += data[post_id][cid]
        result = result[-limit:]
    else:
        for p in data.values():
            for conv in p.values():
                result += conv
        result = result[-limit:]
    return result
