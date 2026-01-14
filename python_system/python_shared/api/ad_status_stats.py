"""
Ad Status Statistics API
Returns counts of ads by status
Converted from PHP to Python
"""

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, case, desc
import time

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from models import Ad
from database import get_db

router = APIRouter()


@router.get("/ad_status_stats")
async def ad_status_stats(company: str = None, db: Session = Depends(get_db)):
    """Get ad status breakdown - matches PHP logic exactly"""
    try:
        # Build base query
        query = db.query(
            func.count(Ad.ad_id).label('total'),
            func.sum(case((Ad.status == 'active', 1), else_=0)).label('active'),
            func.sum(case((Ad.status == 'inactive', 1), else_=0)).label('inactive'),
            func.sum(case((Ad.status == 'scheduled', 1), else_=0)).label('scheduled'),
            func.sum(case((Ad.status == 'expired', 1), else_=0)).label('expired')
        )

        if company:
            query = query.filter(Ad.company_slug == company)

        stats = query.first()

        # Convert to integers (matching PHP behavior)
        result = {
            "total": int(stats.total or 0),
            "active": int(stats.active or 0),
            "inactive": int(stats.inactive or 0),
            "scheduled": int(stats.scheduled or 0),
            "expired": int(stats.expired or 0)
        }

        # Calculate percentages (matching PHP logic)
        total = result["total"] if result["total"] > 0 else 1
        result["percentages"] = {
            "active": round((result["active"] / total) * 100, 1),
            "inactive": round((result["inactive"] / total) * 100, 1),
            "scheduled": round((result["scheduled"] / total) * 100, 1),
            "expired": round((result["expired"] / total) * 100, 1)
        }

        # Get recent status changes (matching PHP query)
        recent_query = db.query(
            Ad.ad_id,
            Ad.status,
            Ad.updated_at
        )
        if company:
            recent_query = recent_query.filter(Ad.company_slug == company)

        recent_changes = recent_query.order_by(desc(Ad.updated_at)).limit(5).all()

        recent_changes_list = [
            {
                "ad_id": change.ad_id,
                "status": change.status,
                "updated_at": str(change.updated_at) if change.updated_at else None
            }
            for change in recent_changes
        ]

        return {
            "success": True,
            "stats": result,
            "recent_changes": recent_changes_list,
            "timestamp": int(time.time())
        }

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "Failed to fetch ad status statistics",
                "message": str(e)
            }
        )
