from fastapi import APIRouter
print(">> imported app.api root")
# Instagram channels disabled (not priority - requires Advanced Access for DM)
# from app.channels.instagram.webhook import router as instagram_router
# from app.channels.instagram_dm.webhook import router as instagram_dm_router
from app.channels.telegram.webhook import router as telegram_router
print(">> imported webhook routers")

router = APIRouter()
# Instagram channels disabled
# router.include_router(instagram_router, tags=["instagram"])
# router.include_router(instagram_dm_router, tags=["instagram_dm"])
router.include_router(telegram_router, tags=["telegram"])

__all__ = ["router"]