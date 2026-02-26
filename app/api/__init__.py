from fastapi import APIRouter
print(">> imported app.api root")
# Instagram channels disabled (not priority - requires Advanced Access for DM)
# from app.channels.instagram.webhook import router as instagram_router
# from app.channels.instagram_dm.webhook import router as instagram_dm_router
from app.channels.telegram.webhook import router as telegram_router
from app.api.chat import router as chat_router
from app.api.rag_test import router as rag_test_router
print(">> imported webhook routers")

router = APIRouter()
# Instagram channels disabled
# router.include_router(instagram_router, tags=["instagram"])
# router.include_router(instagram_dm_router, tags=["instagram_dm"])
router.include_router(telegram_router, tags=["telegram"])
router.include_router(chat_router, tags=["chat"])
router.include_router(rag_test_router, tags=["rag-test"])

__all__ = ["router"]
