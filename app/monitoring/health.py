"""
Health check functions for z3-Agent.

Provides health and readiness endpoints for monitoring and Kubernetes.
"""

import time
from typing import Dict, Any

from app.config import settings

_start_time = time.time()


def get_health_status() -> Dict[str, Any]:
    """
    Get health status for /health endpoint.

    Returns basic system health including uptime, version,
    and core component status.
    """
    uptime = time.time() - _start_time

    from app.monitoring.enhanced_metrics import get_enhanced_metrics_instance
    metrics = get_enhanced_metrics_instance()
    stats = metrics.get_stats()

    return {
        "status": "healthy",
        "timestamp": time.time(),
        "uptime_seconds": round(uptime, 1),
        "version": "0.1.0",
        "environment": settings.AGENT_MODE,
        "metrics": {
            "total_requests": stats["total_requests"],
            "error_rate": stats["error_rate"],
            "avg_response_time": stats["avg_response_time"],
            "requests_per_minute": round(
                stats["total_requests"] / max(uptime / 60, 1), 2
            ),
        },
        "chain": {"status": "available"},
        "storage": {"status": "available"},
    }


def get_readiness_status() -> Dict[str, Any]:
    """
    Get readiness status for /ready endpoint (Kubernetes).

    Checks if the application is ready to serve requests.
    """
    checks = {
        "config": True,
        "chain": True,
    }

    # Check if critical config is present
    if not settings.GEMINI_API_KEY:
        checks["config"] = False

    all_ready = all(checks.values())

    return {
        "status": "ready" if all_ready else "not_ready",
        "checks": checks,
        "timestamp": time.time(),
    }
