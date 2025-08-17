from fastapi import APIRouter
print(">> imported app.api root")
from app.channels.instagram.webhook import router as instagram_router
from app.channels.telegram.webhook import router as telegram_router
print(">> imported webhook routers")

router = APIRouter()
router.include_router(instagram_router, tags=["instagram"])
router.include_router(telegram_router, tags=["telegram"])

__all__ = ["router"]