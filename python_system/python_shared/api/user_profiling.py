"""
user_profiling.py - User Profiling API
Track and analyze user preferences and behavior
Converted from PHP to Python
"""

from fastapi import APIRouter, Request, Query
from fastapi.responses import JSONResponse
from pathlib import Path
from datetime import datetime, timedelta
import json
import time
import hashlib

router = APIRouter()

PROFILES_PATH = Path(__file__).parent.parent / "data" / "user_profiles"
PROFILES_PATH.mkdir(parents=True, exist_ok=True)


def get_device_id(request: Request) -> str:
    """Generate a unique device ID from request"""
    ip = request.client.host if request.client else "unknown"
    ua = request.headers.get("user-agent", "unknown")
    combined = f"{ip}:{ua}"
    return hashlib.md5(combined.encode()).hexdigest()[:16]


@router.post("/user_profile")
async def update_user_profile(request: Request):
    """Update user profile with interaction data"""
    try:
        data = await request.json()

        device_id = data.get("device_id") or get_device_id(request)
        ad_id = data.get("ad_id", "")
        action = data.get("action", "")  # view, like, favorite, contact, click
        category = data.get("category", "")
        duration = data.get("duration", 0)

        # Load or create profile
        profile_file = PROFILES_PATH / f"{device_id}.json"
        profile = {
            "device_id": device_id,
            "created_at": datetime.now().isoformat(),
            "interests": {},
            "category_affinity": {},
            "interaction_history": [],
            "total_views": 0,
            "total_likes": 0,
            "total_favorites": 0,
            "total_contacts": 0,
            "avg_view_duration": 0
        }

        if profile_file.exists():
            with open(profile_file, "r") as f:
                stored = json.load(f)
                profile.update(stored)

        # Update profile based on action
        timestamp = int(time.time())

        if action == "view":
            profile["total_views"] += 1
            if category:
                profile["category_affinity"][category] = profile["category_affinity"].get(category, 0) + 1
        elif action == "like":
            profile["total_likes"] += 1
            if category:
                profile["category_affinity"][category] = profile["category_affinity"].get(category, 0) + 3
        elif action == "favorite":
            profile["total_favorites"] += 1
            if category:
                profile["category_affinity"][category] = profile["category_affinity"].get(category, 0) + 5
        elif action == "contact":
            profile["total_contacts"] += 1
            if category:
                profile["category_affinity"][category] = profile["category_affinity"].get(category, 0) + 10

        # Track duration
        if duration > 0:
            durations = [h.get("duration", 0) for h in profile["interaction_history"] if h.get("duration")]
            durations.append(duration)
            profile["avg_view_duration"] = round(sum(durations) / len(durations), 2)

        # Add to history (keep last 100)
        profile["interaction_history"].append({
            "ad_id": ad_id,
            "action": action,
            "category": category,
            "duration": duration,
            "timestamp": timestamp
        })
        profile["interaction_history"] = profile["interaction_history"][-100:]

        # Update timestamps
        profile["last_active"] = datetime.now().isoformat()
        profile["updated_at"] = datetime.now().isoformat()

        # Save profile
        with open(profile_file, "w") as f:
            json.dump(profile, f, indent=2)

        return {
            "success": True,
            "device_id": device_id,
            "profile_updated": True
        }

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


@router.get("/user_profile")
async def get_user_profile(request: Request, device_id: str = None):
    """Get user profile and recommendations"""
    try:
        if not device_id:
            device_id = get_device_id(request)

        profile_file = PROFILES_PATH / f"{device_id}.json"

        if not profile_file.exists():
            return {
                "success": True,
                "profile": None,
                "message": "No profile found"
            }

        with open(profile_file, "r") as f:
            profile = json.load(f)

        # Generate category recommendations
        recommendations = []
        if profile.get("category_affinity"):
            sorted_categories = sorted(
                profile["category_affinity"].items(),
                key=lambda x: x[1],
                reverse=True
            )
            recommendations = [cat for cat, _ in sorted_categories[:5]]

        return {
            "success": True,
            "profile": {
                "device_id": profile["device_id"],
                "total_views": profile.get("total_views", 0),
                "total_likes": profile.get("total_likes", 0),
                "total_favorites": profile.get("total_favorites", 0),
                "avg_view_duration": profile.get("avg_view_duration", 0),
                "category_affinity": profile.get("category_affinity", {}),
                "last_active": profile.get("last_active")
            },
            "recommended_categories": recommendations
        }

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


@router.get("/user_profile/preferences")
async def get_preferences(request: Request, device_id: str = None):
    """Get user preferences for ad targeting"""
    try:
        if not device_id:
            device_id = get_device_id(request)

        profile_file = PROFILES_PATH / f"{device_id}.json"

        if not profile_file.exists():
            return {"success": True, "preferences": {}, "has_profile": False}

        with open(profile_file, "r") as f:
            profile = json.load(f)

        # Calculate preferences
        category_affinity = profile.get("category_affinity", {})
        total_affinity = sum(category_affinity.values()) or 1

        preferences = {
            cat: round(score / total_affinity, 3)
            for cat, score in category_affinity.items()
        }

        return {
            "success": True,
            "has_profile": True,
            "preferences": preferences,
            "engagement_score": min(100, profile.get("total_views", 0) + profile.get("total_likes", 0) * 5)
        }

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


@router.delete("/user_profile")
async def delete_user_profile(request: Request, device_id: str = None):
    """Delete user profile (GDPR compliance)"""
    try:
        if not device_id:
            device_id = get_device_id(request)

        profile_file = PROFILES_PATH / f"{device_id}.json"

        if profile_file.exists():
            profile_file.unlink()
            return {"success": True, "message": "Profile deleted"}
        else:
            return {"success": True, "message": "No profile found"}

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

