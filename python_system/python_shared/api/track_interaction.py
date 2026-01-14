"""
track_interaction.py - Track User Interactions API
Handles likes, dislikes, favorites, and time spent
Converted from PHP to Python
"""

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
from pathlib import Path
import json
import time

router = APIRouter()

# Analytics storage path
ANALYTICS_PATH = Path(__file__).parent.parent / "companies" / "analytics"
ANALYTICS_PATH.mkdir(parents=True, exist_ok=True)


class InteractionData(BaseModel):
    interaction_type: str
    ad_id: str
    value: Optional[float] = None


@router.post("/track_interaction")
async def track_interaction(request: Request):
    """Track user interactions (like, dislike, favorite, time_spent, contact methods)"""
    try:
        data = await request.json()
        interaction_type = data.get("interaction_type", "")
        ad_id = data.get("ad_id", "")
        value = data.get("value")

        if not interaction_type or not ad_id:
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "Missing required parameters"}
            )

        # Load or create analytics file
        analytics_file = ANALYTICS_PATH / f"{ad_id}.json"

        # Default analytics structure
        analytics = {
            "ad_id": ad_id,
            "total_views": 0,
            "total_clicks": 0,
            "total_contacts": 0,
            "total_likes": 0,
            "total_dislikes": 0,
            "total_favorites": 0,
            "total_unfavorites": 0,
            "current_favorites": 0,
            "total_time_spent": 0,
            "avg_time_spent": 0,
            "events": []
        }

        if analytics_file.exists():
            with open(analytics_file, "r") as f:
                stored = json.load(f)
                analytics.update(stored)

        # Create event
        event = {
            "type": interaction_type,
            "timestamp": int(time.time()),
            "ip": request.client.host if request.client else "unknown",
            "user_agent": request.headers.get("user-agent", "unknown")
        }

        # Handle different interaction types
        if interaction_type == "like":
            analytics["total_likes"] += 1
            event["action"] = "liked"
        elif interaction_type == "dislike":
            analytics["total_dislikes"] += 1
            event["action"] = "not_interested"
        elif interaction_type == "favorite":
            analytics["total_favorites"] += 1
            analytics["current_favorites"] += 1
            event["action"] = "favorited"
        elif interaction_type == "unfavorite":
            analytics["total_unfavorites"] += 1
            analytics["current_favorites"] = max(0, analytics["current_favorites"] - 1)
            event["action"] = "unfavorited"
        elif interaction_type == "time_spent":
            if value and isinstance(value, (int, float)) and value > 0:
                analytics["total_time_spent"] += value
                event["duration"] = value

                # Calculate average time spent
                time_events = [e for e in analytics["events"] if e.get("type") == "time_spent"]
                total_events = len(time_events) + 1
                analytics["avg_time_spent"] = round(analytics["total_time_spent"] / total_events, 2)
        elif interaction_type == "view":
            analytics["total_views"] += 1
            event["action"] = "viewed"
        elif interaction_type in ["call", "sms", "email", "whatsapp"]:
            analytics["total_contacts"] += 1
            event["action"] = f"contacted_via_{interaction_type}"

        analytics["events"].append(event)
        analytics["updated_at"] = int(time.time())

        # Save analytics
        with open(analytics_file, "w") as f:
            json.dump(analytics, f, indent=2)

        return {
            "success": True,
            "message": "Interaction tracked successfully",
            "interaction_type": interaction_type,
            "ad_id": ad_id,
            "stats": {
                "likes": analytics["total_likes"],
                "dislikes": analytics["total_dislikes"],
                "favorites": analytics["total_favorites"],
                "current_favorites": analytics["current_favorites"],
                "avg_time_spent": analytics["avg_time_spent"]
            }
        }

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


@router.get("/track_interaction")
async def track_interaction_get(
    ad_id: str,
    event_type: str,
    request: Request
):
    """Track interaction via GET request (for simpler integrations)"""
    try:
        if not ad_id or not event_type:
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "Missing ad_id or event_type"}
            )

        # Reuse POST logic
        fake_request_data = {"interaction_type": event_type, "ad_id": ad_id}

        # Load analytics
        analytics_file = ANALYTICS_PATH / f"{ad_id}.json"
        analytics = {
            "ad_id": ad_id,
            "total_views": 0,
            "total_contacts": 0,
            "total_likes": 0,
            "total_dislikes": 0,
            "total_favorites": 0,
            "events": []
        }

        if analytics_file.exists():
            with open(analytics_file, "r") as f:
                stored = json.load(f)
                analytics.update(stored)

        # Track based on event type
        if event_type in ["call", "sms", "email", "whatsapp"]:
            analytics["total_contacts"] += 1
        elif event_type == "view":
            analytics["total_views"] += 1
        elif event_type == "like":
            analytics["total_likes"] += 1
        elif event_type == "dislike":
            analytics["total_dislikes"] += 1

        # Add event
        analytics["events"].append({
            "type": event_type,
            "timestamp": int(time.time()),
            "ip": request.client.host if request.client else "unknown"
        })
        analytics["updated_at"] = int(time.time())

        # Save
        with open(analytics_file, "w") as f:
            json.dump(analytics, f, indent=2)

        return {"success": True, "message": f"Tracked {event_type}"}

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

