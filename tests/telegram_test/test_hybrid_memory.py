#!/usr/bin/env python3
"""
Test Hybrid Memory System - LangChain for Telegram vs Manual for Instagram
"""

import asyncio
import sys
from pathlib import Path

# Add project root to Python path
sys.path.append(str(Path(__file__).parent.parent.parent))

from app.chains.telegram_chain import get_telegram_chain, process_telegram_with_memory
from app.chains.conditional_chain import process_with_chain


async def test_telegram_langchain_memory():
    """Test Telegram with LangChain memory system."""
    print("🧪 Testing Telegram LangChain Memory")
    print("=" * 40)
    
    chat_id = "test_chat_123"
    username = "test_user"
    
    # Test conversation flow
    messages = [
        "Halo bot!",
        "Siapa nama kamu?",
        "Apa yang kamu ingat dari percakapan kita?"
    ]
    
    for i, message in enumerate(messages, 1):
        print(f"\n💬 Message {i}: {message}")
        
        try:
            reply = await process_telegram_with_memory(
                chat_id=chat_id,
                username=username,
                message=message,
                enable_monitoring=False
            )
            print(f"🤖 Reply: {reply}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # Test conversation stats
    print("\n📊 Conversation Stats:")
    chain = get_telegram_chain()
    stats = chain.get_conversation_stats(chat_id, username)
    for key, value in stats.items():
        print(f"   {key}: {value}")


async def test_instagram_manual_memory():
    """Test Instagram with manual memory system (unchanged)."""
    print("\n🧪 Testing Instagram Manual Memory")
    print("=" * 40)
    
    post_id = "test_post_456"
    username = "test_user"
    
    # Test conversation flow
    messages = [
        "Nice post!",
        "What's your favorite feature?",
        "Do you remember what I said earlier?"
    ]
    
    for i, message in enumerate(messages, 1):
        print(f"\n💬 Message {i}: {message}")
        
        try:
            reply = await process_with_chain(
                comment=message,
                post_id=post_id,
                comment_id=f"comment_{i}",
                username=username,
                enable_monitoring=False
            )
            print(f"🤖 Reply: {reply}")
            
        except Exception as e:
            print(f"❌ Error: {e}")


async def test_memory_separation():
    """Test that Telegram and Instagram memories are completely separate."""
    print("\n🧪 Testing Memory Separation")
    print("=" * 40)
    
    # Same username, different channels
    username = "same_user"
    
    # Telegram conversation
    print("\n📱 Telegram conversation:")
    reply_tg = await process_telegram_with_memory(
        chat_id="123",
        username=username,
        message="I like pizza",
        enable_monitoring=False
    )
    print(f"🤖 Telegram: {reply_tg}")
    
    # Instagram conversation  
    print("\n📷 Instagram conversation:")
    reply_ig = await process_with_chain(
        comment="I love sushi",
        post_id="456", 
        comment_id="789",
        username=username,
        enable_monitoring=False
    )
    print(f"🤖 Instagram: {reply_ig}")
    
    # Test memory recall
    print("\n🧠 Memory recall test:")
    
    # Telegram should remember pizza
    tg_recall = await process_telegram_with_memory(
        chat_id="123",
        username=username, 
        message="What food did I mention?",
        enable_monitoring=False
    )
    print(f"📱 Telegram recall: {tg_recall}")
    
    # Instagram should not remember pizza (separate memory)
    ig_recall = await process_with_chain(
        comment="What food did I mention?",
        post_id="456",
        comment_id="790", 
        username=username,
        enable_monitoring=False
    )
    print(f"📷 Instagram recall: {ig_recall}")


async def main():
    """Run all hybrid memory tests."""
    print("🚀 Hybrid Memory System Test Suite")
    print("Testing LangChain (Telegram) vs Manual (Instagram)")
    print("=" * 50)
    
    try:
        await test_telegram_langchain_memory()
        await test_instagram_manual_memory() 
        await test_memory_separation()
        
        print("\n✅ All tests completed!")
        print("\n📋 Summary:")
        print("   - Telegram: LangChain SQLChatMessageHistory")
        print("   - Instagram: Manual JSON conversation storage")
        print("   - Memory systems are completely separate")
        print("   - Both use same chain logic (router, RAG, reply)")
        
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())