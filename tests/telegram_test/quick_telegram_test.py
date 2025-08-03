#!/usr/bin/env python3
"""
Quick Telegram Bot Test Script
Input ngrok URL → Setup webhook → Test messaging directly
"""

import asyncio
import sys
from pathlib import Path

# Add project root to Python path
sys.path.append(str(Path(__file__).parent.parent.parent))

from app.services.telegram_api import get_telegram_api
from app.config import settings


async def main():
    print("🚀 Quick Telegram Bot Setup & Test")
    print("=" * 40)
    
    # Check token
    if not settings.TELEGRAM_BOT_TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN not found in .env")
        return
    
    print(f"✅ Bot token loaded: ...{settings.TELEGRAM_BOT_TOKEN[-10:]}")
    
    # Input ngrok URL
    print("\n📡 Setup Webhook:")
    ngrok_url = input("Enter ngrok URL (e.g., https://abc123.ngrok.io): ").strip()
    if not ngrok_url:
        print("❌ ngrok URL required")
        return
    
    # Format webhook URL
    if not ngrok_url.startswith("http"):
        ngrok_url = f"https://{ngrok_url}"
    
    webhook_url = f"{ngrok_url}/api/telegram/webhook"
    print(f"🔗 Webhook URL: {webhook_url}")
    
    try:
        # Setup webhook
        print("\n⚙️ Setting up webhook...")
        api = await get_telegram_api()
        result = await api.set_webhook(webhook_url)
        
        if result.get("ok"):
            print("✅ Webhook setup successful!")
        else:
            print(f"❌ Webhook setup failed: {result}")
            return
            
    except Exception as e:
        print(f"❌ Error setting webhook: {e}")
        return
    
    # Get chat ID for testing
    print("\n💬 Test Messaging:")
    print("1. Open Telegram and find your bot")
    print("2. Send any message to your bot first (to get chat ID)")
    print("3. Then come back here")
    
    chat_id = input("\nEnter chat ID to send test message: ").strip()
    if not chat_id:
        print("⚠️ Skipping message test")
        print("\n✅ Webhook is ready! Send messages to your bot to test.")
        return
    
    try:
        chat_id = int(chat_id)
        
        # Send test message
        print(f"\n📤 Sending test message to chat {chat_id}...")
        test_message = "🎉 Webhook setup berhasil! Bot siap menerima pesan.\n\nSekarang coba kirim pesan lain untuk test AI response!"
        
        result = await api.send_message(chat_id, test_message)
        
        if result.get("ok"):
            print("✅ Test message sent successfully!")
            print("\n🤖 Setup complete! Your bot is ready.")
            print("💡 Try sending messages to your bot - it will respond using AI!")
        else:
            print(f"❌ Failed to send message: {result}")
            
    except ValueError:
        print("❌ Invalid chat ID format")
    except Exception as e:
        print(f"❌ Error sending message: {e}")
    
    print("\n" + "=" * 40)
    print("🎯 Quick Setup Summary:")
    print(f"   Webhook: {webhook_url}")
    print(f"   Bot: @{settings.TELEGRAM_BOT_USERNAME}")
    print(f"   Status: Ready for testing")
    print("\n💡 Next steps:")
    print("   1. Make sure FastAPI is running (uvicorn app.main:app --reload)")
    print("   2. Send messages to your bot")
    print("   3. Check logs for AI responses")


if __name__ == "__main__":
    asyncio.run(main())