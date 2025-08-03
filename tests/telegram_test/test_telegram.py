#!/usr/bin/env python3
"""
Interactive Telegram Bot Testing Terminal
Mirrors test.py structure for testing Telegram functionality.
"""

import asyncio
from pathlib import Path

# Add project root to Python path
import sys
sys.path.append(str(Path(__file__).parent.parent))

from app.services.telegram_api import get_telegram_api
from app.chains.conditional_chain import process_with_chain
from app.config import settings


class TelegramTester:
    """Interactive Telegram testing interface."""
    
    def __init__(self):
        self.api = None
        self.test_chat_id = None
    
    async def initialize(self):
        """Initialize Telegram API connection."""
        try:
            self.api = await get_telegram_api()
            print("✅ Telegram API initialized")
            
            print("🤖 Bot: Telegram API initialized")
            print("🔗 Webhook: Use manual setup if needed")
            
        except Exception as e:
            print(f"❌ Failed to initialize Telegram API: {e}")
            return False
        return True
    
    async def test_send_message(self):
        """Test sending message to Telegram chat."""
        if not self.test_chat_id:
            self.test_chat_id = input("Enter test chat ID (your chat with bot): ").strip()
            if not self.test_chat_id:
                print("❌ Chat ID required")
                return
        
        try:
            chat_id = int(self.test_chat_id)
            test_message = "🧪 Test message from z3_agent"
            
            result = await self.api.send_message(chat_id, test_message)
            print(f"✅ Message sent: {result.get('result', {}).get('message_id', 'Unknown ID')}")
            
        except ValueError:
            print("❌ Invalid chat ID format")
        except Exception as e:
            print(f"❌ Failed to send message: {e}")
    
    async def test_chain_processing(self):
        """Test full chain processing with mock Telegram message."""
        if not self.test_chat_id:
            self.test_chat_id = input("Enter test chat ID: ").strip()
        
        test_comment = input("Enter test message: ").strip()
        if not test_comment:
            test_comment = "Halo bot!"
        
        try:
            chat_id = int(self.test_chat_id)
            
            print(f"\n🔄 Processing message: '{test_comment}'")
            
            # Use chain system
            reply = await process_with_chain(
                comment=test_comment,
                post_id=f"tg_chat_{chat_id}",
                comment_id=f"tg_msg_test_{asyncio.get_event_loop().time()}",
                username="test_user",
                enable_monitoring=True
            )
            
            print(f"🤖 Generated reply: {reply}")
            
            # Ask if want to send to chat
            send = input("Send reply to chat? (y/n): ").strip().lower()
            if send == 'y':
                await self.api.send_message(chat_id, reply)
                print("✅ Reply sent to chat")
            
        except ValueError:
            print("❌ Invalid chat ID format")
        except Exception as e:
            print(f"❌ Chain processing failed: {e}")
    
    async def test_webhook_setup(self):
        """Test webhook setup."""
        webhook_url = input("Enter webhook URL (https://yourdomain.com/api/telegram/webhook): ").strip()
        if not webhook_url:
            print("❌ Webhook URL required")
            return
        
        try:
            result = await self.api.set_webhook(webhook_url)
            if result.get("ok"):
                print("✅ Webhook set successfully")
            else:
                print(f"❌ Webhook setup failed: {result}")
        except Exception as e:
            print(f"❌ Webhook setup error: {e}")
    
    def show_menu(self):
        """Show interactive menu."""
        print("\n" + "="*50)
        print("🤖 TELEGRAM BOT TESTING TERMINAL")
        print("="*50)
        print("1. Test send message")
        print("2. Test chain processing")
        print("3. Test webhook setup")
        print("0. Exit")
        print("-"*50)
    
    async def run(self):
        """Main testing loop."""
        print("🚀 Starting Telegram Bot Tester...")
        
        if not await self.initialize():
            return
        
        while True:
            self.show_menu()
            choice = input("Choose option: ").strip()
            
            if choice == "0":
                print("👋 Goodbye!")
                break
            elif choice == "1":
                await self.test_send_message()
            elif choice == "2":
                await self.test_chain_processing()
            elif choice == "3":
                await self.test_webhook_setup()
            else:
                print("❌ Invalid option")
            
            input("\nPress Enter to continue...")


async def main():
    """Main entry point."""
    # Check if Telegram token is configured
    if not settings.TELEGRAM_BOT_TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN not configured in .env")
        print("Add: TELEGRAM_BOT_TOKEN=your_bot_token")
        return
    
    tester = TelegramTester()
    await tester.run()


if __name__ == "__main__":
    asyncio.run(main())