#!/usr/bin/env python3
"""
Simple Telegram Webhook Setup
Input ngrok URL → Setup webhook → Ready for testing
"""

import asyncio
import sys
from pathlib import Path

# Add project root to Python path
sys.path.append(str(Path(__file__).parent))

from app.services.telegram_api import get_telegram_api
from app.config import settings


async def main():
    print("🚀 Telegram Bot Setup")
    print("=" * 30)
    
    # Check token
    if not settings.TELEGRAM_BOT_TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN not found in .env")
        return
    
    print(f"✅ Bot: @{settings.TELEGRAM_BOT_USERNAME}")
    
    # Input ngrok URL
    ngrok_url = input("\nEnter ngrok URL: ").strip()
    if not ngrok_url:
        print("❌ ngrok URL required")
        return
    
    # Format webhook URL
    if not ngrok_url.startswith("http"):
        ngrok_url = f"https://{ngrok_url}"
    
    webhook_url = f"{ngrok_url}/api/telegram/webhook"
    
    try:
        # Setup webhook
        print("⚙️ Setting up webhook...")
        api = await get_telegram_api()
        result = await api.set_webhook(webhook_url)
        
        if result.get("ok"):
            print("✅ Webhook setup complete!")
            print(f"🔗 Bot ready at: @{settings.TELEGRAM_BOT_USERNAME}")
            print("\n💡 Next steps:")
            print("1. Make sure FastAPI is running: uvicorn app.main:app --reload")
            print("2. Open Telegram → Search @z3Agent_bot → Send message")
            print("3. Bot will reply automatically!")
        else:
            print(f"❌ Webhook setup failed: {result}")
            
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())