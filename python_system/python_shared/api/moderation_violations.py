"""
moderation_violations.py - Moderation Violations API
Get ads flagged by the moderation system
Converted from PHP to Python
"""

from fastapi import APIRouter, Query, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pathlib import Path
import json
import time

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from models import Ad
from database import get_db

router = APIRouter()

VIOLATIONS_PATH = Path(__file__).parent.parent / "data" / "moderation_violations"
VIOLATIONS_PATH.mkdir(parents=True, exist_ok=True)


@router.get("/moderation_violations")
async def get_violations(
    status: str = Query(None, description="Filter by status: pending, reviewed, resolved"),
    severity: str = Query(None, description="Filter by severity: low, medium, high, critical"),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """Get moderation violations"""
    try:
        violations = []

        # Load violations from files
        for file_path in VIOLATIONS_PATH.glob("*.json"):
            try:
                with open(file_path, "r") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        violations.extend(data)
                    else:
                        violations.append(data)
            except Exception:
                continue

        # Filter by status
        if status:
            violations = [v for v in violations if v.get("status") == status]

        # Filter by severity
        if severity:
            violations = [v for v in violations if v.get("severity") == severity]

        # Sort by timestamp (newest first)
        violations.sort(key=lambda x: x.get("timestamp", 0), reverse=True)

        # Limit
        violations = violations[:limit]

        # Count by status
        stats = {
            "pending": sum(1 for v in violations if v.get("status") == "pending"),
            "reviewed": sum(1 for v in violations if v.get("status") == "reviewed"),
            "resolved": sum(1 for v in violations if v.get("status") == "resolved")
        }

        return {
            "success": True,
            "violations": violations,
            "stats": stats,
            "total": len(violations)
        }

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


@router.post("/moderation_violations")
async def create_violation(request):
    """Create a new moderation violation record"""
    try:
        data = await request.json()

        ad_id = data.get("ad_id", "")
        violation_type = data.get("violation_type", "")
        severity = data.get("severity", "medium")
        description = data.get("description", "")
        detected_by = data.get("detected_by", "system")

        if not ad_id or not violation_type:
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "Missing ad_id or violation_type"}
            )

        # Create violation record
        violation = {
            "id": f"VIO-{int(time.time())}-{ad_id[:8]}",
            "ad_id": ad_id,
            "violation_type": violation_type,
            "severity": severity,
            "description": description,
            "detected_by": detected_by,
            "status": "pending",
            "timestamp": int(time.time()),
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }

        # Save to daily file
        today = time.strftime("%Y-%m-%d")
        file_path = VIOLATIONS_PATH / f"{today}.json"

        daily_violations = []
        if file_path.exists():
            with open(file_path, "r") as f:
                daily_violations = json.load(f)

        daily_violations.append(violation)

        with open(file_path, "w") as f:
            json.dump(daily_violations, f, indent=2)

        return {
            "success": True,
            "message": "Violation recorded",
            "violation_id": violation["id"]
        }

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


@router.post("/moderation_violations/{violation_id}/resolve")
async def resolve_violation(violation_id: str, request):
    """Resolve a moderation violation"""
    try:
        data = await request.json()
        action = data.get("action", "")  # approve, block, delete
        notes = data.get("notes", "")

        # Find and update violation
        for file_path in VIOLATIONS_PATH.glob("*.json"):
            try:
                with open(file_path, "r") as f:
                    violations = json.load(f)

                for v in violations:
                    if v.get("id") == violation_id:
                        v["status"] = "resolved"
                        v["resolution_action"] = action
                        v["resolution_notes"] = notes
                        v["resolved_at"] = time.strftime("%Y-%m-%d %H:%M:%S")

                        with open(file_path, "w") as f:
                            json.dump(violations, f, indent=2)

                        return {
                            "success": True,
                            "message": "Violation resolved",
                            "violation_id": violation_id,
                            "action": action
                        }

            except Exception:
                continue

        return JSONResponse(
            status_code=404,
            content={"success": False, "error": "Violation not found"}
        )

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

