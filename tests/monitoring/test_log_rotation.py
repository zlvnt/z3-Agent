"""
Test log rotation functionality.
"""

import json
import time
import sys
import os
from pathlib import Path

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.monitoring.rotation import LogRotator, get_log_rotator
from app.monitoring.callbacks import file_logger_callback


def test_log_rotation():
    print("=== Testing Log Rotation ===")
    
    # Create a small max size for testing (0.001 MB = 1KB)
    rotator = LogRotator(max_size_mb=0.001, max_files=3)
    
    # Generate lots of log entries to trigger rotation
    print("Generating log entries...")
    for i in range(100):
        file_logger_callback(
            step_name="test",
            duration=0.5 + (i * 0.01),
            context={"test_iteration": i, "extra_data": "x" * 50}
        )
    
    # Check rotation status
    status = rotator.get_status()
    print(f"✓ Current log size: {status['current_size_mb']} MB")
    print(f"✓ Needs rotation: {status['needs_rotation']}")
    print(f"✓ Rotated files: {status['rotated_files_count']}")
    
    # Force rotation
    if rotator.rotate_now():
        print("✓ Manual rotation successful")
    
    # Check files in logs directory
    logs_dir = Path("logs")
    log_files = list(logs_dir.glob("*.jsonl*"))
    print(f"✓ Total log files: {len(log_files)}")
    
    for log_file in sorted(log_files):
        size_kb = log_file.stat().st_size / 1024
        print(f"  - {log_file.name}: {size_kb:.1f} KB")
    
    return status


def test_health_with_rotation():
    print("\n=== Testing Health Check with Rotation ===")
    
    from app.monitoring.health import get_health_status
    
    health = get_health_status()
    
    if "log_rotation" in health:
        rotation_status = health["log_rotation"]
        print(f"✓ Current size: {rotation_status.get('current_size_mb', 0)} MB")
        print(f"✓ Max size: {rotation_status.get('max_size_mb', 0)} MB")
        print(f"✓ Rotated files: {rotation_status.get('rotated_files_count', 0)}")
        print(f"✓ Needs rotation: {rotation_status.get('needs_rotation', False)}")
    else:
        print("✗ Log rotation status not found in health check")


def demonstrate_auto_rotation():
    print("\n=== Demonstrating Auto Rotation ===")
    
    # Clear existing logs for clean demo
    logs_dir = Path("logs")
    for log_file in logs_dir.glob("monitoring*.jsonl*"):
        log_file.unlink()
        print(f"✓ Removed {log_file.name}")
    
    # Create very small rotator for demo
    rotator = LogRotator(max_size_mb=0.0005, max_files=2)  # 0.5KB max
    
    print("Generating entries until auto-rotation...")
    
    for i in range(50):
        # This will auto-rotate when size limit is reached
        file_logger_callback(
            step_name="demo",
            duration=1.0,
            context={"iteration": i, "padding": "x" * 100}
        )
        
        if i % 10 == 0:
            status = rotator.get_status()
            print(f"  Iteration {i}: {status ['current_size_mb']:.3f} MB, files: {status['total_log_files']}")
    
    # Final status
    final_status = rotator.get_status()
    print(f"\n✓ Final status:")
    print(f"  Current size: {final_status['current_size_mb']} MB")
    print(f"  Total files: {final_status['total_log_files']}")
    print(f"  Rotated files: {final_status['rotated_files_count']}")


if __name__ == "__main__":
    print("🔄 Log Rotation Tests\n")
    
    test_log_rotation()
    test_health_with_rotation()
    demonstrate_auto_rotation()
    
    print("\n✅ Log rotation tests completed!")
    print("Check 'logs/' directory for rotated files")