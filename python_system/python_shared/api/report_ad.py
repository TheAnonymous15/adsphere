"""
report_ad.py - Report Ad API Endpoint
Records when a user reports an ad for review
Converted from PHP to Python
"""

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pathlib import Path
from datetime import datetime
import json
import re

router = APIRouter()

# Storage path
REPORTED_ADS_PATH = Path(__file__).parent.parent / "data" / "reported_ads"
REPORTED_ADS_PATH.mkdir(parents=True, exist_ok=True)


@router.post("/report_ad")
async def report_ad(request: Request):
    """Report an ad for review"""
    try:
        data = await request.json()

        ad_id = data.get("ad_id", "")
        if not ad_id:
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "Missing ad_id"}
            )

        reason = data.get("reason", "not_specified")
        description = data.get("description", "")[:1000]
        device_id = data.get("device_id", "unknown")

        # Sanitize
        ad_id = re.sub(r'[^a-zA-Z0-9\-_]', '', ad_id)

        # Create report record
        report_record = {
            "ad_id": ad_id,
            "reason": reason,
            "description": description,
            "device_id": device_id,
            "ip_address": request.client.host if request.client else "unknown",
            "user_agent": request.headers.get("user-agent", "unknown"),
            "timestamp": int(datetime.now().timestamp()),
            "created_at": datetime.now().isoformat(),
            "status": "pending"
        }

        # Save to daily file
        today = datetime.now().strftime("%Y-%m-%d")
        file_path = REPORTED_ADS_PATH / f"{today}.json"

        daily_reports = []
        if file_path.exists():
            with open(file_path, "r") as f:
                daily_reports = json.load(f)

        daily_reports.append(report_record)

        with open(file_path, "w") as f:
            json.dump(daily_reports, f, indent=2)

        return {
            "success": True,
            "message": "Ad reported successfully",
            "ad_id": ad_id
        }

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


@router.get("/reported_ads")
async def get_reported_ads(date: str = None, status: str = None):
    """Get reported ads"""
    try:
        reports = []

        if date:
            file_path = REPORTED_ADS_PATH / f"{date}.json"
            if file_path.exists():
                with open(file_path, "r") as f:
                    reports = json.load(f)
        else:
            for file_path in REPORTED_ADS_PATH.glob("*.json"):
                with open(file_path, "r") as f:
                    reports.extend(json.load(f))

        # Filter by status if specified
        if status:
            reports = [r for r in reports if r.get("status") == status]

        return {
            "success": True,
            "reports": reports,
            "total": len(reports)
        }

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

