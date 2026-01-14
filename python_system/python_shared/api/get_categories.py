"""
get_categories.py - Hybrid Database System
Fetches categories from SQLite database
Converted from PHP to Python
"""

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import func

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from models import Category, Ad, Company
from database import get_db

router = APIRouter()


@router.get("/categories")
async def get_categories(db: Session = Depends(get_db)):
    """Fetch all categories with stats - matches PHP logic exactly"""
    try:
        # Subquery to count companies per category (matching PHP query)
        # In PHP: COUNT(DISTINCT cc.company_slug) as company_count
        # Since we may not have company_categories table, count from ads
        company_subquery = db.query(
            Ad.category_slug,
            func.count(func.distinct(Ad.company_slug)).label("company_count")
        ).group_by(Ad.category_slug).subquery()

        # Get categories with ad counts and company counts (matching PHP query)
        categories = db.query(
            Category,
            func.count(Ad.ad_id).label("ad_count"),
            func.coalesce(company_subquery.c.company_count, 0).label("company_count")
        ).outerjoin(
            Ad,
            (Category.category_slug == Ad.category_slug) & (Ad.status == "active")
        ).outerjoin(
            company_subquery,
            Category.category_slug == company_subquery.c.category_slug
        ).group_by(Category.category_slug).order_by(Category.category_name).all()

        formatted_categories = []
        for cat, ad_count, company_count in categories:
            formatted_categories.append({
                "slug": cat.category_slug,
                "name": cat.category_name,
                "description": cat.description or "",
                "company_count": int(company_count or 0),
                "ad_count": int(ad_count or 0)
            })

        return {
            "success": True,
            "categories": formatted_categories,
            "total": len(formatted_categories)
        }

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "Failed to fetch categories",
                "message": str(e)
            }
        )


@router.get("/categories/{category_slug}")
async def get_category(category_slug: str, db: Session = Depends(get_db)):
    """Fetch single category by slug"""
    try:
        category = db.query(Category).filter(Category.category_slug == category_slug).first()

        if not category:
            return JSONResponse(
                status_code=404,
                content={"success": False, "error": "Category not found"}
            )

        # Count ads in this category
        ad_count = db.query(func.count(Ad.ad_id)).filter(
            Ad.category_slug == category_slug,
            Ad.status == "active"
        ).scalar()

        # Count companies in this category
        company_count = db.query(func.count(func.distinct(Ad.company_slug))).filter(
            Ad.category_slug == category_slug
        ).scalar()

        return {
            "success": True,
            "category": {
                "slug": category.category_slug,
                "name": category.category_name,
                "description": category.description or "",
                "company_count": int(company_count or 0),
                "ad_count": int(ad_count or 0)
            }
        }

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )
