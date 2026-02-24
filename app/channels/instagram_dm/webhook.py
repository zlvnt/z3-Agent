"""
Instagram DM webhook handler using channel architecture.

This module provides the webhook endpoint for Instagram Direct Messages, utilizing
the InstagramDMChannel implementation for clean separation of concerns.
"""

import json
from fastapi import APIRouter, Request, BackgroundTasks, HTTPException, Query
from typing import Dict, Any

from .handler import get_instagram_dm_channel

router = APIRouter(prefix="/instagram_dm", tags=["instagram_dm"])


async def process_instagram_dm_entry(entry: Dict[str, Any]) -> None:
    """
    Process Instagram DM entry through the channel architecture.

    Args:
        entry: Instagram messaging entry object
    """
    try:
        # Get the Instagram DM channel instance (singleton)
        channel = get_instagram_dm_channel()

        # Extract messaging events
        messaging = entry.get("messaging", [])

        for message_event in messaging:
            # Process each message through the channel
            result = await channel.process_with_metrics(message_event)
            print(f"📸 Instagram DM processed: {result}")

    except Exception as e:
        print(f"❌ Error processing Instagram DM entry: {e}")
        # Don't re-raise - webhook should always return 200


@router.get("/webhook")
async def instagram_dm_webhook_verify(
    hub_mode: str = Query(alias="hub.mode"),
    hub_verify_token: str = Query(alias="hub.verify_token"),
    hub_challenge: str = Query(alias="hub.challenge")
):
    """
    Instagram webhook verification endpoint (GET).

    Instagram sends a GET request to verify the webhook URL during setup.

    Args:
        hub_mode: Should be "subscribe"
        hub_verify_token: Verification token configured in Meta Dashboard
        hub_challenge: Random string to echo back

    Returns:
        int: Challenge string if verification succeeds

    Raises:
        HTTPException: 403 if verification fails
    """
    from app.config import settings

    print(f"📸 Instagram DM webhook verification request")
    print(f"   Mode: {hub_mode}")
    print(f"   Token: {hub_verify_token}")

    # Verify token matches
    if hub_mode == "subscribe" and hub_verify_token == settings.VERIFY_TOKEN:
        print("✅ Instagram DM webhook verified successfully")
        return int(hub_challenge)
    else:
        print("❌ Instagram DM webhook verification failed")
        raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/webhook")
async def instagram_dm_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Instagram DM webhook endpoint (POST).

    This endpoint receives Instagram messaging events and processes them through
    the channel architecture. It provides immediate response while processing
    messages in the background.

    Instagram Messaging webhook structure:
    {
        "object": "instagram",
        "entry": [{
            "id": "PAGE_ID",
            "time": 1234567890,
            "messaging": [{
                "sender": {"id": "USER_IGSID"},
                "recipient": {"id": "PAGE_IGSID"},
                "timestamp": 1234567890,
                "message": {
                    "mid": "MESSAGE_ID",
                    "text": "Hello"
                }
            }]
        }]
    }

    Returns:
        Dict: Status response for Instagram API

    Raises:
        HTTPException: For invalid requests or JSON parsing errors
    """
    try:
        # Parse incoming webhook data
        body = await request.body()

        if not body:
            print("⚠️ Empty Instagram DM webhook body")
            raise HTTPException(status_code=400, detail="Empty request body")

        try:
            data = json.loads(body.decode('utf-8'))
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON in Instagram DM webhook: {e}")
            raise HTTPException(status_code=400, detail="Invalid JSON format")

        # Validate webhook structure
        if data.get("object") != "instagram":
            print(f"⚠️ Invalid object type: {data.get('object')}")
            raise HTTPException(status_code=400, detail="Invalid object type")

        entries = data.get("entry", [])
        if not entries:
            print("⚠️ No entries in Instagram DM webhook")
            return {"status": "ok", "message": "No entries to process"}

        print(f"📸 Instagram DM webhook received: {len(entries)} entries")

        # Process each entry in background
        for entry in entries:
            background_tasks.add_task(process_instagram_dm_entry, entry)

        # Return immediate success response
        return {"status": "ok", "entries_processed": len(entries)}

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        print(f"❌ Unexpected Instagram DM webhook error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/webhook/info")
async def instagram_dm_webhook_info():
    """
    Get Instagram DM webhook information for debugging.

    Returns:
        Dict: Webhook and channel information
    """
    try:
        channel = get_instagram_dm_channel()

        # Get memory stats
        memory_stats = {}
        if channel.memory:
            memory_stats = await channel.memory.get_memory_size("")

        return {
            "status": "active",
            "channel_type": "instagram_dm",
            "architecture": "channel_based",
            "memory_stats": memory_stats,
            "components": {
                "handler": True if channel else False,
                "memory": True if channel and channel.memory else False,
                "client": True if channel and channel.client else False
            }
        }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "channel_type": "instagram_dm",
            "architecture": "channel_based"
        }


@router.post("/webhook/test")
async def test_instagram_dm_webhook():
    """
    Test Instagram DM webhook with a mock message.

    Returns:
        Dict: Test results
    """
    try:
        # Create mock Instagram DM event
        mock_event = {
            "sender": {"id": "test_user_123"},
            "recipient": {"id": "test_page_456"},
            "timestamp": 1234567890,
            "message": {
                "mid": "test_message_id",
                "text": "Hello, this is a test DM!"
            }
        }

        # Process the mock event
        channel = get_instagram_dm_channel()
        result = await channel.process_message(mock_event)

        return {
            "status": "success",
            "test_result": result,
            "mock_event": mock_event
        }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


@router.get("/health")
async def instagram_dm_health_check():
    """
    Health check endpoint for Instagram DM channel.

    Returns:
        Dict: Health status information
    """
    try:
        channel = get_instagram_dm_channel()

        health_status = {
            "status": "healthy",
            "channel": "instagram_dm",
            "architecture": "channel_based",
            "components": {
                "handler": True if channel else False,
                "memory": True if channel and channel.memory else False,
                "client": True if channel and channel.client else False
            }
        }

        return health_status

    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "channel": "instagram_dm",
            "architecture": "channel_based"
        }
