#!/usr/bin/env python3
"""
Test script untuk validating new chain system.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.chains.integration import MigrationTester, handle_instagram_comment
from app.chains import get_orchestrator


async def main():
    """Test new chain system functionality"""
    print("🧪 Testing Instagram AI Agent Chain System")
    print("=" * 50)
    
    # Test 1: Basic functionality
    print("\n1️⃣ Testing basic functionality...")
    try:
        tester = MigrationTester()
        basic_results = await tester.test_basic_functionality()
        
        success_count = sum(1 for r in basic_results if r["success"])
        print(f"✅ Basic functionality: {success_count}/{len(basic_results)} tests passed")
        
    except Exception as e:
        print(f"❌ Basic functionality test failed: {e}")
    
    # Test 2: Single query test
    print("\n2️⃣ Testing single query...")
    try:
        result = await handle_instagram_comment(
            comment="Bagaimana cara return barang yang rusak?",
            post_id="test_single",
            comment_id="single_1",
            username="test_user"
        )
        
        print(f"✅ Single query success: {len(result)} chars")
        print(f"Preview: {result[:150]}...")
        
    except Exception as e:
        print(f"❌ Single query test failed: {e}")
    
    # Test 3: Health check
    print("\n3️⃣ Testing system health...")
    try:
        orchestrator = get_orchestrator()
        health = orchestrator.health_check()
        
        print(f"✅ System health: {health['status']}")
        print(f"Stats: {health.get('stats', {}).get('requests', 0)} requests processed")
        
    except Exception as e:
        print(f"❌ Health check failed: {e}")
    
    # Test 4: Performance stats
    print("\n4️⃣ System statistics...")
    try:
        orchestrator = get_orchestrator()
        stats = orchestrator.get_stats()
        
        print(f"✅ Performance stats:")
        print(f"  Total requests: {stats.get('requests', 0)}")
        print(f"  Success rate: {stats.get('success_rate', 0):.2%}")
        print(f"  Avg processing time: {stats.get('avg_processing_time', 0):.3f}s")
        
    except Exception as e:
        print(f"❌ Stats retrieval failed: {e}")
    
    print("\n🎉 Chain system testing completed!")


if __name__ == "__main__":
    asyncio.run(main())