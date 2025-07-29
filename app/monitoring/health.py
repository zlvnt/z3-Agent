"""
Health check functionality.
Provides system health status & readiness checks.
"""

import time
import os
from typing import Dict, Any
from pathlib import Path

from .metrics import get_metrics_instance


def get_health_status() -> Dict[str, Any]:
    """
    Get comprehensive health status.
    Suitable for Kubernetes health checks.
    """
    metrics = get_metrics_instance()
    stats = metrics.get_stats()
    
    # Basic system checks
    health_data = {
        "status": stats["health_status"],
        "timestamp": time.time(),
        "uptime_seconds": stats["summary"]["uptime_seconds"],
        "version": "2.1",
        "environment": os.getenv("ENVIRONMENT", "development")
    }
    
    # Performance metrics
    health_data["metrics"] = {
        "total_requests": stats["summary"]["total_requests"],
        "error_rate": round(stats["summary"]["error_rate"], 4),
        "avg_response_time": round(stats["summary"]["avg_response_time"], 3),
        "requests_per_minute": stats["recent_activity"]["requests_last_minute"]
    }
    
    # Chain-specific health
    health_data["chain"] = _get_chain_health()
    
    # Storage health
    health_data["storage"] = _get_storage_health()
    
    # Log rotation status
    health_data["log_rotation"] = _get_log_rotation_status()
    
    return health_data


def get_readiness_status() -> Dict[str, Any]:
    """
    Get readiness status for load balancer.
    More strict than health check.
    """
    health = get_health_status()
    
    # Check if system is ready to serve traffic
    is_ready = (
        health["status"] in ["healthy", "degraded"] and
        health["chain"]["status"] == "ready" and
        health["storage"]["status"] == "ready"
    )
    
    return {
        "ready": is_ready,
        "timestamp": time.time(),
        "checks": {
            "health": health["status"],
            "chain": health["chain"]["status"],
            "storage": health["storage"]["status"]
        }
    }


def _get_chain_health() -> Dict[str, Any]:
    # Check chain-specific health
    try:
        from app.chains.conditional_chain import get_chain
        
        chain = get_chain()
        chain_stats = chain.get_stats()
        
        return {
            "status": "ready",
            "callbacks_registered": chain_stats["callbacks_count"],
            "memory_window": chain_stats["memory_window"],
            "using_conversation_service": chain_stats["using_conversation_service"]
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


def _get_storage_health() -> Dict[str, Any]:
    # Check storage and file system health
    checks = {}
    
    # Check logs directory
    logs_dir = Path("logs")
    checks["logs_directory"] = {
        "exists": logs_dir.exists(),
        "writable": logs_dir.is_dir() and os.access(logs_dir, os.W_OK) if logs_dir.exists() else False
    }
    
    # Check data directory
    data_dir = Path("data")
    checks["data_directory"] = {
        "exists": data_dir.exists(),
        "writable": data_dir.is_dir() and os.access(data_dir, os.W_OK) if data_dir.exists() else False
    }
    
    # Check conversation file
    conversations_file = Path("data/conversations.json")
    checks["conversations_file"] = {
        "exists": conversations_file.exists(),
        "readable": conversations_file.is_file() and os.access(conversations_file, os.R_OK) if conversations_file.exists() else False
    }
    
    # Determine overall storage status
    all_good = all(
        check["exists"] and (check.get("writable", True) or check.get("readable", True))
        for check in checks.values()
    )
    
    return {
        "status": "ready" if all_good else "error",
        "checks": checks
    }


def _get_log_rotation_status() -> Dict[str, Any]:
    # Get log rotation status
    try:
        from .rotation import get_log_rotator
        rotator = get_log_rotator()
        return rotator.get_status()
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }