"""
dashboard_stats.py - Advanced Dashboard Statistics API
Comprehensive analytics and insights
Converted from PHP to Python
"""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from pathlib import Path
from datetime import datetime, timedelta
import json
import time

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from models import Ad, Category, Company
from database import get_db

router = APIRouter()

# Paths
ANALYTICS_PATH = Path(__file__).parent.parent / "companies" / "analytics"
DATA_PATH = Path(__file__).parent.parent / "companies" / "data"


@router.get("/dashboard_stats")
async def dashboard_stats(
    company: str = None,
    db: Session = Depends(get_db)
):
    """Get comprehensive dashboard statistics"""
    try:
        # Build base query
        query = db.query(Ad)
        if company:
            query = query.filter(Ad.company_slug == company)

        # Overview stats
        total_ads = query.count()
        active_ads = query.filter(Ad.status == "active").count()
        paused_ads = db.query(Ad).filter(Ad.status == "paused")
        if company:
            paused_ads = paused_ads.filter(Ad.company_slug == company)
        paused_ads = paused_ads.count()

        scheduled_ads = db.query(Ad).filter(Ad.status == "scheduled")
        if company:
            scheduled_ads = scheduled_ads.filter(Ad.company_slug == company)
        scheduled_ads = scheduled_ads.count()

        blocked_ads = db.query(Ad).filter(Ad.status == "blocked")
        if company:
            blocked_ads = blocked_ads.filter(Ad.company_slug == company)
        blocked_ads = blocked_ads.count()

        # Performance stats
        perf_query = db.query(
            func.coalesce(func.sum(Ad.views_count), 0).label("total_views"),
            func.coalesce(func.sum(Ad.likes_count), 0).label("total_likes"),
            func.coalesce(func.sum(Ad.dislikes_count), 0).label("total_dislikes"),
            func.coalesce(func.sum(Ad.favorites_count), 0).label("total_favorites"),
            func.coalesce(func.sum(Ad.contacts_count), 0).label("total_contacts")
        )
        if company:
            perf_query = perf_query.filter(Ad.company_slug == company)
        perf = perf_query.first()

        total_views = int(perf[0]) if perf else 0
        total_likes = int(perf[1]) if perf else 0
        total_dislikes = int(perf[2]) if perf else 0
        total_favorites = int(perf[3]) if perf else 0
        total_contacts = int(perf[4]) if perf else 0

        # Category breakdown
        cat_query = db.query(
            Ad.category_slug,
            func.count(Ad.ad_id).label("count"),
            func.coalesce(func.sum(Ad.views_count), 0).label("views"),
            func.coalesce(func.sum(Ad.contacts_count), 0).label("contacts")
        )
        if company:
            cat_query = cat_query.filter(Ad.company_slug == company)
        categories = cat_query.group_by(Ad.category_slug).all()

        category_breakdown = {}
        for cat_slug, count, views, contacts in categories:
            category_breakdown[cat_slug] = {
                "count": count,
                "views": int(views),
                "contacts": int(contacts)
            }

        # Top performing ads
        top_query = db.query(Ad)
        if company:
            top_query = top_query.filter(Ad.company_slug == company)
        top_ads = top_query.filter(Ad.status == "active").order_by(
            Ad.views_count.desc()
        ).limit(5).all()

        top_performers = [
            {
                "ad_id": ad.ad_id,
                "title": ad.title,
                "views": ad.views_count or 0,
                "likes": ad.likes_count or 0,
                "contacts": ad.contacts_count or 0
            }
            for ad in top_ads
        ]

        # Get trends from analytics files
        trends = get_trends_from_analytics(company)

        # Calculate rates
        conversion_rate = round((total_contacts / total_views * 100), 2) if total_views > 0 else 0
        favorite_rate = round((total_favorites / total_views * 100), 2) if total_views > 0 else 0
        avg_views_per_ad = round(total_views / total_ads, 2) if total_ads > 0 else 0

        # Company stats (if not filtering by company)
        total_companies = db.query(func.count(Company.company_slug)).scalar() or 0
        total_categories = db.query(func.count(Category.category_slug)).scalar() or 0

        return {
            "success": True,
            "overview": {
                "total_ads": total_ads,
                "active_ads": active_ads,
                "paused_ads": paused_ads,
                "scheduled_ads": scheduled_ads,
                "blocked_ads": blocked_ads,
                "total_companies": total_companies,
                "total_categories": total_categories
            },
            "performance": {
                "total_views": total_views,
                "total_likes": total_likes,
                "total_dislikes": total_dislikes,
                "total_favorites": total_favorites,
                "total_contacts": total_contacts,
                "conversion_rate": conversion_rate,
                "favorite_rate": favorite_rate,
                "avg_views_per_ad": avg_views_per_ad
            },
            "categories": category_breakdown,
            "top_performers": top_performers,
            "trends": trends,
            "timestamp": int(time.time())
        }

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


def get_trends_from_analytics(company_slug: str = None) -> dict:
    """Extract trend data from analytics files"""
    trends = {
        "daily_stats": {},
        "views_trend": [],
        "contacts_trend": []
    }

    if not ANALYTICS_PATH.exists():
        return trends

    # Get last 30 days
    today = datetime.now()
    dates = [(today - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(30)]

    for date in dates:
        trends["daily_stats"][date] = {"views": 0, "contacts": 0, "clicks": 0}

    # Scan analytics files
    for analytics_file in ANALYTICS_PATH.glob("*.json"):
        try:
            with open(analytics_file, "r") as f:
                analytics = json.load(f)

            for event in analytics.get("events", []):
                event_time = event.get("timestamp", 0)
                if event_time:
                    date = datetime.fromtimestamp(event_time).strftime("%Y-%m-%d")
                    if date in trends["daily_stats"]:
                        event_type = event.get("type", "")
                        if event_type == "view":
                            trends["daily_stats"][date]["views"] += 1
                        elif event_type in ["call", "sms", "email", "whatsapp"]:
                            trends["daily_stats"][date]["contacts"] += 1
                        elif event_type == "click":
                            trends["daily_stats"][date]["clicks"] += 1

        except Exception:
            continue

    # Convert to arrays for charts
    for date in sorted(trends["daily_stats"].keys()):
        trends["views_trend"].append({
            "date": date,
            "value": trends["daily_stats"][date]["views"]
        })
        trends["contacts_trend"].append({
            "date": date,
            "value": trends["daily_stats"][date]["contacts"]
        })

    return trends


@router.get("/dashboard_stats/overview")
async def dashboard_overview(db: Session = Depends(get_db)):
    """Get quick overview stats"""
    try:
        total_ads = db.query(func.count(Ad.ad_id)).scalar() or 0
        active_ads = db.query(func.count(Ad.ad_id)).filter(Ad.status == "active").scalar() or 0
        total_views = db.query(func.coalesce(func.sum(Ad.views_count), 0)).scalar() or 0
        total_companies = db.query(func.count(Company.company_slug)).scalar() or 0

        return {
            "success": True,
            "total_ads": total_ads,
            "active_ads": active_ads,
            "total_views": int(total_views),
            "total_companies": total_companies
        }

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

