from fastapi import APIRouter, Request, BackgroundTasks, HTTPException
from typing import Dict, Any
import json

from app.services.telegram_api import send_telegram_message
from app.chains.conditional_chain import process_with_chain
from app.config import settings

router = APIRouter(prefix="/telegram", tags=["telegram"])


async def process_telegram_message(update: Dict[str, Any]) -> None:
    try:
        # Extract message data
        message = update.get("message", {})
        if not message:
            print("⚠️ No message in Telegram update")
            return
        
        # Extract required fields
        chat_id = message.get("chat", {}).get("id")
        message_id = message.get("message_id")
        text = message.get("text", "").strip()
        user = message.get("from", {})
        username = user.get("username") or user.get("first_name", "unknown")
        
        if not all([chat_id, message_id, text]):
            print("⚠️ Missing required fields in Telegram message")
            return
        
        # Self-loop prevention
        bot_username = getattr(settings, 'TELEGRAM_BOT_USERNAME', 'z3_agent_bot')
        if username == bot_username:
            print(f"🔄 Skipping message from bot itself: {username}")
            return
        
        print(f"📨 Processing Telegram message: {text[:50]}... from @{username}")
        
        # Use existing chain system with channel context
        # Format IDs as strings for consistency with Instagram
        reply = await process_with_chain(
            comment=text,
            post_id=f"tg_chat_{chat_id}",  # Channel-aware post ID
            comment_id=f"tg_msg_{message_id}",  # Channel-aware comment ID  
            username=username,
            enable_monitoring=True
        )
        
        # Send reply back to Telegram
        if reply:
            success = await send_telegram_message(
                chat_id=chat_id,
                text=reply,
                reply_to_message_id=message_id
            )
            
            if success:
                print(f"✅ Telegram reply sent to @{username}")
            else:
                print(f"❌ Failed to send Telegram reply to @{username}")
        else:
            print("⚠️ No reply generated for Telegram message")
            
    except Exception as e:
        print(f"❌ Error processing Telegram message: {e}")


@router.post("/webhook")
async def telegram_webhook(request: Request, background_tasks: BackgroundTasks):
    try:
        # Parse incoming update
        body = await request.body()
        update = json.loads(body.decode('utf-8'))
        
        print(f"📱 Telegram webhook received: {update.get('update_id', 'unknown')}")
        
        # Validate update structure
        if not isinstance(update, dict):
            raise HTTPException(status_code=400, detail="Invalid update format")
        
        # Process message in background (non-blocking)
        background_tasks.add_task(process_telegram_message, update)
        
        # Return immediate response to Telegram
        return {"status": "ok"}
        
    except json.JSONDecodeError:
        print("❌ Invalid JSON in Telegram webhook")
        raise HTTPException(status_code=400, detail="Invalid JSON")
    except Exception as e:
        print(f"❌ Telegram webhook error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


