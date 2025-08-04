from fastapi import APIRouter
print(">> imported app.api root")
from .webhook import router as webhook_router
from app.channels.telegram.webhook import router as telegram_router
print(">> imported webhook routers")

router = APIRouter()
router.include_router(webhook_router, prefix="/webhook", tags=["instagram"])
router.include_router(telegram_router, tags=["telegram"])

__all__ = ["router"]