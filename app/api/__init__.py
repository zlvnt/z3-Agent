from fastapi import APIRouter
from .webhook import router as webhook_router

router = APIRouter()
router.include_router(webhook_router, prefix="/webhook", tags=["instagram"])

__all__ = ["router"]