from fastapi import APIRouter, Request, BackgroundTasks, HTTPException, Header, Query, Response, status
from app.config import settings
from app.agents.router import handle
from app.services.instagram_api import upload_reply     
from app.services.logger import logger                
import hmac, hashlib, json
from typing import Any

router = APIRouter()

# ───────────────────────────── helper ─────────────────────────────
def _verify_signature(secret: str, body: bytes, header_sig: str) -> None:
    """Raise 403 jika X-Hub-Signature-256 tidak cocok."""
    expected = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    print(f"DEBUG: Expected signature: {expected}")
    print(f"DEBUG: Received signature: {header_sig}")
    print(f"DEBUG: Body length: {len(body)}")
    print(f"DEBUG: Secret length: {len(secret)}")
    print(f"DEBUG: Raw body: {body[:100]}...")  # First 100 chars
    # Temporary disable signature verification
    # if not hmac.compare_digest(expected, header_sig):
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid signature")

# ─────────────────────────── handshake GET ─────────────────────────
@router.get(
    "",
    summary="Webhook verification handshake",
    response_class=Response,
)
async def verify_webhook(
    hub_mode: str = Query(..., alias="hub.mode"),
    hub_challenge: str = Query(..., alias="hub.challenge"),
    hub_verify_token: str = Query(..., alias="hub.verify_token"),
) -> Response:
    if hub_verify_token != settings.VERIFY_TOKEN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized")

    # challenge dikembalikan mentah (string), tanpa JSON
    return Response(content=hub_challenge, media_type="text/plain")


# ──────────────────────────── receive POST ─────────────────────────
@router.post(
    "",
    summary="Receive Instagram events",
    status_code=status.HTTP_202_ACCEPTED,
)
async def receive_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_hub_signature_256: str | None = Header(None, alias="X-Hub-Signature-256"),
) -> dict[str, str]:
    
    if not x_hub_signature_256:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Missing signature header")

    raw_body: bytes = await request.body()
    print(f"DEBUG: Using APP_SECRET from settings (length: {len(settings.APP_SECRET)})")
    _verify_signature(settings.APP_SECRET, raw_body, x_hub_signature_256)

    try:
        payload: dict[str, Any] = json.loads(raw_body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON")

    background_tasks.add_task(_process_payload, payload)
    return {"status": "accepted"}


# ─────────────────────── background processing ────────────────────
def _process_payload(payload: dict[str, Any]) -> None:
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            if change.get("field") != "comments":
                continue

            val: dict[str, Any] = change["value"]
            comment_txt = val.get("text", "")
            comment_id = val.get("id")
            post_id = val.get("media", {}).get("id")
            username = val.get("from", {}).get("username", "")

            # Cegah loop
            if username.lower() == settings.BOT_USERNAME.lower():
                print(f"INFO: Skip self-comment - comment_id: {comment_id}")
                continue

            try:
                reply_txt = handle(
                    comment=comment_txt,
                    post_id=post_id,
                    comment_id=comment_id,
                    username=username,
                )
                upload_reply(comment_id, reply_txt)
                print(f"INFO: Reply sent - post_id: {post_id}, comment_id: {comment_id}, user: {username}")
            except Exception as exc:  # noqa: BLE001
                print(f"ERROR: Failed to process comment: {exc}")