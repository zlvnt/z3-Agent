from fastapi import APIRouter, Request, BackgroundTasks, HTTPException
from app.config import settings
from app.agent.langchain_z3 import generate_reply   
from app.services.instagram_api import upload_reply     
from app.services.logger import logger                     # util logger
import hmac, hashlib, json

router = APIRouter()


def _verify_signature(secret: str, body: bytes, header_sig: str) -> None:
    """X-Hub-Signature-256 cocok (HMAC-SHA256)."""
    expected = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, header_sig):
        raise HTTPException(status_code=403, detail="Invalid signature")


@router.get("/")
async def verify(
    hub_mode: str | None = None,
    hub_challenge: str | None = None,
    hub_verify_token: str | None = None,
):
    """Endpoint handshake Meta IG Graph."""
    if hub_verify_token == settings.VERIFY_TOKEN:
        return hub_challenge or "ok"
    raise HTTPException(status_code=403, detail="Unauthorized")


@router.post("/")
async def receive(request: Request, bg: BackgroundTasks):
    """Terima event → verifikasi → delegasikan ke background task."""
    raw_body = await request.body()

    _verify_signature(
        settings.APP_SECRET,
        raw_body,
        request.headers.get("X-Hub-Signature-256", ""),
    )

    payload = json.loads(raw_body)
    bg.add_task(process_payload, payload)        # non-blocking
    return {"status": "accepted"}                # < 3 detik respon


# ---------- helper ----------
def process_payload(payload: dict) -> None:
    """Logic pemrosesan — jalan di background thread."""
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            if change.get("field") != "comments":
                continue

            val         = change["value"]
            comment_txt = val.get("text", "")
            comment_id  = val.get("id")
            post_id     = val.get("media", {}).get("id")
            username    = val.get("from", {}).get("username", "")

            if username.lower() == settings.BOT_USERNAME.lower():
                logger.info("Skip self-comment", comment_id=comment_id)
                continue

            try:
                reply_txt = generate_reply(
                    comment_txt,
                    post_id=post_id,
                    comment_id=comment_id,
                    username=username,
                )
                upload_reply(comment_id, reply_txt)
                logger.info(
                    "Reply sent",
                    post_id=post_id,
                    comment_id=comment_id,
                    user=username,
                )
            except Exception as exc:
                logger.exception("Failed to process comment", error=str(exc))
