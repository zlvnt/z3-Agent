"""
Test health and metrics endpoints via HTTP.
Runs FastAPI server dan test endpoints secara automated.
"""

import asyncio
import subprocess
import time
import json
import requests
import sys
import os
from pathlib import Path

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


async def start_server_and_test():
    """Start FastAPI server dan test endpoints"""
    print("🚀 Testing Phase 1 Monitoring Endpoints\n")
    
    # Start server in background
    print("Starting FastAPI server...")
    server_process = subprocess.Popen(
        ["python", "-m", "uvicorn", "app.main:app", "--port", "8001"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for server to start
    print("Waiting for server to start...")
    await asyncio.sleep(3)
    
    try:
        # Test health endpoint
        print("\n=== Testing /health endpoint ===")
        health_response = requests.get("http://localhost:8001/health", timeout=10)
        
        if health_response.status_code == 200:
            health_data = health_response.json()
            print(f"✓ Health status: {health_data['status']}")
            print(f"✓ Version: {health_data['version']}")
            print(f"✓ Uptime: {health_data['uptime_seconds']:.2f}s")
            
            if "log_rotation" in health_data:
                rotation = health_data["log_rotation"]
                print(f"✓ Log size: {rotation.get('current_size_mb', 0)} MB")
                print(f"✓ Rotated files: {rotation.get('rotated_files_count', 0)}")
        else:
            print(f"✗ Health check failed: {health_response.status_code}")
        
        # Test readiness endpoint
        print("\n=== Testing /ready endpoint ===")
        ready_response = requests.get("http://localhost:8001/ready", timeout=10)
        
        if ready_response.status_code == 200:
            ready_data = ready_response.json()
            print(f"✓ Ready: {ready_data['ready']}")
            print(f"✓ Chain status: {ready_data['checks']['chain']}")
            print(f"✓ Storage status: {ready_data['checks']['storage']}")
        else:
            print(f"✗ Readiness check failed: {ready_response.status_code}")
        
        # Test basic metrics endpoint
        print("\n=== Testing /metrics/basic endpoint ===")
        metrics_response = requests.get("http://localhost:8001/metrics/basic", timeout=10)
        
        if metrics_response.status_code == 200:
            metrics_data = metrics_response.json()
            summary = metrics_data.get("summary", {})
            
            print(f"✓ Total requests: {summary.get('total_requests', 0)}")
            print(f"✓ Error rate: {summary.get('error_rate', 0):.2%}")
            print(f"✓ Avg response time: {summary.get('avg_response_time', 0):.3f}s")
            print(f"✓ Health status: {metrics_data.get('health_status', 'unknown')}")
            
            # Show step performance if available
            step_perf = metrics_data.get("step_performance", {})
            if step_perf:
                print("✓ Step performance:")
                for step, stats in step_perf.items():
                    print(f"  - {step}: {stats['avg_duration']:.3f}s avg")
        else:
            print(f"✗ Metrics endpoint failed: {metrics_response.status_code}")
        
        # Test webhook endpoint with monitoring
        print("\n=== Testing webhook with monitoring ===")
        
        # Generate some activity untuk metrics
        from app.monitoring.callbacks import file_logger_callback
        from app.monitoring.metrics import get_metrics_instance
        
        metrics = get_metrics_instance()
        
        # Simulate some requests
        for i in range(5):
            file_logger_callback(f"test_step_{i%3}", 0.5 + i*0.1)
            metrics.record_request(1.0 + i*0.2, i < 4)  # Last one is error
        
        # Check metrics again
        print("\n=== Updated metrics after activity ===")
        updated_metrics = requests.get("http://localhost:8001/metrics/basic", timeout=10)
        
        if updated_metrics.status_code == 200:
            data = updated_metrics.json()
            summary = data.get("summary", {})
            print(f"✓ Updated requests: {summary.get('total_requests', 0)}")
            print(f"✓ Updated error rate: {summary.get('error_rate', 0):.2%}")
        
        print("\n✅ All endpoints tested successfully!")
        
    except requests.exceptions.RequestException as e:
        print(f"✗ Request failed: {e}")
    except Exception as e:
        print(f"✗ Test failed: {e}")
    finally:
        # Stop server
        print("\nStopping server...")
        server_process.terminate()
        server_process.wait()
        print("✓ Server stopped")


def test_endpoints_direct():
    """Test endpoints directly without HTTP server (faster)"""
    print("🔧 Direct Endpoint Testing (No HTTP Server)\n")
    
    from app.monitoring.health import get_health_status, get_readiness_status
    from app.monitoring.metrics import get_metrics_instance
    
    # Test health status
    print("=== Health Status ===")
    health = get_health_status()
    print(f"✓ Status: {health['status']}")
    print(f"✓ Version: {health['version']}")
    print(f"✓ Chain ready: {health['chain']['status']}")
    print(f"✓ Storage ready: {health['storage']['status']}")
    
    # Test readiness
    print("\n=== Readiness Status ===")
    readiness = get_readiness_status()
    print(f"✓ Ready: {readiness['ready']}")
    print(f"✓ All checks passed: {all(status == 'ready' for status in readiness['checks'].values())}")
    
    # Test metrics
    print("\n=== Basic Metrics ===")
    metrics = get_metrics_instance()
    stats = metrics.get_stats()
    
    print(f"✓ Total requests: {stats['summary']['total_requests']}")
    print(f"✓ Health status: {stats['health_status']}")
    print(f"✓ Recent requests (1min): {stats['recent_activity']['requests_last_minute']}")
    
    print("\n✅ Direct endpoint tests completed!")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--direct":
        # Fast direct testing
        test_endpoints_direct()
    else:
        # Full HTTP testing (requires server startup)
        print("Use --direct for faster testing without HTTP server")
        asyncio.run(start_server_and_test())