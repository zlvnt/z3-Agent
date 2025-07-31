from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from app.config import settings

_PATH = Path(settings.CONVERSATIONS_PATH)

def _load() -> Dict[str, Dict[str, List[dict]]]:
    if not _PATH.exists():
        print(f"INFO: Conversations file not found - path: {_PATH}")
        return {}
    try:
        data = json.loads(_PATH.read_text(encoding="utf-8"))
        conversations = data.get("conversations", data)
        print(f"DEBUG: Conversations loaded - total: {len(conversations)}")
        return conversations
    except Exception as e:
        print(f"WARNING: Failed to load conversations - error: {e}")
        return {}

def _save(data: dict) -> None:
    _PATH.write_text(json.dumps({"conversations": data}, ensure_ascii=False, indent=2), encoding="utf-8")

def add(post_id: str, comment_id: str, entry: dict) -> None:
    """Add conversation entry. Now groups by username instead of comment_id."""
    data = _load()
    username = entry.get('user', 'unknown')
    
    if post_id not in data:
        data[post_id] = {}
    if username not in data[post_id]:
        data[post_id][username] = []
    data[post_id][username].append(entry)
    _save(data)

def get_comment_history(post_id: str, comment_id: str, limit: int = 5) -> List[dict]:
    """Get conversation history by post_id and comment_id (backward compatibility)."""
    data = _load()
    try:
        history = data[post_id][comment_id]
        return history[-limit:]
    except Exception:
        return []
        
def get_user_history(post_id: str, username: str, limit: int = 5) -> List[dict]:
    """Get conversation history by post_id and username (new method)."""
    data = _load()
    try:
        history = data[post_id][username]
        return history[-limit:]
    except Exception:
        return []
    
def history(post_id: str = None, comment_id: str = None, limit: int = 50) -> List[dict]:
    """Get conversation history with various filters."""
    data = _load()
    result = []
    if post_id and comment_id:
        # Try both old (comment_id) and new (username) format
        result = data.get(post_id, {}).get(comment_id, [])[-limit:]
    elif post_id:
        for key in data.get(post_id, {}):
            result += data[post_id][key]
        result = result[-limit:]
    else:
        for p in data.values():
            for conv in p.values():
                result += conv
        result = result[-limit:]
    return result
