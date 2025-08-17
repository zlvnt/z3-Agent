"""
Instagram webhook handler using the new channel architecture.

Refactored from app/api/webhook.py to use InstagramChannel pattern.
"""

from fastapi import APIRouter, Request, BackgroundTasks, HTTPException, Header, Query, Response, status
from app.config import settings
from .handler import get_instagram_channel
                
import hmac, hashlib, json
import asyncio
from typing import Any

router = APIRouter(prefix="/instagram", tags=["instagram"])

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
    "/webhook",
    summary="Instagram webhook verification handshake",
    response_class=Response,
)
async def webhook_get(
    hub_mode: str = Query(..., alias="hub.mode"),
    hub_challenge: str = Query(..., alias="hub.challenge"),
    hub_verify_token: str = Query(..., alias="hub.verify_token"),
):
    """Instagram webhook GET handshake untuk verifikasi."""
    print(f"GET webhook called - mode: {hub_mode}, token: {hub_verify_token}")
    
    if hub_mode == "subscribe" and hub_verify_token == settings.VERIFY_TOKEN:
        print("Instagram webhook verified successfully")
        return Response(content=hub_challenge, media_type="text/plain")
    else:
        print(f"Instagram webhook verification failed - expected: {settings.VERIFY_TOKEN}, got: {hub_verify_token}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")


async def process_instagram_comment(comment_data: dict) -> None:
    """
    Process Instagram comment through the new channel architecture.
    
    Args:
        comment_data: Instagram comment data extracted from webhook
    """
    try:
        # Get the Instagram channel instance (singleton)
        channel = get_instagram_channel()
        
        # Process through the channel with metrics tracking
        result = await channel.process_with_metrics(comment_data)
        
        print(f"📸 Instagram comment processed: {result}")
        
    except Exception as e:
        print(f"❌ Error processing Instagram comment: {e}")
        # Don't re-raise - webhook should always return 200 to Instagram


# ─────────────────────────── webhook POST ─────────────────────────
@router.post(
    "/webhook",
    summary="Instagram webhook untuk menerima notifikasi",
    status_code=status.HTTP_200_OK,
)
async def webhook_post(
    request: Request,
    background_tasks: BackgroundTasks,
    x_hub_signature_256: str | None = Header(default=None, alias="X-Hub-Signature-256"),
):
    """Instagram webhook POST untuk menerima comment notifications."""
    print("📸 Instagram webhook received")
    
    body = await request.body()
    
    # Signature verification (currently disabled)
    # if x_hub_signature_256:
    #     _verify_signature(settings.APP_SECRET, body, x_hub_signature_256)
    
    try:
        data = json.loads(body)
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in Instagram webhook: {e}")
        raise HTTPException(status_code=400, detail="Invalid JSON format")
    
    if not data.get("entry"):
        print("⚠️ No entry field in Instagram webhook")
        return {"status": "ok"}
    
    # Process each entry in background
    for entry in data["entry"]:
        if "changes" not in entry:
            continue
        
        for change in entry["changes"]:
            if change.get("field") != "comments":
                continue
            
            if "value" not in change:
                continue
                
            value = change["value"]
            if not value.get("text"):
                continue
            
            # Extract comment data
            comment_data = {
                'comment': value.get("text", ""),
                'post_id': value.get("media", {}).get("id", ""),
                'comment_id': value.get("id", ""),
                'username': value.get("from", {}).get("username", ""),
                'timestamp': value.get("created_time", 0)
            }
            
            # Skip self-comments
            username = comment_data.get('username', '')
            if username.lower() == settings.BOT_USERNAME.lower():
                print(f"🔄 Skipping self-comment from: {username}")
                continue
            
            print(f"📸 Processing Instagram comment from @{username}: {comment_data['comment'][:50]}...")
            
            # Process comment in background (non-blocking response)
            background_tasks.add_task(process_instagram_comment, comment_data)
    
    # Return immediate success response to Instagram
    return {"status": "ok"}


@router.get("/webhook/info")
async def webhook_info():
    """Get Instagram webhook information for debugging."""
    try:
        channel = get_instagram_channel()
        
        return {
            "status": "active",
            "channel": "instagram",
            "architecture": "new_channel_based",
            "webhook_url": "/api/instagram/webhook"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "architecture": "new_channel_based"
        }


@router.get("/health")
async def instagram_health_check():
    """Health check endpoint for Instagram channel."""
    try:
        channel = get_instagram_channel()
        
        health_status = {
            "status": "healthy",
            "channel": "instagram",
            "architecture": "new_channel_based",
            "components": {
                "handler": True if channel else False,
            }
        }
        
        return health_status
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "channel": "instagram",
            "architecture": "new_channel_based"
        }