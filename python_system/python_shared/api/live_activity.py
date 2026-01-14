"""
live_activity.py - Live Activity Feed API
Real-time updates on platform activity
Converted from PHP to Python
"""

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from pathlib import Path
from datetime import datetime
import json
import time
import random

router = APIRouter()

# Paths
ANALYTICS_PATH = Path(__file__).parent.parent / "companies" / "analytics"
DATA_PATH = Path(__file__).parent.parent / "companies" / "data"


def geolocate_ip(ip: str) -> str:
    """Simple city detection based on IP (placeholder)"""
    cities = ['Nairobi', 'Mombasa', 'Kisumu', 'Nakuru', 'Eldoret', 'Thika']
    return random.choice(cities)


def time_ago(timestamp: int) -> str:
    """Convert timestamp to human-readable time ago"""
    diff = int(time.time()) - timestamp

    if diff < 60:
        return "Just now"
    elif diff < 3600:
        mins = diff // 60
        return f"{mins} min{'s' if mins > 1 else ''} ago"
    elif diff < 86400:
        hours = diff // 3600
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    else:
        days = diff // 86400
        return f"{days} day{'s' if days > 1 else ''} ago"


@router.get("/live_activity")
async def live_activity(company: str = None, limit: int = Query(30, ge=1, le=100)):
    """Get recent platform activity"""
    try:
        activities = []

        if not ANALYTICS_PATH.exists():
            return {
                "success": True,
                "activities": [],
                "total": 0,
                "generated_at": int(time.time())
            }

        # Scan analytics files
        for analytics_file in ANALYTICS_PATH.glob("*.json"):
            try:
                with open(analytics_file, "r") as f:
                    analytics = json.load(f)

                ad_id = analytics.get("ad_id", analytics_file.stem)

                # Try to get ad title from meta file
                ad_title = "Untitled"
                # Search for meta.json in data directory
                if DATA_PATH.exists():
                    for category_dir in DATA_PATH.iterdir():
                        if category_dir.is_dir():
                            for company_dir in category_dir.iterdir():
                                if company_dir.is_dir():
                                    ad_dir = company_dir / ad_id
                                    if ad_dir.exists():
                                        meta_file = ad_dir / "meta.json"
                                        if meta_file.exists():
                                            with open(meta_file, "r") as mf:
                                                meta = json.load(mf)
                                                ad_title = meta.get("title", "Untitled")
                                        break

                # Get recent events (last 50)
                events = analytics.get("events", [])[-50:]

                # Only include events from last 24 hours
                cutoff = int(time.time()) - 86400

                for event in events:
                    event_time = event.get("timestamp", 0)
                    if event_time > cutoff:
                        activities.append({
                            "ad_id": ad_id,
                            "ad_title": ad_title,
                            "type": event.get("type", "unknown"),
                            "action": event.get("action", event.get("type", "unknown")),
                            "timestamp": event_time,
                            "location": geolocate_ip(event.get("ip", "")),
                            "time_ago": time_ago(event_time)
                        })

            except Exception:
                continue

        # Sort by timestamp (most recent first)
        activities.sort(key=lambda x: x["timestamp"], reverse=True)

        # Limit results
        activities = activities[:limit]

        return {
            "success": True,
            "activities": activities,
            "total": len(activities),
            "generated_at": int(time.time())
        }

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


@router.get("/live_activity/stats")
async def activity_stats():
    """Get activity statistics summary"""
    try:
        stats = {
            "total_events_24h": 0,
            "views_24h": 0,
            "contacts_24h": 0,
            "likes_24h": 0,
            "event_types": {}
        }

        if not ANALYTICS_PATH.exists():
            return {"success": True, **stats}

        cutoff = int(time.time()) - 86400

        for analytics_file in ANALYTICS_PATH.glob("*.json"):
            try:
                with open(analytics_file, "r") as f:
                    analytics = json.load(f)

                for event in analytics.get("events", []):
                    if event.get("timestamp", 0) > cutoff:
                        stats["total_events_24h"] += 1
                        event_type = event.get("type", "unknown")

                        if event_type == "view":
                            stats["views_24h"] += 1
                        elif event_type in ["call", "sms", "email", "whatsapp"]:
                            stats["contacts_24h"] += 1
                        elif event_type == "like":
                            stats["likes_24h"] += 1

                        stats["event_types"][event_type] = stats["event_types"].get(event_type, 0) + 1

            except Exception:
                continue

        return {"success": True, **stats}

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

