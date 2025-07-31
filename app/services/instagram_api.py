from __future__ import annotations
import requests

from app.config import settings

INSTAGRAM_API_BASE_URL = settings.INSTAGRAM_API_BASE_URL
GRAPH_API_VERSION = settings.GRAPH_API_VERSION
ACCESS_TOKEN = settings.INSTAGRAM_ACCESS_TOKEN

def upload_reply(comment_id: str, message: str) -> dict:
    url = f"{INSTAGRAM_API_BASE_URL}/v{GRAPH_API_VERSION}/{comment_id}/replies"
    payload = {
        "message": message,
        "access_token": ACCESS_TOKEN,
    }
    try:
        resp = requests.post(url, data=payload, timeout=10)
        result = resp.json()
        if resp.status_code != 200 or "error" in result:
            print(f"ERROR: Failed to reply Instagram comment - result: {result}")
        else:
            print(f"INFO: Reply sent to Instagram comment - comment_id: {comment_id}")
        return result
    except Exception as e:
        print(f"ERROR: Upload reply to Instagram failed - {e}")
        return {"error": str(e)}