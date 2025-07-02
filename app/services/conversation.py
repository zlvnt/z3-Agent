from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from app.config import settings
from app.services.logger import logger

_PATH = Path(settings.CONVERSATIONS_PATH)

def _load() -> List[Dict[str, Any]]:
    if _PATH.exists():
        try:
            return json.loads(_PATH.read_text())
        except json.JSONDecodeError:
            logger.warning("Corrupt conversations.json – recreating empty")
    return []

def _save(data: List[Dict[str, Any]]) -> None:
    _PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2))

def add(entry: Dict[str, Any]) -> None:
    convos = _load()
    convos.append(entry)
    _save(convos)

def history(limit: int = 50) -> List[Dict[str, Any]]:
    return _load()[-limit:]
