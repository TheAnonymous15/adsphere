"""
block_ad.py - Block Ad API Endpoint
Records when a user blocks an ad from appearing in their feed
Converted from PHP to Python
"""

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pathlib import Path
from datetime import datetime
import json
import re

router = APIRouter()

# Storage paths
BLOCKED_ADS_PATH = Path(__file__).parent.parent / "data" / "blocked_ads"
BLOCKED_ADS_PATH.mkdir(parents=True, exist_ok=True)


@router.post("/block_ad")
async def block_ad(request: Request):
    """Block an ad from appearing in user's feed"""
    try:
        data = await request.json()

        ad_id = data.get("ad_id", "")
        if not ad_id:
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "Missing ad_id"}
            )

        reason = data.get("reason", "not_specified")
        comment = data.get("comment", "")[:500]  # Limit to 500 chars
        device_id = data.get("device_id", "unknown")
        timestamp = data.get("timestamp", int(datetime.now().timestamp() * 1000))

        # Sanitize inputs
        ad_id = re.sub(r'[^a-zA-Z0-9\-_]', '', ad_id)
        reason = re.sub(r'[^a-zA-Z0-9_]', '', reason)
        device_id = re.sub(r'[^a-zA-Z0-9\-_]', '', device_id)

        # Create block record
        block_record = {
            "ad_id": ad_id,
            "reason": reason,
            "comment": comment,
            "device_id": device_id,
            "ip_address": request.client.host if request.client else "unknown",
            "user_agent": request.headers.get("user-agent", "unknown"),
            "timestamp": timestamp,
            "created_at": datetime.now().isoformat()
        }

        # Save to file system (daily files)
        today = datetime.now().strftime("%Y-%m-%d")
        file_path = BLOCKED_ADS_PATH / f"{today}.json"

        daily_blocks = []
        if file_path.exists():
            with open(file_path, "r") as f:
                daily_blocks = json.load(f)

        daily_blocks.append(block_record)

        with open(file_path, "w") as f:
            json.dump(daily_blocks, f, indent=2)

        # Try to update database as well
        try:
            import sys
            sys.path.insert(0, str(Path(__file__).parent.parent))
            from database import SessionLocal
            from models import Ad

            db = SessionLocal()
            ad = db.query(Ad).filter(Ad.ad_id == ad_id).first()
            if ad:
                ad.blocks_count = (ad.blocks_count or 0) + 1
                db.commit()
            db.close()
        except Exception:
            pass  # Database update is optional

        return {
            "success": True,
            "message": "Ad blocked successfully",
            "ad_id": ad_id
        }

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


@router.get("/blocked_ads")
async def get_blocked_ads(date: str = None):
    """Get blocked ads for a specific date or all"""
    try:
        blocked_ads = []

        if date:
            # Get specific date
            file_path = BLOCKED_ADS_PATH / f"{date}.json"
            if file_path.exists():
                with open(file_path, "r") as f:
                    blocked_ads = json.load(f)
        else:
            # Get all blocked ads
            for file_path in BLOCKED_ADS_PATH.glob("*.json"):
                with open(file_path, "r") as f:
                    blocked_ads.extend(json.load(f))

        return {
            "success": True,
            "blocked_ads": blocked_ads,
            "total": len(blocked_ads)
        }

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

