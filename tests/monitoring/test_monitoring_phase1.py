"""
Test script untuk Phase 1 monitoring implementation.
Tests file logging, metrics collection, dan health endpoints.
"""

import asyncio
import time
import json
import sys
import os
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Test file logging callback
def test_file_logging():
    print("=== Testing File Logging Callback ===")
    
    from app.monitoring.callbacks import file_logger_callback
    
    # Ensure logs directory exists
    Path("logs").mkdir(exist_ok=True)
    
    # Test different scenarios
    test_data = [
        ("memory", 0.05, "normal"),
        ("router", 0.3, "normal"), 
        ("rag", 1.5, "warning"),
        ("reply", 3.0, "critical"),
        ("total", 4.8, "critical")
    ]
    
    for step, duration, expected_severity in test_data:
        file_logger_callback(step, duration, {"test": True})
        print(f"✓ Logged {step}: {duration}s ({expected_severity})")
    
    # Check log file
    log_file = Path("logs/monitoring.jsonl")
    if log_file.exists():
        print(f"✓ Log file created: {log_file}")
        with open(log_file, 'r') as f:
            lines = f.readlines()
            print(f"✓ Log entries: {len(lines)}")
            
            # Show last entry
            if lines:
                last_entry = json.loads(lines[-1])
                print(f"✓ Last entry: {last_entry['step']} - {last_entry['severity']}")
    else:
        print("✗ Log file not created")


def test_basic_metrics():
    print("\n=== Testing Basic Metrics ===")
    
    from app.monitoring.enhanced_metrics import get_metrics_instance, reset_metrics
    
    # Reset for clean test
    reset_metrics()
    metrics = get_metrics_instance()
    
    # Simulate some requests
    test_requests = [
        (1.2, True),   # successful
        (0.8, True),   # successful  
        (2.5, False),  # error
        (1.1, True),   # successful
        (0.9, True)    # successful
    ]
    
    for duration, success in test_requests:
        metrics.record_request(duration, success)
        
        # Record step timings
        metrics.record_step_duration("router", duration * 0.3)
        metrics.record_step_duration("rag", duration * 0.4) 
        metrics.record_step_duration("reply", duration * 0.3)
    
    # Get stats
    stats = metrics.get_stats()
    
    print(f"✓ Total requests: {stats['summary']['total_requests']}")
    print(f"✓ Error rate: {stats['summary']['error_rate']:.2%}")
    print(f"✓ Avg response time: {stats['summary']['avg_response_time']:.3f}s")
    print(f"✓ Health status: {stats['health_status']}")
    
    # Check step performance
    if "router" in stats["step_performance"]:
        router_stats = stats["step_performance"]["router"] 
        print(f"✓ Router avg: {router_stats['avg_duration']:.3f}s")
    
    return stats


async def test_health_endpoints():
    print("\n=== Testing Health Endpoints ===")
    
    # Test direct function calls (simulates FastAPI endpoints)
    from app.monitoring.health import get_health_status, get_readiness_status
    
    # Test health status
    health = get_health_status()
    print(f"✓ Health status: {health['status']}")
    print(f"✓ Uptime: {health['uptime_seconds']:.2f}s")
    print(f"✓ Version: {health['version']}")
    
    if "metrics" in health:
        print(f"✓ Total requests: {health['metrics']['total_requests']}")
        print(f"✓ Error rate: {health['metrics']['error_rate']:.2%}")
    
    # Test readiness status
    readiness = get_readiness_status()
    print(f"✓ Ready: {readiness['ready']}")
    print(f"✓ Chain status: {readiness['checks']['chain']}")
    print(f"✓ Storage status: {readiness['checks']['storage']}")
    
    return health, readiness


async def test_chain_with_monitoring():
    print("\n=== Testing Chain with Monitoring ===")
    
    from app.chains.conditional_chain import process_with_chain
    
    # Test different scenarios
    test_cases = [
        {
            "comment": "Hello there!",
            "post_id": "test_post_1",
            "comment_id": "test_comment_1", 
            "username": "test_user",
            "scenario": "Simple greeting"
        },
        {
            "comment": "How do I use the API?",
            "post_id": "test_post_2",
            "comment_id": "test_comment_2",
            "username": "test_user",
            "scenario": "Technical question"
        }
    ]
    
    for test_case in test_cases:
        print(f"\n--- {test_case['scenario']} ---")
        
        try:
            start_time = time.time()
            
            reply = await process_with_chain(
                comment=test_case["comment"],
                post_id=test_case["post_id"],
                comment_id=test_case["comment_id"],
                username=test_case["username"],
                enable_monitoring=True
            )
            
            duration = time.time() - start_time
            print(f"✓ Reply generated in {duration:.3f}s")
            print(f"✓ Reply: {reply[:100]}...")
            
        except Exception as e:
            print(f"✗ Error: {e}")


def show_log_file_contents():
    print("\n=== Log File Contents ===")
    
    log_file = Path("logs/monitoring.jsonl")
    if log_file.exists():
        with open(log_file, 'r') as f:
            lines = f.readlines()
            
        print(f"Total log entries: {len(lines)}")
        print("\nRecent entries:")
        
        for line in lines[-5:]:  # Show last 5 entries
            entry = json.loads(line)
            timestamp = entry["timestamp"].split("T")[1][:8]  # HH:MM:SS
            print(f"  {timestamp} | {entry['step']:>6} | {entry['duration']:>6.3f}s | {entry['severity']}")
    else:
        print("No log file found")


async def main():
    """Run all Phase 1 monitoring tests"""
    print("🚀 Instagram AI Agent - Phase 1 Monitoring Tests\n")
    
    # Test individual components
    test_file_logging()
    test_basic_metrics()
    await test_health_endpoints()
    
    # Test integrated chain monitoring
    await test_chain_with_monitoring()
    
    # Show log file results
    show_log_file_contents()
    
    print("\n✅ Phase 1 monitoring tests completed!")
    print("Check 'logs/monitoring.jsonl' for detailed logs")


if __name__ == "__main__":
    asyncio.run(main())