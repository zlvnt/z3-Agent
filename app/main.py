from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.api import router
from app.config import settings
from app.services.logger import setup_logging, logger
from app.monitoring import get_health_status, get_metrics_instance
from app.monitoring.health import get_readiness_status

@asynccontextmanager
async def lifespan(app: FastAPI):
    print(">> Startup mulai")
    setup_logging()
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