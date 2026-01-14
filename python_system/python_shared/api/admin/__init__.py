"""
Admin API Module
"""

from fastapi import APIRouter

from .get_users import router as users_router

admin_router = APIRouter(prefix="/api", tags=["Admin"])

admin_router.include_router(users_router)

__all__ = ["admin_router"]

