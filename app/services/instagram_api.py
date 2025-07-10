from __future__ import annotations
import requests

from app.config import settings
from app.services.logger import logger

BASE_URL = "https://graph.facebook.com/v19.0"
GRAPH_API_VERSION = getattr(settings, "GRAPH_API_VERSION", "18.0")
ACCESS_TOKEN = getattr(settings, "INSTAGRAM_ACCESS_TOKEN", "")

def _url(path: str) -> str:
    return f"{BASE_URL}/{path}"

def _params(extra: dict | None = None) -> dict:
    p = {"access_token": settings.INSTAGRAM_ACCESS_TOKEN}
    if extra:
        p.update(extra)
    return p

# ─────────────────────────── Public helpers ────────────────────────────
def upload_reply(comment_id: str, message: str) -> dict:
    url = f"https://graph.facebook.com/v{GRAPH_API_VERSION}/{comment_id}/replies"
    payload = {
        "message": message,
        "access_token": ACCESS_TOKEN,
    }
    try:
        resp = requests.post(url, data=payload, timeout=10)
        result = resp.json()
        if resp.status_code != 200 or "error" in result:
            logger.error("Failed to reply Instagram comment", result=result)
        else:
            logger.info("Reply sent to Instagram comment", comment_id=comment_id)
        return result
    except Exception as e:
        logger.exception("Upload reply to Instagram failed")
        return {"error": str(e)}