from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.api import router
from app.config import settings
from app.services.logger import setup_logging, logger

@asynccontextmanager
async def lifespan(app: FastAPI):
    print(">> Startup mulai")
    setup_logging()
    print("Startup berjalan")
    logger.info("FastAPI started", env=getattr(settings, "ENV", "production"))
    yield
    print(">>> after yield")
    # Cleanup/log shutdown
    logger.info("FastAPI shutdown")

app = FastAPI(
    title="z3 Agent",
    description="AI Agent cihuyy",
    version="0.1.0",
    contact={"name": "z3-agent"},
    lifespan=lifespan,
)

app.include_router(router, prefix="/api")