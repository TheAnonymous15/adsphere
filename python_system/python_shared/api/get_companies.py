"""
get_companies.py - Get Companies API
Fetches all companies from database
Converted from PHP to Python
"""

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
import time

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from models import Company, Ad
from database import get_db

router = APIRouter()


@router.get("/companies")
async def get_companies(db: Session = Depends(get_db)):
    """Fetch all companies with stats"""
    try:
        # Fetch companies with aggregated stats
        companies = db.query(
            Company,
            func.count(Ad.ad_id).label("total_ads"),
            func.coalesce(func.sum(Ad.views_count), 0).label("total_views"),
            func.coalesce(func.sum(Ad.likes_count), 0).label("total_likes"),
            func.coalesce(func.sum(Ad.favorites_count), 0).label("total_favorites")
        ).outerjoin(
            Ad, Company.company_slug == Ad.company_slug
        ).group_by(Company.company_slug).order_by(desc(Company.created_at)).all()

        # Calculate statistics
        stats = {
            "total": len(companies),
            "verified": 0,
            "inactive": 0,
            "suspended": 0,
            "blocked": 0,
            "active": 0
        }

        formatted_companies = []
        for comp, total_ads, total_views, total_likes, total_favorites in companies:
            status = comp.status or "active"

            # Update stats
            if status == "verified":
                stats["verified"] += 1
            elif status == "inactive":
                stats["inactive"] += 1
            elif status == "suspended":
                stats["suspended"] += 1
            elif status in ["blocked", "banned"]:
                stats["blocked"] += 1
            else:
                stats["active"] += 1

            formatted_companies.append({
                "company_slug": comp.company_slug,
                "company_name": comp.company_name,
                "email": comp.email or "",
                "phone": comp.phone or "",
                "status": status,
                "created_at": str(comp.created_at) if comp.created_at else "",
                "total_ads": total_ads,
                "total_views": int(total_views),
                "total_likes": int(total_likes),
                "total_favorites": int(total_favorites)
            })

        return {
            "success": True,
            "companies": formatted_companies,
            "stats": stats,
            "timestamp": int(time.time())
        }

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "Failed to fetch companies",
                "message": str(e)
            }
        )


@router.get("/companies/{company_slug}")
async def get_company(company_slug: str, db: Session = Depends(get_db)):
    """Fetch single company by slug"""
    try:
        company = db.query(Company).filter(Company.company_slug == company_slug).first()

        if not company:
            return JSONResponse(
                status_code=404,
                content={"success": False, "error": "Company not found"}
            )

        # Get company stats
        stats = db.query(
            func.count(Ad.ad_id).label("total_ads"),
            func.coalesce(func.sum(Ad.views_count), 0).label("total_views"),
            func.coalesce(func.sum(Ad.likes_count), 0).label("total_likes")
        ).filter(Ad.company_slug == company_slug).first()

        return {
            "success": True,
            "company": {
                "company_slug": company.company_slug,
                "company_name": company.company_name,
                "email": company.email or "",
                "phone": company.phone or "",
                "status": company.status or "active",
                "created_at": str(company.created_at) if company.created_at else "",
                "total_ads": stats[0] if stats else 0,
                "total_views": int(stats[1]) if stats else 0,
                "total_likes": int(stats[2]) if stats else 0
            }
        }

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

