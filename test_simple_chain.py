#!/usr/bin/env python3
"""
Simple test untuk conditional chain implementation.
"""

import sys
import asyncio
from pathlib import Path

# Add project root
sys.path.insert(0, str(Path(__file__).parent))

from app.chains import create_instagram_chain, process_with_chain


async def test_basic_chain():
    """Test basic conditional chain functionality"""
    print("🧪 Testing Simple Conditional Chain")
    print("=" * 40)
    
    # Test 1: Create chain
    try:
        chain = create_instagram_chain()
        print("✅ Chain created successfully")
        
        stats = chain.get_stats()
        print(f"✅ Chain stats: {stats}")
        
    except Exception as e:
        print(f"❌ Chain creation failed: {e}")
        return
    
    # Test 2: Test route decision
    test_cases = [
        {
            "comment": "Bagaimana cara return barang?",
            "expected": "docs route",
            "description": "Return policy query"
        },
        {
            "comment": "Halo, apa kabar?",
            "expected": "direct route", 
            "description": "Simple greeting"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n[TEST {i}] {test_case['description']}")
        print(f"Query: '{test_case['comment']}'")
        
        try:
            result = chain.run({
                "comment": test_case["comment"],
                "post_id": f"test_post_{i}",
                "comment_id": f"test_comment_{i}",
                "username": "test_user"
            })
            
            reply = result["reply"]
            route_used = result["route_used"]
            processing_info = result["processing_info"]
            
            print(f"✅ Route: {route_used}")
            print(f"✅ Context used: {processing_info['context_used']}")
            print(f"✅ Reply length: {len(reply)} chars")
            print(f"Preview: {reply[:100]}...")
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
    
    # Test 3: Async wrapper
    print(f"\n[TEST 3] Async wrapper test")
    try:
        reply = await process_with_chain(
            comment="Customer service jam berapa buka?",
            post_id="async_test",
            comment_id="async_1", 
            username="async_user"
        )
        
        print(f"✅ Async wrapper works: {len(reply)} chars")
        print(f"Preview: {reply[:100]}...")
        
    except Exception as e:
        print(f"❌ Async test failed: {e}")
    
    print("\n🎉 Simple chain testing completed!")


if __name__ == "__main__":
    asyncio.run(test_basic_chain())