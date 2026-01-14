"""
get_analytics.py - Get Analytics API
Retrieves analytics data for company ads
Converted from PHP to Python
"""

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from pathlib import Path
import json

router = APIRouter()

ANALYTICS_PATH = Path(__file__).parent.parent / "companies" / "analytics"


@router.get("/analytics/{ad_id}")
async def get_ad_analytics(ad_id: str):
    """Get analytics for a specific ad"""
    try:
        analytics_file = ANALYTICS_PATH / f"{ad_id}.json"

        if not analytics_file.exists():
            # Return default analytics
            return {
                "success": True,
                "analytics": {
                    "ad_id": ad_id,
                    "total_views": 0,
                    "total_clicks": 0,
                    "total_contacts": 0,
                    "total_likes": 0,
                    "total_dislikes": 0,
                    "total_favorites": 0,
                    "events": []
                }
            }

        with open(analytics_file, "r") as f:
            analytics = json.load(f)

        return {
            "success": True,
            "analytics": analytics
        }

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


@router.get("/analytics")
async def get_all_analytics(company: str = Query(None)):
    """Get analytics for all ads or by company"""
    try:
        all_analytics = []

        if not ANALYTICS_PATH.exists():
            return {"success": True, "analytics": [], "total": 0}

        for analytics_file in ANALYTICS_PATH.glob("*.json"):
            try:
                with open(analytics_file, "r") as f:
                    analytics = json.load(f)
                    all_analytics.append(analytics)
            except Exception:
                continue

        # Calculate totals
        totals = {
            "total_views": sum(a.get("total_views", 0) for a in all_analytics),
            "total_contacts": sum(a.get("total_contacts", 0) for a in all_analytics),
            "total_likes": sum(a.get("total_likes", 0) for a in all_analytics),
            "total_dislikes": sum(a.get("total_dislikes", 0) for a in all_analytics),
            "total_favorites": sum(a.get("total_favorites", 0) for a in all_analytics)
        }

        return {
            "success": True,
            "analytics": all_analytics,
            "totals": totals,
            "total": len(all_analytics)
        }

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


@router.get("/analytics/summary")
async def analytics_summary():
    """Get summary of all analytics"""
    try:
        if not ANALYTICS_PATH.exists():
            return {
                "success": True,
                "summary": {
                    "total_ads_tracked": 0,
                    "total_views": 0,
                    "total_contacts": 0,
                    "total_likes": 0,
                    "total_favorites": 0
                }
            }

        total_views = 0
        total_contacts = 0
        total_likes = 0
        total_favorites = 0
        ads_tracked = 0

        for analytics_file in ANALYTICS_PATH.glob("*.json"):
            try:
                with open(analytics_file, "r") as f:
                    analytics = json.load(f)
                    ads_tracked += 1
                    total_views += analytics.get("total_views", 0)
                    total_contacts += analytics.get("total_contacts", 0)
                    total_likes += analytics.get("total_likes", 0)
                    total_favorites += analytics.get("total_favorites", 0)
            except Exception:
                continue

        return {
            "success": True,
            "summary": {
                "total_ads_tracked": ads_tracked,
                "total_views": total_views,
                "total_contacts": total_contacts,
                "total_likes": total_likes,
                "total_favorites": total_favorites
            }
        }

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

