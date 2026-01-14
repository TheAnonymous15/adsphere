"""
schedule_ad.py - Ad Scheduling API
Set start and end dates for ads
Converted from PHP to Python
"""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from datetime import datetime
from pathlib import Path
import json
import time

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from models import Ad
from database import get_db

router = APIRouter()

DATA_PATH = Path(__file__).parent.parent / "companies" / "data"


@router.post("/schedule_ad")
async def schedule_ad(request: Request, db: Session = Depends(get_db)):
    """Schedule an ad - matches PHP logic exactly"""
    try:
        data = await request.json()

        ad_id = data.get("ad_id", "")
        start_date = data.get("start_date")  # Can be None
        end_date = data.get("end_date")  # Can be None
        auto_renew = data.get("auto_renew", False)

        if not ad_id:
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "No ad ID provided"}
            )

        # Validate dates (matching PHP strtotime behavior)
        start_timestamp = None
        end_timestamp = None

        if start_date:
            try:
                start_timestamp = int(datetime.strptime(start_date, "%Y-%m-%d").timestamp())
            except ValueError:
                try:
                    start_timestamp = int(datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S").timestamp())
                except ValueError:
                    return JSONResponse(
                        status_code=400,
                        content={"success": False, "message": "Invalid start date format"}
                    )

        if end_date:
            try:
                end_timestamp = int(datetime.strptime(end_date, "%Y-%m-%d").timestamp())
            except ValueError:
                try:
                    end_timestamp = int(datetime.strptime(end_date, "%Y-%m-%d %H:%M:%S").timestamp())
                except ValueError:
                    return JSONResponse(
                        status_code=400,
                        content={"success": False, "message": "Invalid end date format"}
                    )

        # Find ad in database
        ad = db.query(Ad).filter(Ad.ad_id == ad_id).first()

        if ad:
            # Update via database
            now = int(time.time())

            # Auto-set status based on dates (matching PHP logic)
            if start_timestamp and start_timestamp > now:
                ad.status = "scheduled"
            elif end_timestamp and end_timestamp < now:
                ad.status = "expired"
            else:
                ad.status = "active"

            ad.scheduled_at = datetime.fromtimestamp(start_timestamp) if start_timestamp else None
            ad.updated_at = datetime.now()
            db.commit()

            schedule_info = {
                "start_date": start_timestamp,
                "end_date": end_timestamp,
                "auto_renew": auto_renew,
                "updated_at": int(time.time())
            }

            return {
                "success": True,
                "message": "Schedule updated successfully",
                "ad_id": ad_id,
                "schedule": schedule_info,
                "status": ad.status
            }

        # Also try to update meta.json file (matching PHP file-based approach)
        found = False
        for category_dir in DATA_PATH.iterdir():
            if not category_dir.is_dir():
                continue
            for company_dir in category_dir.iterdir():
                if not company_dir.is_dir():
                    continue
                ad_path = company_dir / ad_id
                if ad_path.is_dir():
                    meta_file = ad_path / "meta.json"
                    if meta_file.exists():
                        with open(meta_file, "r") as f:
                            meta = json.load(f)

                        # Update scheduling (matching PHP logic)
                        now = int(time.time())
                        meta["schedule"] = {
                            "start_date": start_timestamp,
                            "end_date": end_timestamp,
                            "auto_renew": auto_renew,
                            "updated_at": int(time.time())
                        }

                        # Auto-set status based on dates
                        if start_timestamp and start_timestamp > now:
                            meta["status"] = "scheduled"
                        elif end_timestamp and end_timestamp < now:
                            meta["status"] = "expired"
                        else:
                            meta["status"] = "active"

                        with open(meta_file, "w") as f:
                            json.dump(meta, f, indent=2)

                        return {
                            "success": True,
                            "message": "Schedule updated successfully",
                            "ad_id": ad_id,
                            "schedule": meta["schedule"],
                            "status": meta["status"]
                        }

        return JSONResponse(
            status_code=404,
            content={"success": False, "message": "Ad not found or unauthorized"}
        )

    except Exception as e:
        if db:
            db.rollback()
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


@router.post("/unschedule_ad")
async def unschedule_ad(request: Request, db: Session = Depends(get_db)):
    """Remove scheduling from an ad"""
    try:
        data = await request.json()
        ad_id = data.get("ad_id", "")

        if not ad_id:
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "Missing ad_id"}
            )

        ad = db.query(Ad).filter(Ad.ad_id == ad_id).first()

        if not ad:
            return JSONResponse(
                status_code=404,
                content={"success": False, "error": "Ad not found"}
            )

        ad.status = "draft"
        ad.scheduled_at = None
        ad.updated_at = datetime.now()

        db.commit()

        return {
            "success": True,
            "message": "Ad unscheduled",
            "ad_id": ad_id
        }

    except Exception as e:
        db.rollback()
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


@router.get("/scheduled_ads")
async def get_scheduled_ads(company: str = None, db: Session = Depends(get_db)):
    """Get all scheduled ads"""
    try:
        query = db.query(Ad).filter(Ad.status == "scheduled")

        if company:
            query = query.filter(Ad.company_slug == company)

        ads = query.order_by(Ad.scheduled_at).all()

        return {
            "success": True,
            "scheduled_ads": [
                {
                    "ad_id": ad.ad_id,
                    "title": ad.title,
                    "scheduled_at": ad.scheduled_at.isoformat() if ad.scheduled_at else None,
                    "category": ad.category_slug,
                    "company": ad.company_slug
                }
                for ad in ads
            ],
            "total": len(ads)
        }

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )
