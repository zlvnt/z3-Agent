from fastapi import FastAPI

from app.api import api_router
from app.config import settings
from app.services.logger import logger  # opsional: kalau mau log saat start

app = FastAPI(
    title="Instagram AI Agent",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Mount every API router
app.include_router(api_router)

# Simple health-check
@app.get("/", tags=["health"])
def health():
    return {"status": "ok", "env": settings.ENV}


# ----- optional startup/shutdown hooks -----
@app.on_event("startup")
def _startup() -> None:
    logger.info("FastAPI started", env=settings.ENV)


@app.on_event("shutdown")
def _shutdown() -> None:
    logger.info("FastAPI shutdown")
