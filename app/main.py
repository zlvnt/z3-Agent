"""
FastAPI entry-point.
• Meng-include router API
• Menambah middleware CORS & logger (bila perlu)
• Menyediakan /healthz
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import router as api_router
from app.config import settings
from app.services.logger import logger

app = FastAPI(
    title="Instagram AI Agent",
    version="1.0.0",
    docs_url="/docs",
    redoc_url=None,
)

# ────── Middleware CORS (opsional) ──────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.ENV == "local" else ["https://your-domain.com"],
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

# ────── Include seluruh endpoint API ─────────────────────
app.include_router(api_router)

# ────── Health check endpoint ───────────────────────────
@app.get("/healthz", tags=["meta"])
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


# ────── Event Hooks ─────────────────────────────────────
@app.on_event("startup")
async def on_startup() -> None:
    logger.info("⚡️ API started", env=settings.ENV)


@app.on_event("shutdown")
async def on_shutdown() -> None:
    logger.info("🛑 API stopped")
