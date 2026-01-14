"""
AdSphere API Module
Combines all API routes into a single router
"""

from fastapi import APIRouter

# Import all routers
from .get_ads import router as ads_router
from .get_categories import router as categories_router
from .get_companies import router as companies_router
from .track_interaction import router as track_router
from .track_event import router as track_event_router
from .dashboard_stats import router as dashboard_router
from .live_activity import router as activity_router
from .block_ad import router as block_router
from .report_ad import router as report_router
from .ad_status_stats import router as status_router
from .update_ad_status import router as update_ad_router
from .update_company_status import router as update_company_router
from .delete_ad import router as delete_router
from .duplicate_ad import router as duplicate_router
from .schedule_ad import router as schedule_router
from .get_analytics import router as analytics_router
from .contact_analytics import router as contact_router
from .user_feedback_stats import router as feedback_router
from .user_profiling import router as profiling_router
from .ai_search import router as search_router
from .scanner import router as scanner_router
from .moderation_violations import router as violations_router
from .admin import admin_router

# Create main API router
api_router = APIRouter(prefix="/api", tags=["API"])

# Include all sub-routers
api_router.include_router(ads_router, tags=["Ads"])
api_router.include_router(categories_router, tags=["Categories"])
api_router.include_router(companies_router, tags=["Companies"])
api_router.include_router(track_router, tags=["Tracking"])
api_router.include_router(track_event_router, tags=["Tracking"])
api_router.include_router(dashboard_router, tags=["Dashboard"])
api_router.include_router(activity_router, tags=["Activity"])
api_router.include_router(block_router, tags=["User Feedback"])
api_router.include_router(report_router, tags=["User Feedback"])
api_router.include_router(feedback_router, tags=["User Feedback"])
api_router.include_router(profiling_router, tags=["User Profiling"])
api_router.include_router(status_router, tags=["Status"])
api_router.include_router(update_ad_router, tags=["Admin"])
api_router.include_router(update_company_router, tags=["Admin"])
api_router.include_router(delete_router, tags=["Admin"])
api_router.include_router(duplicate_router, tags=["Admin"])
api_router.include_router(schedule_router, tags=["Admin"])
api_router.include_router(analytics_router, tags=["Analytics"])
api_router.include_router(contact_router, tags=["Analytics"])
api_router.include_router(search_router, tags=["Search"])
api_router.include_router(scanner_router, tags=["Moderation"])
api_router.include_router(violations_router, tags=["Moderation"])
api_router.include_router(admin_router, tags=["Admin"])


# Health check endpoint
@api_router.get("/health")
async def health_check():
    """API Health check"""
    return {
        "status": "healthy",
        "service": "adsphere-api",
        "version": "1.0.0"
    }


__all__ = ["api_router"]

