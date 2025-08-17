from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.api import router
from app.config import settings
from app.monitoring import get_health_status, get_metrics_instance
from app.monitoring.health import get_readiness_status
from app.monitoring.enhanced_metrics import get_enhanced_metrics_instance
from app.monitoring.simple_alerts import get_alerts_instance

@asynccontextmanager
async def lifespan(app: FastAPI):
    print(">> Startup mulai")
    print(">> FastAPI startup complete")
    yield
    print(">>> FastAPI shutdown")

app = FastAPI(
    title="z3 Agent",
    description="AI Agent cihuyy",
    version="0.1.0",
    contact={"name": "z3-agent"},
    lifespan=lifespan,
)

app.include_router(router, prefix="/api")

# Health check endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return get_health_status()

@app.get("/ready")  
async def readiness_check():
    """Readiness check endpoint for Kubernetes"""
    return get_readiness_status()

@app.get("/metrics/basic")
async def basic_metrics():
    """Basic metrics endpoint"""
    metrics = get_metrics_instance()
    return metrics.get_stats()

@app.get("/metrics")
async def enhanced_metrics():
    """Enhanced metrics endpoint with channel-specific data"""
    metrics = get_enhanced_metrics_instance()
    return metrics.get_enhanced_stats()

@app.get("/metrics/alerts")
async def alert_status():
    """Alert system status and configuration"""
    alerts = get_alerts_instance()
    return alerts.get_alert_status()

@app.get("/metrics/summary")
async def metrics_summary():
    """Compact metrics summary for quick monitoring"""
    metrics = get_enhanced_metrics_instance()
    stats = metrics.get_enhanced_stats()
    
    return {
        "timestamp": stats["summary"]["uptime_seconds"],
        "requests_total": stats["summary"]["total_requests"],
        "error_rate": stats["summary"]["error_rate"],
        "avg_response_time": stats["summary"]["avg_response_time"],
        "health_status": stats["health_status"],
        "channels": {
            channel: {
                "requests": data["requests"],
                "error_rate": data["error_rate"]
            } for channel, data in stats.get("channels", {}).items()
        },
        "alerts": stats.get("alerts", {})
    }

@app.get("/metrics/requests")
async def recent_requests():
    """Get recent user request logs"""
    from app.monitoring.request_logger import get_request_logger
    logger = get_request_logger()
    return {
        "recent_requests": logger.get_recent_requests(20)
    }