"""
user_feedback_stats.py - User Feedback Statistics API
Get statistics on user feedback (blocks, reports)
Converted from PHP to Python
"""

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pathlib import Path
import json

router = APIRouter()

BLOCKED_ADS_PATH = Path(__file__).parent.parent / "data" / "blocked_ads"
REPORTED_ADS_PATH = Path(__file__).parent.parent / "data" / "reported_ads"


@router.get("/user_feedback_stats")
async def user_feedback_stats():
    """Get user feedback statistics (blocks, reports)"""
    try:
        # Count blocked ads
        blocked_count = 0
        block_reasons = {}

        if BLOCKED_ADS_PATH.exists():
            for file_path in BLOCKED_ADS_PATH.glob("*.json"):
                try:
                    with open(file_path, "r") as f:
                        data = json.load(f)
                        blocked_count += len(data)

                        for block in data:
                            reason = block.get("reason", "not_specified")
                            block_reasons[reason] = block_reasons.get(reason, 0) + 1
                except Exception:
                    continue

        # Count reported ads
        reported_count = 0
        report_reasons = {}
        pending_reports = 0

        if REPORTED_ADS_PATH.exists():
            for file_path in REPORTED_ADS_PATH.glob("*.json"):
                try:
                    with open(file_path, "r") as f:
                        data = json.load(f)
                        reported_count += len(data)

                        for report in data:
                            reason = report.get("reason", "not_specified")
                            report_reasons[reason] = report_reasons.get(reason, 0) + 1

                            if report.get("status") == "pending":
                                pending_reports += 1
                except Exception:
                    continue

        return {
            "success": True,
            "stats": {
                "total_blocks": blocked_count,
                "total_reports": reported_count,
                "pending_reports": pending_reports,
                "block_reasons": block_reasons,
                "report_reasons": report_reasons
            }
        }

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

