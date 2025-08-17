"""
Telegram webhook handler using the new channel architecture.

This module provides the webhook endpoint for Telegram updates, utilizing the new
TelegramChannel implementation for clean separation of concerns and standardized
message processing.
"""

import json
from fastapi import APIRouter, Request, BackgroundTasks, HTTPException
from typing import Dict, Any

from .handler import get_telegram_channel

router = APIRouter(prefix="/telegram", tags=["telegram"])


async def process_telegram_update(update: Dict[str, Any]) -> None:
    """
    Process Telegram update through the new channel architecture.
    
    This function handles all Telegram updates by delegating to the TelegramChannel
    which provides standardized processing, memory management, and error handling.
    
    Args:
        update: Raw Telegram webhook update object
    """
    try:
        # Get the Telegram channel instance (singleton)
        channel = get_telegram_channel()
        
        # Process through the channel with metrics tracking
        result = await channel.process_with_metrics(update)
        
        print(f"📱 Telegram update processed: {result}")
        
    except Exception as e:
        print(f"❌ Error processing Telegram update: {e}")
        # Don't re-raise - webhook should always return 200 to Telegram


@router.post("/webhook")
async def telegram_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Telegram webhook endpoint with simplified processing.
    
    This endpoint receives Telegram updates and processes them through the new
    channel architecture. It provides immediate response to Telegram while
    processing the message in the background.
    
    Returns:
        Dict: Status response for Telegram API
        
    Raises:
        HTTPException: For invalid requests or JSON parsing errors
    """
    try:
        # Parse incoming update
        body = await request.body()
        
        if not body:
            print("⚠️ Empty Telegram webhook body")
            raise HTTPException(status_code=400, detail="Empty request body")
        
        try:
            update = json.loads(body.decode('utf-8'))
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON in Telegram webhook: {e}")
            raise HTTPException(status_code=400, detail="Invalid JSON format")
        
        # Validate update structure
        if not isinstance(update, dict):
            print("⚠️ Telegram update is not a dictionary")
            raise HTTPException(status_code=400, detail="Invalid update format")
        
        update_id = update.get('update_id', 'unknown')
        print(f"📱 Telegram webhook received: update_id={update_id}")
        
        # Process update in background (non-blocking response)
        background_tasks.add_task(process_telegram_update, update)
        
        # Return immediate success response to Telegram
        return {"status": "ok", "update_id": update_id}
        
    except HTTPException:
        # Re-raise HTTP exceptions (400 errors)
        raise
    except Exception as e:
        print(f"❌ Unexpected Telegram webhook error: {e}")
        # Return 500 for unexpected errors
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/webhook/info")
async def webhook_info():
    """
    Get webhook information for debugging and monitoring.
    
    This endpoint provides information about the current webhook configuration
    and the Telegram channel status.
    
    Returns:
        Dict: Webhook and channel information
    """
    try:
        channel = get_telegram_channel()
        
        # Get webhook info from Telegram API
        webhook_info = {}
        if channel.client:
            webhook_info = await channel.client.get_webhook_info()
        
        # Get memory stats for monitoring
        memory_stats = {}
        if channel.memory:
            # Get stats for a sample session (empty means no specific session)
            memory_stats = await channel.memory.get_memory_size("")
        
        return {
            "status": "active",
            "webhook_info": webhook_info,
            "memory_stats": memory_stats,
            "channel_type": "telegram",
            "architecture": "new_channel_based"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "architecture": "new_channel_based"
        }


@router.post("/webhook/test")
async def test_webhook():
    """
    Test webhook functionality with a mock update.
    
    This endpoint allows testing the webhook processing pipeline without
    needing actual Telegram updates. Useful for development and debugging.
    
    Returns:
        Dict: Test results
    """
    try:
        # Create a mock Telegram update for testing
        mock_update = {
            "update_id": 999999,
            "message": {
                "message_id": 999,
                "from": {
                    "id": 12345,
                    "username": "test_user",
                    "first_name": "Test",
                    "last_name": "User"
                },
                "chat": {
                    "id": 12345,
                    "type": "private"
                },
                "text": "Hello, this is a test message!",
                "date": 1234567890
            }
        }
        
        # Process the mock update
        channel = get_telegram_channel()
        result = await channel.process_message(mock_update)
        
        return {
            "status": "success",
            "test_result": result,
            "mock_update": mock_update
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


@router.delete("/webhook")
async def delete_webhook():
    """
    Delete the current Telegram webhook.
    
    This endpoint allows removing the webhook configuration from Telegram.
    Useful for debugging or switching webhook URLs.
    
    Returns:
        Dict: Deletion result
    """
    try:
        channel = get_telegram_channel()
        
        if not channel.client:
            return {"status": "error", "message": "No Telegram client available"}
        
        success = await channel.client.delete_webhook()
        
        if success:
            return {"status": "success", "message": "Webhook deleted successfully"}
        else:
            return {"status": "error", "message": "Failed to delete webhook"}
            
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.get("/health")
async def telegram_health_check():
    """
    Health check endpoint for Telegram channel.
    
    This endpoint provides health status information for monitoring
    and load balancer integration.
    
    Returns:
        Dict: Health status information
    """
    try:
        channel = get_telegram_channel()
        
        # Test basic channel functionality
        health_status = {
            "status": "healthy",
            "channel": "telegram",
            "architecture": "new_channel_based",
            "components": {
                "handler": True if channel else False,
                "memory": True if channel and channel.memory else False,
                "client": True if channel and channel.client else False
            }
        }
        
        # Test client connection if available
        if channel and channel.client:
            try:
                bot_info = await channel.client.get_me()
                health_status["bot_info"] = {
                    "username": bot_info.get("username"),
                    "id": bot_info.get("id")
                }
            except Exception as e:
                health_status["components"]["client"] = False
                health_status["client_error"] = str(e)
        
        return health_status
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "channel": "telegram",
            "architecture": "new_channel_based"
        }