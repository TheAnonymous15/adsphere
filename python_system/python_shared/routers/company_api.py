"""
============================================================================
COMPANY SERVICE - API Router
============================================================================
Handles all /api/* requests for the company portal
Equivalent to: python_company/api/router.php
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta, timezone
from typing import Optional

# Import from parent directory
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import get_db
from models import Ad, Company, Category, AdView, Interaction, Favorite, get_current_timestamp
from auth import get_current_company

# Create router
router = APIRouter(prefix="/api", tags=["Company API"])

# Public APIs that don't require authentication
PUBLIC_APIS = ["auth", "login", "register", "health"]


# ============================================================================
# GET /api/get_ads - Get company ads (filtered by company)
# ============================================================================
@router.get("/get_ads")
async def get_ads(
    page: int = 1,
    limit: int = 20,
    status: Optional[str] = None,
    category: Optional[str] = None,
    search: Optional[str] = None,
    sort: str = "newest",
    db: Session = Depends(get_db),
    current_company: dict = Depends(get_current_company)
):
    """Get company ads - filtered by authenticated company for security"""
    company_slug = current_company.get("sub")

    # Build query - FORCE company filter for security
    query = db.query(Ad).filter(Ad.company_slug == company_slug)

    # Apply filters
    if status:
        query = query.filter(Ad.status == status)
    if category:
        query = query.filter(Ad.category_slug == category)
    if search:
        query = query.filter(
            (Ad.title.ilike(f"%{search}%")) |
            (Ad.description.ilike(f"%{search}%"))
        )

    # Apply sorting
    if sort == "newest":
        query = query.order_by(Ad.created_at.desc())
    elif sort == "oldest":
        query = query.order_by(Ad.created_at.asc())
    elif sort == "most_viewed":
        query = query.order_by(Ad.views_count.desc())
    elif sort == "most_liked":
        query = query.order_by(Ad.likes_count.desc())
    elif sort == "most_favorites":
        query = query.order_by(Ad.favorites_count.desc())

    # Get total count
    total = query.count()

    # Paginate
    offset = (page - 1) * limit
    ads = query.offset(offset).limit(limit).all()

    return {
        "success": True,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit,
        "ads": [
            {
                "id": ad.ad_id,
                "title": ad.title,
                "description": ad.description,
                "category": ad.category_slug,
                "status": ad.status,
                "views": ad.views_count or 0,
                "likes": ad.likes_count or 0,
                "dislikes": ad.dislikes_count or 0,
                "favorites": ad.favorites_count or 0,
                "contacts": ad.contacts_count or 0,
                "media_type": ad.media_type,
                "media_path": ad.media_path,
                "created_at": str(ad.created_at) if ad.created_at else None,
                "updated_at": str(ad.updated_at) if ad.updated_at else None
            }
            for ad in ads
        ]
    }


# ============================================================================
# GET /api/dashboard_stats - Dashboard statistics
# ============================================================================
@router.get("/dashboard_stats")
async def dashboard_stats(
    db: Session = Depends(get_db),
    current_company: dict = Depends(get_current_company)
):
    """Get dashboard statistics for company"""
    company_slug = current_company.get("sub")

    # Get ads for this company
    company_ads = db.query(Ad).filter(Ad.company_slug == company_slug)

    total_ads = company_ads.count()
    active_ads = company_ads.filter(Ad.status == "active").count()
    inactive_ads = company_ads.filter(Ad.status == "inactive").count()
    scheduled_ads = company_ads.filter(Ad.status == "scheduled").count()

    # Aggregate metrics
    total_views = db.query(func.sum(Ad.views_count)).filter(
        Ad.company_slug == company_slug
    ).scalar() or 0

    total_likes = db.query(func.sum(Ad.likes_count)).filter(
        Ad.company_slug == company_slug
    ).scalar() or 0

    total_favorites = db.query(func.sum(Ad.favorites_count)).filter(
        Ad.company_slug == company_slug
    ).scalar() or 0

    total_contacts = db.query(func.sum(Ad.contacts_count)).filter(
        Ad.company_slug == company_slug
    ).scalar() or 0

    return {
        "success": True,
        "stats": {
            "total_ads": total_ads,
            "active_ads": active_ads,
            "inactive_ads": inactive_ads,
            "scheduled_ads": scheduled_ads,
            "total_views": int(total_views),
            "total_likes": int(total_likes),
            "total_favorites": int(total_favorites),
            "total_contacts": int(total_contacts)
        }
    }


# ============================================================================
# GET /api/live_activity - Live activity feed
# ============================================================================
@router.get("/live_activity")
async def live_activity(
    limit: int = 20,
    db: Session = Depends(get_db),
    current_company: dict = Depends(get_current_company)
):
    """Get live activity feed for company ads"""
    company_slug = current_company.get("sub")

    # Get recent interactions for company's ads
    recent_views = db.query(AdView).join(Ad).filter(
        Ad.company_slug == company_slug
    ).order_by(AdView.viewed_at.desc()).limit(limit).all()

    activities = []
    for view in recent_views:
        activities.append({
            "type": "view",
            "ad_id": view.ad_id,
            "timestamp": str(view.viewed_at),
            "device": view.device_type,
            "location": view.location
        })

    return {
        "success": True,
        "activities": activities,
        "count": len(activities)
    }


# ============================================================================
# GET /api/contact_analytics - Contact analytics
# ============================================================================
@router.get("/contact_analytics")
async def contact_analytics(
    days: int = 30,
    db: Session = Depends(get_db),
    current_company: dict = Depends(get_current_company)
):
    """Get contact analytics for company"""
    company_slug = current_company.get("sub")

    # Get contact interactions
    since = datetime.now(timezone.utc) - timedelta(days=days)

    contacts = db.query(Interaction).join(Ad).filter(
        Ad.company_slug == company_slug,
        Interaction.event_type.in_(["call", "sms", "email", "whatsapp"]),
        Interaction.created_at >= since
    ).all()

    # Aggregate by method
    methods = {"call": 0, "sms": 0, "email": 0, "whatsapp": 0}
    for contact in contacts:
        if contact.event_type in methods:
            methods[contact.event_type] += 1

    return {
        "success": True,
        "period_days": days,
        "contact_methods": methods,
        "total_contacts": sum(methods.values())
    }


# ============================================================================
# GET /api/get_analytics - Get ad analytics
# ============================================================================
@router.get("/get_analytics")
@router.get("/analytics")
async def get_analytics(
    ad_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_company: dict = Depends(get_current_company)
):
    """Get analytics for specific ad or all ads"""
    company_slug = current_company.get("sub")

    if ad_id:
        # Get specific ad analytics
        ad = db.query(Ad).filter(
            Ad.ad_id == ad_id,
            Ad.company_slug == company_slug
        ).first()

        if not ad:
            raise HTTPException(status_code=404, detail="Ad not found")

        return {
            "success": True,
            "ad_id": ad.ad_id,
            "title": ad.title,
            "analytics": {
                "views": ad.views_count or 0,
                "likes": ad.likes_count or 0,
                "dislikes": ad.dislikes_count or 0,
                "favorites": ad.favorites_count or 0,
                "contacts": ad.contacts_count or 0
            }
        }
    else:
        # Get all ads analytics
        ads = db.query(Ad).filter(Ad.company_slug == company_slug).all()

        return {
            "success": True,
            "total_ads": len(ads),
            "ads": [
                {
                    "ad_id": ad.ad_id,
                    "title": ad.title,
                    "views": ad.views_count or 0,
                    "likes": ad.likes_count or 0,
                    "favorites": ad.favorites_count or 0,
                    "contacts": ad.contacts_count or 0
                }
                for ad in ads
            ]
        }


# ============================================================================
# POST /api/delete_ad - Delete an ad
# ============================================================================
@router.post("/delete_ad")
async def delete_ad(
    request: Request,
    db: Session = Depends(get_db),
    current_company: dict = Depends(get_current_company)
):
    """Delete an ad"""
    company_slug = current_company.get("sub")

    # Get request data
    try:
        data = await request.json()
    except:
        form = await request.form()
        data = dict(form)

    ad_id = data.get("ad_id")
    if not ad_id:
        raise HTTPException(status_code=400, detail="ad_id is required")

    # Find and verify ownership
    ad = db.query(Ad).filter(
        Ad.ad_id == ad_id,
        Ad.company_slug == company_slug
    ).first()

    if not ad:
        raise HTTPException(status_code=404, detail="Ad not found or not owned by you")

    # Delete ad
    db.delete(ad)
    db.commit()

    return {
        "success": True,
        "message": "Ad deleted successfully",
        "ad_id": ad_id
    }


# ============================================================================
# POST /api/update_ad_status - Update ad status
# ============================================================================
@router.post("/update_ad_status")
async def update_ad_status(
    request: Request,
    db: Session = Depends(get_db),
    current_company: dict = Depends(get_current_company)
):
    """Update ad status (active/inactive/scheduled)"""
    company_slug = current_company.get("sub")

    try:
        data = await request.json()
    except:
        form = await request.form()
        data = dict(form)

    ad_id = data.get("ad_id")
    new_status = data.get("status")

    if not ad_id or not new_status:
        raise HTTPException(status_code=400, detail="ad_id and status are required")

    if new_status not in ["active", "inactive", "scheduled"]:
        raise HTTPException(status_code=400, detail="Invalid status")

    ad = db.query(Ad).filter(
        Ad.ad_id == ad_id,
        Ad.company_slug == company_slug
    ).first()

    if not ad:
        raise HTTPException(status_code=404, detail="Ad not found")

    ad.status = new_status
    ad.updated_at = get_current_timestamp()
    db.commit()

    return {
        "success": True,
        "message": f"Ad status updated to {new_status}",
        "ad_id": ad_id,
        "new_status": new_status
    }


# ============================================================================
# POST /api/duplicate_ad - Duplicate an ad
# ============================================================================
@router.post("/duplicate_ad")
async def duplicate_ad(
    request: Request,
    db: Session = Depends(get_db),
    current_company: dict = Depends(get_current_company)
):
    """Duplicate an existing ad"""
    company_slug = current_company.get("sub")

    try:
        data = await request.json()
    except:
        form = await request.form()
        data = dict(form)

    ad_id = data.get("ad_id")
    if not ad_id:
        raise HTTPException(status_code=400, detail="ad_id is required")

    # Find original ad
    original = db.query(Ad).filter(
        Ad.ad_id == ad_id,
        Ad.company_slug == company_slug
    ).first()

    if not original:
        raise HTTPException(status_code=404, detail="Ad not found")

    # Create new ad ID
    import random
    import string
    new_id = f"AD-{datetime.now().strftime('%Y%m')}-{datetime.now().strftime('%H%M%S%f')[:10]}-{''.join(random.choices(string.ascii_uppercase + string.digits, k=5))}"

    # Create duplicate
    new_ad = Ad(
        ad_id=new_id,
        company_slug=company_slug,
        category_slug=original.category_slug,
        title=f"{original.title} (Copy)",
        description=original.description,
        media_type=original.media_type,
        media_path=original.media_path,
        contact_phone=original.contact_phone,
        contact_email=original.contact_email,
        contact_whatsapp=original.contact_whatsapp,
        price=original.price,
        location=original.location,
        status="inactive",  # Start as inactive
        created_at=get_current_timestamp()
    )

    db.add(new_ad)
    db.commit()

    return {
        "success": True,
        "message": "Ad duplicated successfully",
        "original_id": ad_id,
        "new_id": new_id
    }


# ============================================================================
# POST /api/schedule_ad - Schedule an ad
# ============================================================================
@router.post("/schedule_ad")
async def schedule_ad(
    request: Request,
    db: Session = Depends(get_db),
    current_company: dict = Depends(get_current_company)
):
    """Schedule an ad for future publication"""
    company_slug = current_company.get("sub")

    try:
        data = await request.json()
    except:
        form = await request.form()
        data = dict(form)

    ad_id = data.get("ad_id")
    schedule_date = data.get("schedule_date")

    if not ad_id or not schedule_date:
        raise HTTPException(status_code=400, detail="ad_id and schedule_date are required")

    ad = db.query(Ad).filter(
        Ad.ad_id == ad_id,
        Ad.company_slug == company_slug
    ).first()

    if not ad:
        raise HTTPException(status_code=404, detail="Ad not found")

    ad.status = "scheduled"
    ad.scheduled_at = schedule_date
    ad.updated_at = get_current_timestamp()
    db.commit()

    return {
        "success": True,
        "message": f"Ad scheduled for {schedule_date}",
        "ad_id": ad_id,
        "scheduled_at": schedule_date
    }


# ============================================================================
# POST /api/track_event - Track events
# ============================================================================
@router.post("/track_event")
async def track_event(
    request: Request,
    db: Session = Depends(get_db)
):
    """Track ad events (views, clicks, etc.)"""
    try:
        data = await request.json()
    except:
        form = await request.form()
        data = dict(form)

    ad_id = data.get("ad_id")
    event_type = data.get("event_type", "view")

    if not ad_id:
        raise HTTPException(status_code=400, detail="ad_id is required")

    ad = db.query(Ad).filter(Ad.ad_id == ad_id).first()
    if not ad:
        raise HTTPException(status_code=404, detail="Ad not found")

    # Update counters
    if event_type == "view":
        ad.views_count = (ad.views_count or 0) + 1
    elif event_type == "like":
        ad.likes_count = (ad.likes_count or 0) + 1
    elif event_type == "dislike":
        ad.dislikes_count = (ad.dislikes_count or 0) + 1
    elif event_type == "favorite":
        ad.favorites_count = (ad.favorites_count or 0) + 1
    elif event_type in ["call", "sms", "email", "whatsapp"]:
        ad.contacts_count = (ad.contacts_count or 0) + 1

    db.commit()

    return {
        "success": True,
        "message": f"Event {event_type} tracked for ad {ad_id}"
    }


# ============================================================================
# POST /api/track_interaction - Track interactions
# ============================================================================
@router.post("/track_interaction")
async def track_interaction(
    request: Request,
    db: Session = Depends(get_db)
):
    """Track detailed interactions"""
    try:
        data = await request.json()
    except:
        form = await request.form()
        data = dict(form)

    ad_id = data.get("ad_id")
    event_type = data.get("event_type")
    duration = data.get("duration_seconds", 0)

    if not ad_id or not event_type:
        raise HTTPException(status_code=400, detail="ad_id and event_type required")

    # Create interaction record
    interaction = Interaction(
        ad_id=ad_id,
        event_type=event_type,
        duration_seconds=duration,
        device_info=data.get("device_info"),
        created_at=get_current_timestamp()
    )

    db.add(interaction)

    # Also update ad counters
    ad = db.query(Ad).filter(Ad.ad_id == ad_id).first()
    if ad:
        if event_type == "view":
            ad.views_count = (ad.views_count or 0) + 1
        elif event_type in ["call", "sms", "email", "whatsapp"]:
            ad.contacts_count = (ad.contacts_count or 0) + 1

    db.commit()

    return {
        "success": True,
        "message": "Interaction tracked"
    }


# ============================================================================
# GET /api/categories - Get categories
# ============================================================================
@router.get("/categories")
@router.get("/get_categories")
async def get_categories(db: Session = Depends(get_db)):
    """Get all categories"""
    categories = db.query(Category).filter(Category.status == "active").all()

    return {
        "success": True,
        "categories": [
            {
                "slug": cat.category_slug,
                "name": cat.category_name,
                "icon": cat.icon,
                "description": cat.description
            }
            for cat in categories
        ]
    }


# ============================================================================
# GET /api/session - Session info
# ============================================================================
@router.get("/session")
async def get_session(current_company: dict = Depends(get_current_company)):
    """Get current session info"""
    return {
        "success": True,
        "data": {
            "company": current_company.get("sub"),
            "company_name": current_company.get("company_name"),
            "logged_in": True,
            "token_exp": current_company.get("exp")
        }
    }


# ============================================================================
# POST /api/logout - Logout
# ============================================================================
@router.post("/logout")
async def logout():
    """Logout - client should discard token"""
    return {
        "success": True,
        "message": "Logged out. Please discard your token."
    }


# ============================================================================
# GET /api/health - Health check
# ============================================================================
@router.get("/health")
async def health_check(request: Request):
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "company",
        "authenticated": hasattr(request.state, "company"),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

