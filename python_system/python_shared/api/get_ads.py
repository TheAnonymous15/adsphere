"""
get_ads.py - Hybrid Database System
Fetches ads from SQLite database
Converted from PHP to Python
"""

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional
import json

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from models import Ad, Category, Company
from database import get_db

router = APIRouter()


@router.get("/ads")
async def get_ads(
    page: int = Query(1, ge=1),
    q: str = Query("", description="Search query"),
    category: str = Query("", description="Category filter"),
    company: str = Query("", description="Company filter"),
    sort: str = Query("date", description="Sort by: date, views, favs, ai"),
    pageSize: int = Query(12, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Fetch ads with filters and pagination"""
    try:
        # Build query
        query = db.query(Ad).filter(Ad.status == "active")

        # Company filter
        if company:
            query = query.filter(Ad.company_slug == company)

        # Search filter
        if q:
            search_term = f"%{q}%"
            query = query.filter(
                (Ad.title.ilike(search_term)) |
                (Ad.description.ilike(search_term))
            )

        # Category filter
        if category:
            query = query.filter(Ad.category_slug == category)

        # Sorting
        if sort == "views":
            query = query.order_by(desc(Ad.views_count), desc(Ad.created_at))
        elif sort == "favs":
            query = query.order_by(desc(Ad.favorites_count), desc(Ad.created_at))
        elif sort == "ai":
            query = query.order_by(desc(Ad.likes_count), desc(Ad.views_count), desc(Ad.created_at))
        else:  # date
            query = query.order_by(desc(Ad.created_at))

        # Get total count
        total = query.count()

        # Pagination
        offset = (page - 1) * pageSize
        ads = query.offset(offset).limit(pageSize).all()

        # Format ads for frontend
        formatted_ads = []
        for ad in ads:
            # Build media URLs
            media_url = ""
            media_files = []

            if ad.media_path:
                media_url = f"/company/data/{ad.media_path}"

            if ad.media_filename:
                # Check if it's a JSON array or single file
                if ad.media_filename.startswith('['):
                    try:
                        files = json.loads(ad.media_filename)
                    except:
                        files = [ad.media_filename]
                else:
                    files = [ad.media_filename]

                media_files = [
                    f"/company/data/{ad.category_slug}/{ad.company_slug}/{ad.ad_id}/{f}"
                    for f in files
                ]

            # Get category and company names
            cat = db.query(Category).filter(Category.category_slug == ad.category_slug).first()
            comp = db.query(Company).filter(Company.company_slug == ad.company_slug).first()

            formatted_ads.append({
                "ad_id": ad.ad_id,
                "title": ad.title,
                "description": ad.description or "",
                "category": ad.category_slug,
                "category_name": cat.category_name if cat else ad.category_slug.title(),
                "company": ad.company_slug,
                "company_name": comp.company_name if comp else ad.company_slug.title(),
                "media": media_files[0] if media_files else media_url,
                "media_files": media_files,
                "media_path": media_url,
                "media_type": ad.media_type or "image",
                "timestamp": str(ad.created_at) if ad.created_at else "",
                "views": ad.views_count or 0,
                "likes": ad.likes_count or 0,
                "favorites": ad.favorites_count or 0,
                "contacts": ad.contacts_count or 0,
                "contact": {
                    "phone": ad.contact_phone or "",
                    "sms": ad.contact_sms or "",
                    "email": ad.contact_email or "",
                    "whatsapp": ad.contact_whatsapp or ""
                }
            })

        return {
            "success": True,
            "ads": formatted_ads,
            "page": page,
            "pageSize": pageSize,
            "total": total,
            "totalPages": (total + pageSize - 1) // pageSize
        }

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "Failed to fetch ads",
                "message": str(e)
            }
        )


@router.get("/ads/{ad_id}")
async def get_single_ad(ad_id: str, db: Session = Depends(get_db)):
    """Fetch single ad by ID"""
    try:
        ad = db.query(Ad).filter(Ad.ad_id == ad_id).first()

        if not ad:
            return JSONResponse(
                status_code=404,
                content={"success": False, "error": "Ad not found"}
            )

        media_url = f"/company/data/{ad.media_path}" if ad.media_path else ""

        return {
            "success": True,
            "ad": {
                "ad_id": ad.ad_id,
                "title": ad.title,
                "description": ad.description or "",
                "category": ad.category_slug,
                "company": ad.company_slug,
                "media_path": media_url,
                "media_type": ad.media_type or "image",
                "views": ad.views_count or 0,
                "likes": ad.likes_count or 0,
                "favorites": ad.favorites_count or 0,
                "contacts": ad.contacts_count or 0,
                "contact": {
                    "phone": ad.contact_phone or "",
                    "sms": ad.contact_sms or "",
                    "email": ad.contact_email or "",
                    "whatsapp": ad.contact_whatsapp or ""
                },
                "created_at": str(ad.created_at) if ad.created_at else ""
            }
        }

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

