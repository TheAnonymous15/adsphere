"""
AdSphere Complete Python System
Full recreation of PHP system with FastAPI
All 3 services: Public (8001), Company (8003), Admin (8004)
"""

from fastapi import FastAPI, HTTPException, Depends, Request
from sqlalchemy.orm import Session
from sqlalchemy import func
from contextlib import asynccontextmanager
import uvicorn
import sys

# Import local modules
from models import (
    Company, Ad, Category, get_current_timestamp
)
from auth import AuthService, get_current_company
from database import get_db
from schemas import CompanyLogin

# Import routers
from python_system.python_shared.routers import router as company_api_router

# Don't create tables - use existing database
# Base.metadata.create_all(bind=engine)


# ============================================================================
# STARTUP AND SHUTDOWN EVENTS
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown"""
    # Startup
    print(f"✅ {app.title} starting up...")
    yield
    # Shutdown
    print(f"✅ {app.title} shutting down...")


# ============================================================================
# PUBLIC SERVICE - Port 8001
# ============================================================================

public_app = FastAPI(
    title="AdSphere Public Service",
    description="Browse and interact with advertisements",
    version="1.0.0",
    lifespan=lifespan
)


@public_app.get("/")
async def public_home(db: Session = Depends(get_db)):
    """Public home - list featured ads"""
    try:
        featured_ads = db.query(Ad).filter(Ad.status == "active").order_by(Ad.views_count.desc()).limit(20).all()

        return {
            "status": "success",
            "message": "Welcome to AdSphere",
            "ads": [
                {
                    "id": ad.ad_id,
                    "title": ad.title,
                    "description": (ad.description[:100] if ad.description else ""),
                    "category": ad.category_slug,
                    "views": ad.views_count or 0,
                    "contacts": ad.contacts_count or 0,
                    "image": ad.media_path if ad.media_type == "image" else None
                }
                for ad in featured_ads
            ]
        }
    except Exception as e:
        return {
            "status": "success",
            "message": "Welcome to AdSphere",
            "ads": [],
            "error": str(e)
        }


@public_app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "public", "port": 8001}


@public_app.get("/api/ads")
async def get_ads(
    category: str = None,
    search: str = None,
    page: int = 1,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Get ads with optional filters"""
    try:
        query = db.query(Ad).filter(Ad.status == "active")

        if category:
            query = query.filter(Ad.category_slug == category)

        if search:
            query = query.filter(
                (Ad.title.ilike(f"%{search}%")) |
                (Ad.description.ilike(f"%{search}%"))
            )

        total = query.count()
        offset = (page - 1) * limit
        ads = query.order_by(Ad.created_at.desc()).offset(offset).limit(limit).all()

        return {
            "status": "success",
            "total": total,
            "page": page,
            "limit": limit,
            "ads": [
                {
                    "id": ad.ad_id,
                    "title": ad.title,
                    "description": ad.description,
                    "category": ad.category_slug,
                    "status": ad.status,
                    "views": ad.views_count or 0,
                    "likes": ad.likes_count or 0,
                    "favorites": ad.favorites_count or 0,
                    "contacts": ad.contacts_count or 0,
                    "media_path": ad.media_path,
                    "media_type": ad.media_type,
                    "created_at": ad.created_at
                }
                for ad in ads
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@public_app.get("/api/ads/{ad_id}")
async def get_ad_detail(ad_id: str, db: Session = Depends(get_db)):
    """Get single ad details"""
    ad = db.query(Ad).filter(Ad.ad_id == ad_id).first()
    if not ad:
        raise HTTPException(status_code=404, detail="Ad not found")

    # Increment view count
    ad.views_count = (ad.views_count or 0) + 1
    db.commit()

    return {
        "status": "success",
        "ad": {
            "id": ad.ad_id,
            "title": ad.title,
            "description": ad.description,
            "category": ad.category_slug,
            "company": ad.company_slug,
            "status": ad.status,
            "views": ad.views_count,
            "likes": ad.likes_count or 0,
            "dislikes": ad.dislikes_count or 0,
            "favorites": ad.favorites_count or 0,
            "contacts": ad.contacts_count or 0,
            "media_path": ad.media_path,
            "media_type": ad.media_type,
            "contact": {
                "phone": ad.contact_phone,
                "sms": ad.contact_sms,
                "email": ad.contact_email,
                "whatsapp": ad.contact_whatsapp
            },
            "created_at": ad.created_at,
            "updated_at": ad.updated_at
        }
    }


@public_app.get("/api/categories")
async def get_categories(db: Session = Depends(get_db)):
    """Get all categories"""
    categories = db.query(Category).all()
    return {
        "status": "success",
        "categories": [
            {
                "id": cat.category_id,
                "slug": cat.category_slug,
                "name": cat.category_name,
                "description": cat.description
            }
            for cat in categories
        ]
    }


@public_app.get("/api/dashboard_stats")
async def get_dashboard_stats(db: Session = Depends(get_db)):
    """Get public dashboard statistics"""
    try:
        total_ads = db.query(Ad).filter(Ad.status == "active").count()
        total_views = db.query(func.sum(Ad.views_count)).scalar() or 0
        total_companies = db.query(Company).count()
        total_categories = db.query(Category).count()

        return {
            "status": "success",
            "total_ads": total_ads,
            "total_views": int(total_views),
            "total_companies": total_companies,
            "total_categories": total_categories
        }
    except Exception as e:
        return {
            "status": "success",
            "total_ads": 0,
            "total_views": 0,
            "total_companies": 0,
            "total_categories": 0,
            "error": str(e)
        }


@public_app.post("/api/track_interaction")
async def track_interaction(
    ad_id: str,
    event_type: str,
    duration_seconds: int = 0,
    db: Session = Depends(get_db)
):
    """Track user interactions with ads"""
    ad = db.query(Ad).filter(Ad.ad_id == ad_id).first()
    if not ad:
        raise HTTPException(status_code=404, detail="Ad not found")

    # Track based on event type
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

    return {"status": "success", "message": f"Tracked {event_type} for ad {ad_id}"}


# ============================================================================
# COMPANY SERVICE - Port 8003
# ============================================================================

company_app = FastAPI(
    title="AdSphere Company Service",
    description="Manage ads and analytics for companies",
    version="1.0.0",
    lifespan=lifespan
)

# Include the company API router
company_app.include_router(company_api_router)
company_app.include_router(company_handlers_router)


@company_app.get("/health")
async def company_health():
    return {"status": "healthy", "service": "company", "port": 8003}


@company_app.post("/api/login")
async def company_login(credentials: CompanyLogin, db: Session = Depends(get_db)):
    """Company login"""
    company = db.query(Company).filter(Company.company_slug == credentials.slug).first()

    if not company:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # For now, check against simple password (you can enhance this)
    # In production, use password_hash comparison

    token = AuthService.create_company_token(company.company_slug, company.company_name)

    return {
        "status": "success",
        "message": "Logged in successfully",
        "company_slug": company.company_slug,
        "company_name": company.company_name,
        "token": token
    }


@company_app.get("/api/my-ads")
async def get_company_ads(
    db: Session = Depends(get_db),
    current_company: dict = Depends(get_current_company)
):
    """Get ads for current company"""
    company_slug = current_company.get("sub")

    ads = db.query(Ad).filter(Ad.company_slug == company_slug).order_by(Ad.created_at.desc()).all()

    return {
        "status": "success",
        "total": len(ads),
        "ads": [
            {
                "id": ad.ad_id,
                "title": ad.title,
                "description": ad.description,
                "category": ad.category_slug,
                "status": ad.status,
                "views": ad.views_count or 0,
                "likes": ad.likes_count or 0,
                "favorites": ad.favorites_count or 0,
                "contacts": ad.contacts_count or 0,
                "media_path": ad.media_path,
                "created_at": ad.created_at
            }
            for ad in ads
        ]
    }


@company_app.get("/api/analytics/{ad_id}")
async def get_ad_analytics(
    ad_id: str,
    db: Session = Depends(get_db),
    current_company: dict = Depends(get_current_company)
):
    """Get analytics for a specific ad"""
    company_slug = current_company.get("sub")

    ad = db.query(Ad).filter(Ad.ad_id == ad_id, Ad.company_slug == company_slug).first()
    if not ad:
        raise HTTPException(status_code=404, detail="Ad not found")

    return {
        "status": "success",
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


@company_app.get("/api/profile")
async def get_company_profile(
    db: Session = Depends(get_db),
    current_company: dict = Depends(get_current_company)
):
    """Get company profile"""
    company_slug = current_company.get("sub")

    company = db.query(Company).filter(Company.company_slug == company_slug).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    return {
        "status": "success",
        "profile": {
            "company_slug": company.company_slug,
            "company_name": company.company_name,
            "email": company.email or "",
            "phone": company.phone or "",
            "website": company.website or "",
            "description": company.description or "",
            "logo": company.logo or "",
            "status": company.status,
            "created_at": company.created_at
        }
    }


@company_app.post("/api/profile/save")
async def save_company_profile(
    request: Request,
    db: Session = Depends(get_db),
    current_company: dict = Depends(get_current_company)
):
    """Save/update company profile"""
    company_slug = current_company.get("sub")

    company = db.query(Company).filter(Company.company_slug == company_slug).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    # Get form data or JSON
    try:
        data = await request.json()
    except:
        form = await request.form()
        data = dict(form)

    # Update allowed fields
    if "email" in data:
        company.email = data["email"]
    if "phone" in data:
        company.phone = data["phone"]
    if "website" in data:
        company.website = data["website"]
    if "description" in data:
        company.description = data["description"]
    if "company_name" in data:
        company.company_name = data["company_name"]

    company.updated_at = get_current_timestamp()
    db.commit()

    return {
        "status": "success",
        "message": "Profile updated successfully",
        "redirect": "/profile?updated=1"
    }


# ============================================================================
# ADMIN SERVICE - Port 8004
# ============================================================================

admin_app = FastAPI(
    title="AdSphere Admin Service",
    description="Platform administration and moderation",
    version="1.0.0",
    lifespan=lifespan
)


@admin_app.get("/health")
async def admin_health():
    return {"status": "healthy", "service": "admin", "port": 8004}


@admin_app.get("/api/dashboard")
async def admin_dashboard(db: Session = Depends(get_db)):
    """Admin dashboard stats"""
    try:
        total_ads = db.query(Ad).count()
        active_ads = db.query(Ad).filter(Ad.status == "active").count()
        total_companies = db.query(Company).count()
        total_views = db.query(func.sum(Ad.views_count)).scalar() or 0
        total_likes = db.query(func.sum(Ad.likes_count)).scalar() or 0
        total_favorites = db.query(func.sum(Ad.favorites_count)).scalar() or 0
        total_contacts = db.query(func.sum(Ad.contacts_count)).scalar() or 0

        return {
            "status": "success",
            "stats": {
                "total_ads": total_ads,
                "active_ads": active_ads,
                "total_companies": total_companies,
                "total_views": int(total_views),
                "total_likes": int(total_likes),
                "total_favorites": int(total_favorites),
                "total_contacts": int(total_contacts)
            }
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


@admin_app.get("/api/companies")
async def get_companies(db: Session = Depends(get_db)):
    """Get all companies"""
    companies = db.query(Company).all()
    return {
        "status": "success",
        "companies": [
            {
                "slug": c.company_slug,
                "name": c.company_name,
                "email": c.email,
                "status": c.status,
                "created_at": c.created_at
            }
            for c in companies
        ]
    }


@admin_app.get("/api/ads")
async def admin_get_ads(
    status: str = None,
    db: Session = Depends(get_db)
):
    """Get all ads (admin view)"""
    query = db.query(Ad)

    if status:
        query = query.filter(Ad.status == status)

    ads = query.order_by(Ad.created_at.desc()).all()

    return {
        "status": "success",
        "total": len(ads),
        "ads": [
            {
                "id": ad.ad_id,
                "title": ad.title,
                "company": ad.company_slug,
                "category": ad.category_slug,
                "status": ad.status,
                "views": ad.views_count or 0,
                "created_at": ad.created_at
            }
            for ad in ads
        ]
    }


@admin_app.post("/api/ads/{ad_id}/moderate")
async def moderate_ad(
    ad_id: str,
    action: str,
    reason: str = None,
    db: Session = Depends(get_db)
):
    """Moderate an ad (approve/block/review)"""
    ad = db.query(Ad).filter(Ad.ad_id == ad_id).first()
    if not ad:
        raise HTTPException(status_code=404, detail="Ad not found")

    if action == "approve":
        ad.status = "active"
    elif action == "block":
        ad.status = "inactive"
    elif action == "review":
        ad.status = "scheduled"  # Using scheduled as "pending review"

    ad.updated_at = get_current_timestamp()
    db.commit()

    return {
        "status": "success",
        "message": f"Ad {action}d successfully",
        "ad_id": ad_id,
        "new_status": ad.status
    }


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    if len(sys.argv) > 1:
        service = sys.argv[1]

        if service == "public":
            print("🚀 Starting Public Service on Port 8001...")
            uvicorn.run(public_app, host="0.0.0.0", port=8001, reload=False)

        elif service == "company":
            print("🚀 Starting Company Service on Port 8003...")
            uvicorn.run(company_app, host="0.0.0.0", port=8003, reload=False)

        elif service == "admin":
            print("🚀 Starting Admin Service on Port 8004...")
            uvicorn.run(admin_app, host="0.0.0.0", port=8004, reload=False)

        elif service == "all":
            print("🚀 Starting all services...")
            print("  - Public: 8001")
            print("  - Company: 8003")
            print("  - Admin: 8004")
            print("\nRun each in separate terminal:")
            print("  python app.py public")
            print("  python app.py company")
            print("  python app.py admin")

        else:
            print("Usage: python app.py [public|company|admin|all]")

    else:
        print("Usage: python app.py [public|company|admin|all]")

