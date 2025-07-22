"""
Example monitoring callback untuk InstagramConditionalChain.
Demo cara menggunakan callback system untuk performance tracking.
"""

from app.chains.conditional_chain import get_chain
import asyncio


def performance_callback(step_name: str, duration: float) -> None:
    """Simple performance monitoring callback"""
    print(f"🔍 {step_name.upper()}: {duration:.3f}s")
    
    # Alert jika terlalu lambat
    if duration > 2.0:
        print(f"⚠️  WARNING: {step_name} took {duration:.3f}s (>2s)")


def detailed_callback(step_name: str, duration: float) -> None:
    """Detailed monitoring dengan berbagai threshold"""
    thresholds = {
        "router": 0.5,
        "rag": 1.0, 
        "reply": 2.0,
        "memory": 0.1,
        "total": 3.0
    }
    
    threshold = thresholds.get(step_name, 1.0)
    status = "🟢" if duration < threshold else "🟡" if duration < threshold * 2 else "🔴"
    
    print(f"{status} {step_name}: {duration:.3f}s (threshold: {threshold}s)")


async def demo_monitoring():
    """Demo monitoring callbacks"""
    print("=== Chain Monitoring Demo ===\n")
    
    # Get chain dengan callbacks
    callbacks = [performance_callback, detailed_callback]
    chain = get_chain(callbacks=callbacks)
    
    print("Chain stats:", chain.get_stats())
    print()
    
    # Test dengan different scenarios
    test_cases = [
        {
            "comment": "Hello!",
            "post_id": "demo_post_1", 
            "comment_id": "demo_comment_1",
            "username": "demo_user",
            "scenario": "Simple greeting (direct route)"
        },
        {
            "comment": "How do I use the API documentation?",
            "post_id": "demo_post_2",
            "comment_id": "demo_comment_2", 
            "username": "demo_user",
            "scenario": "FAQ query (docs route)"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- Test Case {i}: {test_case['scenario']} ---")
        
        try:
            # Simulate chain call dengan mock
            with patch_chain_functions():
                result = chain.run({
                    "comment": test_case["comment"],
                    "post_id": test_case["post_id"],
                    "comment_id": test_case["comment_id"],
                    "username": test_case["username"]
                })
                
                print(f"Reply: {result['reply']}")
                print(f"Route: {result['route_used']}")
                timing = result['processing_info']['timing']
                print(f"Total time: {timing['total_time']}s")
                
        except Exception as e:
            print(f"Error: {e}")


def patch_chain_functions():
    """Mock chain functions untuk demo"""
    from unittest.mock import patch
    import time
    import random
    
    def mock_supervisor_route(comment):
        time.sleep(random.uniform(0.1, 0.3))  # Simulate router time
        if "hello" in comment.lower():
            return "direct"
        elif "api" in comment.lower() or "documentation" in comment.lower():
            return "docs"
        else:
            return "web"
    
    def mock_retrieve_context(comment, mode):
        time.sleep(random.uniform(0.5, 1.2))  # Simulate RAG time
        return f"Context for {mode} mode"
    
    def mock_generate_reply(comment, post_id, comment_id, username, context=""):
        time.sleep(random.uniform(1.0, 2.5))  # Simulate reply generation
        return f"Generated reply for: {comment[:30]}..."
    
    return patch.multiple(
        'app.chains.conditional_chain',
        supervisor_route=mock_supervisor_route,
        retrieve_context=mock_retrieve_context,
        generate_reply=mock_generate_reply
    )


if __name__ == "__main__":
    # Jalankan demo
    from unittest.mock import patch
    asyncio.run(demo_monitoring())