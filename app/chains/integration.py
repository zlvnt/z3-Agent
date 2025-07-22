"""
Integration layer untuk gradual migration dari legacy ke chain system.

Provides:
- Drop-in replacement functions
- Migration path utilities
- Performance comparison tools
- Testing framework integration
"""

from __future__ import annotations
from typing import Any, Optional, Dict
import time
import os
from functools import wraps

from app.chains.orchestrator import process_instagram_comment as chain_process
from app.chains.models import ChainInput, ChainOutput


# Migration control - environment variable based
USE_CHAIN_SYSTEM = os.getenv("USE_CHAIN_SYSTEM", "true").lower() == "true"
CHAIN_FALLBACK_ENABLED = os.getenv("CHAIN_FALLBACK_ENABLED", "true").lower() == "true"


async def handle_instagram_comment(
    comment: str,
    post_id: str,
    comment_id: str,
    username: str,
    **kwargs: Any,
) -> str:
    """
    Drop-in replacement untuk legacy router.handle function.
    
    Provides gradual migration path:
    - USE_CHAIN_SYSTEM=true → Use new chain system
    - USE_CHAIN_SYSTEM=false → Use legacy system
    - CHAIN_FALLBACK_ENABLED=true → Auto fallback jika chain fails
    """
    
    if USE_CHAIN_SYSTEM:
        try:
            # Use new chain system
            return await chain_process(
                comment=comment,
                post_id=post_id,
                comment_id=comment_id,
                username=username,
                **kwargs
            )
        except Exception as e:
            print(f"ERROR: Chain system failed: {e}")
            
            if CHAIN_FALLBACK_ENABLED:
                print("INFO: Falling back to legacy system")
                return await _legacy_handle(comment, post_id, comment_id, username, **kwargs)
            else:
                raise
    else:
        # Use legacy system
        return await _legacy_handle(comment, post_id, comment_id, username, **kwargs)


async def _legacy_handle(
    comment: str,
    post_id: str,
    comment_id: str,
    username: str,
    **kwargs: Any,
) -> str:
    """Execute legacy handler with async wrapper"""
    import asyncio
    from app.agents.router import handle as legacy_handle
    
    # Run legacy synchronous code dalam thread pool
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        legacy_handle,
        comment,
        post_id,
        comment_id,
        username,
        **{k: v for k, v in kwargs.items()}
    )


def performance_comparison_decorator(func):
    """
    Decorator untuk comparing performance between systems.
    Enable dengan ENABLE_PERFORMANCE_COMPARISON=true
    """
    
    @wraps(func)
    async def wrapper(*args, **kwargs):
        if not os.getenv("ENABLE_PERFORMANCE_COMPARISON", "false").lower() == "true":
            return await func(*args, **kwargs)
        
        print("INFO: Running performance comparison...")
        
        # Extract parameters
        comment = args[0] if args else kwargs.get("comment", "")
        post_id = args[1] if len(args) > 1 else kwargs.get("post_id", "")
        comment_id = args[2] if len(args) > 2 else kwargs.get("comment_id", "")
        username = args[3] if len(args) > 3 else kwargs.get("username", "")
        
        # Run both systems
        results = {}
        
        # Test chain system
        try:
            start_time = time.time()
            chain_result = await chain_process(comment, post_id, comment_id, username)
            chain_time = time.time() - start_time
            
            results["chain"] = {
                "result": chain_result,
                "time": chain_time,
                "success": True,
                "length": len(chain_result)
            }
        except Exception as e:
            results["chain"] = {
                "result": None,
                "time": None,
                "success": False,
                "error": str(e)
            }
        
        # Test legacy system
        try:
            start_time = time.time()
            legacy_result = await _legacy_handle(comment, post_id, comment_id, username)
            legacy_time = time.time() - start_time
            
            results["legacy"] = {
                "result": legacy_result,
                "time": legacy_time,
                "success": True,
                "length": len(legacy_result)
            }
        except Exception as e:
            results["legacy"] = {
                "result": None,
                "time": None,
                "success": False,
                "error": str(e)
            }
        
        # Log comparison
        print(f"PERF COMPARISON:")
        print(f"  Chain: {results['chain']['time']:.3f}s, Success: {results['chain']['success']}")
        print(f"  Legacy: {results['legacy']['time']:.3f}s, Success: {results['legacy']['success']}")
        
        # Return preferred result (chain if successful, otherwise legacy)
        if results["chain"]["success"]:
            return results["chain"]["result"]
        elif results["legacy"]["success"]:
            return results["legacy"]["result"]
        else:
            raise Exception("Both systems failed")
    
    return wrapper


# Apply performance comparison if enabled
handle_instagram_comment = performance_comparison_decorator(handle_instagram_comment)


class MigrationTester:
    """
    Testing utilities untuk migration validation.
    """
    
    @staticmethod
    async def test_basic_functionality():
        """Test basic chain functionality"""
        test_cases = [
            {
                "comment": "Bagaimana cara return barang?",
                "expected_route": "docs",
                "description": "Return policy query"
            },
            {
                "comment": "Halo, apa kabar?", 
                "expected_route": "direct",
                "description": "Simple greeting"
            },
            {
                "comment": "Customer service jam berapa buka?",
                "expected_route": "docs",
                "description": "Contact info query"
            }
        ]
        
        results = []
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n[TEST {i}] {test_case['description']}")
            print(f"Query: '{test_case['comment']}'")
            
            try:
                result = await handle_instagram_comment(
                    comment=test_case["comment"],
                    post_id="test_post",
                    comment_id=f"test_comment_{i}",
                    username="test_user"
                )
                
                test_result = {
                    "test_id": i,
                    "success": True,
                    "result": result,
                    "length": len(result),
                    "description": test_case["description"]
                }
                
                print(f"✅ Success: {len(result)} chars")
                print(f"Preview: {result[:100]}...")
                
            except Exception as e:
                test_result = {
                    "test_id": i,
                    "success": False,
                    "error": str(e),
                    "description": test_case["description"]
                }
                
                print(f"❌ Failed: {e}")
            
            results.append(test_result)
        
        # Summary
        successful_tests = sum(1 for r in results if r["success"])
        print(f"\n📊 Test Summary: {successful_tests}/{len(test_cases)} passed")
        
        return results
    
    @staticmethod
    async def test_memory_persistence():
        """Test memory persistence across requests"""
        user_id = "test_user_memory"
        post_id = "memory_test_post"
        
        print("\n🧠 Testing memory persistence...")
        
        # First interaction
        result1 = await handle_instagram_comment(
            comment="Halo, nama saya John",
            post_id=post_id,
            comment_id="memory_1",
            username=user_id
        )
        print(f"Interaction 1: {result1[:50]}...")
        
        # Second interaction (should remember name)
        result2 = await handle_instagram_comment(
            comment="Bagaimana cara return barang?",
            post_id=post_id,
            comment_id="memory_2", 
            username=user_id
        )
        print(f"Interaction 2: {result2[:50]}...")
        
        # Check if name is mentioned dalam context
        memory_working = "john" in result2.lower()
        print(f"Memory test: {'✅ PASSED' if memory_working else '❌ FAILED'}")
        
        return {
            "memory_working": memory_working,
            "interaction1": result1,
            "interaction2": result2
        }


# Export for webhook integration
__all__ = [
    "handle_instagram_comment",
    "MigrationTester",
    "USE_CHAIN_SYSTEM", 
    "CHAIN_FALLBACK_ENABLED"
]