"""
Monitoring callbacks.
File-based logging dan metrics collection callbacks.
"""

import json
import os
import time
from datetime import datetime
from typing import Optional
from pathlib import Path


def file_logger_callback(step_name: str, duration: float, context: Optional[dict] = None) -> None:
    """
    Args:
        step_name: Name of the processing step
        duration: Duration in seconds  
        context: Optional additional context
    """
    try:
        # Auto-rotate logs if needed
        from .rotation import auto_rotate_logs
        auto_rotate_logs()
        
        # Ensure logs directory exists
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)
        
        # Create log entry
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "step": step_name,
            "duration": round(duration, 3),
            "channel": "instagram",
            "severity": _get_severity(step_name, duration),
            "context": context or {}
        }
        
        # Write to JSON Lines file
        log_file = logs_dir / "monitoring.jsonl"
        with open(log_file, "a") as f:
            json.dump(log_entry, f)
            f.write("\n")
            
    except Exception as e:
        print(f"WARNING: File logging callback failed: {e}")


def _get_severity(step_name: str, duration: float) -> str:
    """Determine severity based on step and duration"""
    thresholds = {
        "memory": 0.1,
        "router": 0.5, 
        "rag": 1.0,
        "reply": 2.0,
        "total": 3.0
    }
    
    threshold = thresholds.get(step_name, 1.0)
    
    if duration < threshold:
        return "normal"
    elif duration < threshold * 2:
        return "warning"
    else:
        return "critical"


def prometheus_callback(step_name: str, duration: float, context: Optional[dict] = None) -> None:
    """
    Prometheus metrics callback (just placeholder).
    Currently just tracks basic metrics.
    """
    try:
        from .metrics import get_metrics_instance
        metrics = get_metrics_instance()
        
        # Record timing data
        metrics.record_step_duration(step_name, duration)
        
        # Record request completion for total step
        if step_name == "total":
            success = context.get("success", True) if context else True
            metrics.record_request(duration, success)
            
    except Exception as e:
        print(f"WARNING: Prometheus callback failed: {e}")


def combined_callback(step_name: str, duration: float, context: Optional[dict] = None) -> None:
    """
    Combined callback: logging, metrics.
    Useful for development & testing.
    """
    file_logger_callback(step_name, duration, context)
    prometheus_callback(step_name, duration, context)


def debug_callback(step_name: str, duration: float, context: Optional[dict] = None) -> None:
    """
    Prints detailed timing information.
    """
    severity = _get_severity(step_name, duration)
    status_icon = {
        "normal": "🟢",
        "warning": "🟡", 
        "critical": "🔴"
    }.get(severity, "⚪")
    
    print(f"{status_icon} {step_name.upper()}: {duration:.3f}s ({severity})")
    
    if context:
        print(f"    Context: {context}")
        
    if severity in ["warning", "critical"]:
        print(f"    ⚠️  Performance issue detected in {step_name}")