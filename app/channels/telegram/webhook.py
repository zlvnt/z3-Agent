"""
Telegram webhook endpoints.

Handles incoming Telegram updates and provides webhook management endpoints.
"""

from fastapi import APIRouter, BackgroundTasks, Request
from typing import Dict, Any

from app.config import settings

router = APIRouter(prefix="/telegram/webhook")


async def process_telegram_update(update: Dict[str, Any]):
    """Process a Telegram update in background."""
    try:
        from app.channels.telegram.handler import get_telegram_channel

        channel = get_telegram_channel()
        result = await channel.process_message(update)
        print(f"Telegram update processed: {result}")
    except Exception as e:
        print(f"Error processing Telegram update: {e}")


@router.post("")
async def telegram_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Main Telegram webhook endpoint.

    Receives Telegram updates and processes them in background tasks
    for non-blocking response.
    """
    try:
        update = await request.json()
        update_id = update.get("update_id", "unknown")

        # Process in background for fast webhook response
        background_tasks.add_task(process_telegram_update, update)

        return {"status": "ok", "update_id": str(update_id)}
    except Exception as e:
        print(f"Webhook error: {e}")
        return {"status": "error", "message": str(e)}


@router.get("")
async def telegram_webhook_verify():
    """Webhook verification endpoint."""
    return {"status": "ok", "message": "Telegram webhook is active"}


@router.get("/info")
async def telegram_webhook_info():
    """Get webhook configuration info."""
    try:
        from app.channels.telegram.client import get_telegram_client
        from app.channels.telegram.memory import get_telegram_memory

        client = get_telegram_client()
        memory = get_telegram_memory()

        webhook_info = await client.get_webhook_info()

        return {
            "status": "ok",
            "webhook_info": webhook_info,
            "memory_stats": {
                "db_type": memory.db_type,
                "connection": "configured",
            },
            "channel_type": "telegram",
            "architecture": "unified_processor + quality_gate",
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.post("/test")
async def telegram_webhook_test():
    """Test webhook processing with mock data."""
    mock_update = {
        "update_id": 999999999,
        "message": {
            "message_id": 1,
            "from": {
                "id": 12345,
                "is_bot": False,
                "first_name": "Test",
                "username": "test_user",
            },
            "chat": {"id": 12345, "type": "private"},
            "date": 1234567890,
            "text": "Hello, this is a test message!",
        },
    }

    try:
        from app.channels.telegram.handler import get_telegram_channel

        channel = get_telegram_channel()
        result = await channel.process_message(mock_update)

        return {
            "status": "ok",
            "test_result": result,
            "mock_update": mock_update,
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.delete("")
async def telegram_webhook_delete():
    """Delete current webhook."""
    try:
        from app.channels.telegram.client import get_telegram_client

        client = get_telegram_client()
        success = await client.delete_webhook()

        if success:
            return {"status": "ok", "message": "Webhook deleted"}
        else:
            return {"status": "error", "message": "Failed to delete webhook"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.get("/health", tags=["telegram"])
async def telegram_health():
    """Telegram channel health check."""
    result = {
        "status": "ok",
        "channel": "telegram",
        "architecture": "unified_processor + quality_gate",
        "components": {
            "handler": "available",
            "memory": "unknown",
            "client": "unknown",
        },
    }

    try:
        from app.channels.telegram.client import get_telegram_client

        client = get_telegram_client()
        bot_info = await client.get_me()
        if "error" not in bot_info:
            result["bot_info"] = bot_info
            result["components"]["client"] = "connected"
        else:
            result["components"]["client"] = "error"
            result["client_error"] = bot_info.get("error")
    except Exception as e:
        result["components"]["client"] = "error"
        result["client_error"] = str(e)

    try:
        from app.channels.telegram.memory import get_telegram_memory

        memory = get_telegram_memory()
        result["components"]["memory"] = f"{memory.db_type} connected"
    except Exception as e:
        result["components"]["memory"] = f"error: {e}"

    return result
