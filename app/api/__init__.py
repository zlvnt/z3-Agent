from fastapi import APIRouter
print(">> imported app.api root")
from .webhook import router as webhook_router
print(">> imported webhook router")

router = APIRouter()
router.include_router(webhook_router, prefix="/webhook", tags=["instagram"])

__all__ = ["router"]