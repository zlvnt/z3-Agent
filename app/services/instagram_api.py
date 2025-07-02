from __future__ import annotations

import requests
from app.config import settings
from app.services.logger import logger

BASE_URL = "https://graph.facebook.com/v19.0"

def _url(path: str) -> str:
    return f"{BASE_URL}/{path}"

def _params(extra: dict | None = None) -> dict:
    p = {"access_token": settings.INSTAGRAM_ACCESS_TOKEN}
    if extra:
        p.update(extra)
    return p

# ─────────────────────────── Public helpers ────────────────────────────
def upload_reply(comment_id: str, text: str) -> None:
    """POST <comment_id>/replies"""
    url = _url(f"{comment_id}/replies")
    resp = requests.post(url, params=_params(), data={"message": text}, timeout=10)
    if resp.status_code >= 300:
        logger.error("Failed to upload reply", status=resp.status_code, body=resp.text)
        resp.raise_for_status()
    logger.debug("Reply OK", cid=comment_id)

def get_username(account_id: str | None = None) -> str:
    """Fetch username of the bot account (fallback)."""
    account_id = account_id or settings.INSTAGRAM_ACCOUNT_ID
    url = _url(account_id)
    fields = {"fields": "username"}
    resp = requests.get(url, params=_params(fields), timeout=10).json()
    return resp.get("username", "")
