"""
track_event.py - Track Event API
Records ad views, clicks, and contacts
Converted from PHP to Python
"""

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pathlib import Path
import json
import time

router = APIRouter()

ANALYTICS_PATH = Path(__file__).parent.parent / "companies" / "analytics"
ANALYTICS_PATH.mkdir(parents=True, exist_ok=True)


@router.post("/track_event")
async def track_event(request: Request):
    """Track event - matches PHP logic exactly"""
    try:
        data = await request.json()

        event_type = data.get("event_type", "")  # 'view', 'click', 'contact'
        ad_id = data.get("ad_id", "")
        metadata = data.get("metadata", {})

        if not event_type or not ad_id:
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "Missing required parameters"}
            )

        # Load or create analytics file (matching PHP structure)
        analytics_file = ANALYTICS_PATH / f"{ad_id}.json"
        analytics = {}

        if analytics_file.exists():
            with open(analytics_file, "r") as f:
                analytics = json.load(f)

        # Initialize structure if needed (matching PHP defaults)
        if "ad_id" not in analytics:
            analytics["ad_id"] = ad_id
            analytics["total_views"] = 0
            analytics["total_clicks"] = 0
            analytics["total_contacts"] = 0
            analytics["events"] = []

        # Create event (matching PHP event structure)
        event = {
            "type": event_type,
            "timestamp": int(time.time()),
            "ip": request.client.host if request.client else "unknown",
            "user_agent": request.headers.get("user-agent", "unknown"),
            "metadata": metadata
        }

        analytics["events"].append(event)

        # Update counters (matching PHP switch statement)
        if event_type == "view":
            analytics["total_views"] = analytics.get("total_views", 0) + 1
        elif event_type == "click":
            analytics["total_clicks"] = analytics.get("total_clicks", 0) + 1
        elif event_type == "contact":
            analytics["total_contacts"] = analytics.get("total_contacts", 0) + 1
            analytics["last_contact"] = int(time.time())

        analytics["updated_at"] = int(time.time())

        # Save analytics
        with open(analytics_file, "w") as f:
            json.dump(analytics, f, indent=2)

        return {
            "success": True,
            "message": "Event tracked successfully",
            "event_type": event_type,
            "ad_id": ad_id
        }

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


@router.get("/track_event")
async def track_event_get(ad_id: str, event_type: str, request: Request):
    """Track event via GET request"""
    try:
        if not ad_id or not event_type:
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "Missing ad_id or event_type"}
            )

        # Load analytics
        analytics_file = ANALYTICS_PATH / f"{ad_id}.json"
        analytics = {
            "ad_id": ad_id,
            "total_views": 0,
            "total_clicks": 0,
            "total_contacts": 0,
            "events": []
        }

        if analytics_file.exists():
            with open(analytics_file, "r") as f:
                analytics = json.load(f)

        # Create event
        event = {
            "type": event_type,
            "timestamp": int(time.time()),
            "ip": request.client.host if request.client else "unknown",
            "user_agent": request.headers.get("user-agent", "unknown")
        }

        analytics["events"].append(event)

        # Update counters
        if event_type == "view":
            analytics["total_views"] = analytics.get("total_views", 0) + 1
        elif event_type == "click":
            analytics["total_clicks"] = analytics.get("total_clicks", 0) + 1
        elif event_type == "contact":
            analytics["total_contacts"] = analytics.get("total_contacts", 0) + 1
            analytics["last_contact"] = int(time.time())

        analytics["updated_at"] = int(time.time())

        # Save
        with open(analytics_file, "w") as f:
            json.dump(analytics, f, indent=2)

        return {
            "success": True,
            "message": "Event tracked successfully",
            "event_type": event_type,
            "ad_id": ad_id
        }

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )
