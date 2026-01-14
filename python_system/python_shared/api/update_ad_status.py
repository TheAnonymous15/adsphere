"""
update_ad_status.py - Update Ad Status API
Update the status of an ad
Converted from PHP to Python
"""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from datetime import datetime

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from models import Ad
from database import get_db

router = APIRouter()


@router.post("/update_ad_status")
async def update_ad_status(request: Request, db: Session = Depends(get_db)):
    """Update ad status"""
    try:
        data = await request.json()

        ad_id = data.get("ad_id", "")
        new_status = data.get("status", "")

        if not ad_id or not new_status:
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "Missing ad_id or status"}
            )

        # Validate status
        valid_statuses = ["active", "paused", "blocked", "scheduled", "expired", "review", "draft"]
        if new_status not in valid_statuses:
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": f"Invalid status. Must be one of: {', '.join(valid_statuses)}"}
            )

        # Find and update ad
        ad = db.query(Ad).filter(Ad.ad_id == ad_id).first()

        if not ad:
            return JSONResponse(
                status_code=404,
                content={"success": False, "error": "Ad not found"}
            )

        old_status = ad.status
        ad.status = new_status
        ad.updated_at = datetime.now()

        db.commit()

        return {
            "success": True,
            "message": f"Ad status updated from '{old_status}' to '{new_status}'",
            "ad_id": ad_id,
            "old_status": old_status,
            "new_status": new_status
        }

    except Exception as e:
        db.rollback()
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


@router.post("/update_ad_status/{ad_id}")
async def update_ad_status_path(ad_id: str, status: str, db: Session = Depends(get_db)):
    """Update ad status via path parameters"""
    try:
        valid_statuses = ["active", "paused", "blocked", "scheduled", "expired", "review", "draft"]
        if status not in valid_statuses:
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": f"Invalid status"}
            )

        ad = db.query(Ad).filter(Ad.ad_id == ad_id).first()

        if not ad:
            return JSONResponse(
                status_code=404,
                content={"success": False, "error": "Ad not found"}
            )

        old_status = ad.status
        ad.status = status
        ad.updated_at = datetime.now()

        db.commit()

        return {
            "success": True,
            "ad_id": ad_id,
            "old_status": old_status,
            "new_status": status
        }

    except Exception as e:
        db.rollback()
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

