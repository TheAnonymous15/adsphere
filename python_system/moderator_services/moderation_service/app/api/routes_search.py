"""
Search Routes - AI-powered category search endpoints
"""

from fastapi import APIRouter
from ..services.search_assisatnt.search_service import router as search_router

# Re-export the search router
__all__ = ['search_router']

