"""
ADSPHERE PUBLIC SERVICE - Python FastAPI Version
Replaces services/public/index.php
Port 8001 - Public ad browsing with full HTML frontend
"""

from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func
from pathlib import Path
from datetime import datetime
import time
import os
import sys

# Add parent path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))  # python_system directory

from models import Base, Company, Ad, Category, AdView, Interaction, Favorite, get_current_timestamp
from database import engine, SessionLocal, get_db

# ============================================================================
# PATHS CONFIGURATION
# ============================================================================
PYTHON_SYSTEM_PATH = Path(__file__).parent.parent  # /python_system
BASE_PATH = PYTHON_SYSTEM_PATH.parent  # /adsphere
SERVICE_PATH = Path(__file__).parent  # /python_system/public_python
TEMPLATES_PATH = SERVICE_PATH / "templates"

# Static assets - within python_system
ASSETS_PATH = PYTHON_SYSTEM_PATH / "static"

# Media storage paths - python_company/data has the actual ad media
COMPANY_DATA_PATH = PYTHON_SYSTEM_PATH / "python_company" / "data"

# ============================================================================
# APP INITIALIZATION
# ============================================================================
app = FastAPI(
    title="AdSphere Public Service",
    description="Public ad browsing with full HTML frontend",
    version="1.0.0"
)

# Mount static files
if ASSETS_PATH.exists():
    app.mount("/static", StaticFiles(directory=str(ASSETS_PATH)), name="static")

# Mount company data for ad media
if COMPANY_DATA_PATH.exists():
    app.mount("/company/data", StaticFiles(directory=str(COMPANY_DATA_PATH)), name="company_data")

# Setup Jinja2 templates
templates = Jinja2Templates(directory=str(TEMPLATES_PATH))


# ============================================================================
# DATABASE HELPERS
# ============================================================================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_ads_from_db(db: Session, category: str = None, search: str = None, limit: int = 20, offset: int = 0):
    """Fetch ads from database"""
    query = db.query(Ad).filter(Ad.status == "active")

    if category:
        query = query.filter(Ad.category_slug == category)

    if search:
        query = query.filter(
            (Ad.title.ilike(f"%{search}%")) |
            (Ad.description.ilike(f"%{search}%"))
        )

    total = query.count()
    ads = query.order_by(Ad.created_at.desc()).offset(offset).limit(limit).all()

    formatted_ads = []
    for ad in ads:
        # Build proper media URL
        media_url = ""
        if ad.media_path:
            # Media path format: category/company/ad_id/filename
            # URL should be: /company/data/category/company/ad_id/filename
            media_url = f"/company/data/{ad.media_path}"

        formatted_ads.append({
            "id": ad.ad_id,
            "title": ad.title,
            "description": ad.description or "",
            "category": ad.category_slug,
            "company": ad.company_slug,
            "status": ad.status,
            "views": ad.views_count or 0,
            "likes": ad.likes_count or 0,
            "dislikes": ad.dislikes_count or 0,
            "favorites": ad.favorites_count or 0,
            "contacts": ad.contacts_count or 0,
            "media_path": media_url,  # Full URL path
            "media_type": ad.media_type or "image",
            "contact": {
                "phone": ad.contact_phone or "",
                "sms": ad.contact_sms or "",
                "email": ad.contact_email or "",
                "whatsapp": ad.contact_whatsapp or ""
            },
            "created_at": str(ad.created_at) if ad.created_at else ""
        })

    return {
        "total": total,
        "ads": formatted_ads
    }


def get_categories_from_db(db: Session):
    """Fetch all categories"""
    categories = db.query(Category).all()
    return [
        {
            "id": cat.category_id,
            "slug": cat.category_slug,
            "name": cat.category_name,
            "description": cat.description
        }
        for cat in categories
    ]


def get_stats_from_db(db: Session):
    """Get platform statistics"""
    try:
        total_ads = db.query(Ad).filter(Ad.status == "active").count()
        total_views = db.query(func.sum(Ad.views_count)).scalar() or 0
        total_companies = db.query(Company).count()
        total_categories = db.query(Category).count()
        total_likes = db.query(func.sum(Ad.likes_count)).scalar() or 0
        total_favorites = db.query(func.sum(Ad.favorites_count)).scalar() or 0

        return {
            "total_ads": total_ads,
            "total_views": int(total_views),
            "total_companies": total_companies,
            "total_categories": total_categories,
            "total_likes": int(total_likes),
            "total_favorites": int(total_favorites)
        }
    except:
        return {
            "total_ads": 0,
            "total_views": 0,
            "total_companies": 0,
            "total_categories": 0,
            "total_likes": 0,
            "total_favorites": 0
        }


# ============================================================================
# HTML PAGE ROUTES
# ============================================================================

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, db: Session = Depends(get_db)):
    """Home page - main landing page with ads"""
    start_time = time.time()

    ads_data = get_ads_from_db(db, limit=20)
    categories = get_categories_from_db(db)
    stats = get_stats_from_db(db)

    exec_time = round((time.time() - start_time) * 1000, 2)

    return templates.TemplateResponse("home_unified.html", {
        "request": request,
        "ads": ads_data["ads"],
        "total_ads": ads_data["total"],
        "categories": categories,
        "stats": stats,
        "exec_time": exec_time,
        "current_year": datetime.now().year
    })


@app.get("/browse", response_class=HTMLResponse)
@app.get("/ads", response_class=HTMLResponse)
@app.get("/search", response_class=HTMLResponse)
async def browse(
    request: Request,
    category: str = None,
    search: str = None,
    page: int = 1,
    db: Session = Depends(get_db)
):
    """Browse ads page"""
    limit = 20
    offset = (page - 1) * limit

    ads_data = get_ads_from_db(db, category=category, search=search, limit=limit, offset=offset)
    categories = get_categories_from_db(db)

    total_pages = (ads_data["total"] + limit - 1) // limit

    return templates.TemplateResponse("browse.html", {
        "request": request,
        "ads": ads_data["ads"],
        "total_ads": ads_data["total"],
        "categories": categories,
        "current_category": category,
        "search_query": search,
        "page": page,
        "total_pages": total_pages,
        "current_year": datetime.now().year
    })


@app.get("/ad/{ad_id}", response_class=HTMLResponse)
async def ad_detail(request: Request, ad_id: str, db: Session = Depends(get_db)):
    """Single ad detail page"""
    ad = db.query(Ad).filter(Ad.ad_id == ad_id).first()

    if not ad:
        return templates.TemplateResponse("404.html", {
            "request": request,
            "message": "Ad not found"
        }, status_code=404)

    # Increment view count
    ad.views_count = (ad.views_count or 0) + 1
    db.commit()

    # Get related ads
    related_ads = db.query(Ad).filter(
        Ad.category_slug == ad.category_slug,
        Ad.ad_id != ad_id,
        Ad.status == "active"
    ).limit(4).all()

    ad_data = {
        "id": ad.ad_id,
        "title": ad.title,
        "description": ad.description or "",
        "category": ad.category_slug,
        "company": ad.company_slug,
        "status": ad.status,
        "views": ad.views_count or 0,
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
        "created_at": ad.created_at
    }

    return templates.TemplateResponse("ad_detail.html", {
        "request": request,
        "ad": ad_data,
        "related_ads": [
            {
                "id": r.ad_id,
                "title": r.title,
                "media_path": r.media_path,
                "views": r.views_count or 0
            }
            for r in related_ads
        ],
        "current_year": datetime.now().year
    })


@app.get("/category/{category_slug}", response_class=HTMLResponse)
async def category_page(request: Request, category_slug: str, page: int = 1, db: Session = Depends(get_db)):
    """Category page"""
    category = db.query(Category).filter(Category.category_slug == category_slug).first()

    if not category:
        return templates.TemplateResponse("404.html", {
            "request": request,
            "message": "Category not found"
        }, status_code=404)

    limit = 20
    offset = (page - 1) * limit
    ads_data = get_ads_from_db(db, category=category_slug, limit=limit, offset=offset)

    return templates.TemplateResponse("category.html", {
        "request": request,
        "category": {
            "slug": category.category_slug,
            "name": category.category_name,
            "description": category.description
        },
        "ads": ads_data["ads"],
        "total_ads": ads_data["total"],
        "page": page,
        "current_year": datetime.now().year
    })


@app.get("/categories", response_class=HTMLResponse)
async def categories_listing(request: Request, db: Session = Depends(get_db)):
    """All categories listing page"""
    categories = get_categories_with_icons(db)

    # Get ad count per category
    for cat in categories:
        count = db.query(Ad).filter(Ad.category_slug == cat["slug"], Ad.status == "active").count()
        cat["ad_count"] = count

    return templates.TemplateResponse("categories.html", {
        "request": request,
        "categories": categories,
        "current_year": datetime.now().year
    })


# Category icons mapping
CATEGORY_ICONS = {
    'electronics': 'fa-laptop',
    'vehicles': 'fa-car',
    'property': 'fa-home',
    'housing': 'fa-home',
    'real_estate': 'fa-building',
    'fashion': 'fa-tshirt',
    'clothing': 'fa-tshirt',
    'furniture': 'fa-couch',
    'home': 'fa-couch',
    'services': 'fa-briefcase',
    'jobs': 'fa-user-tie',
    'careers': 'fa-user-tie',
    'food': 'fa-utensils',
    'dining': 'fa-utensils',
    'health': 'fa-heartbeat',
    'beauty': 'fa-spa',
    'sports': 'fa-futbol',
    'fitness': 'fa-dumbbell',
    'education': 'fa-graduation-cap',
    'travel': 'fa-plane',
    'tourism': 'fa-globe',
    'technology': 'fa-microchip',
    'entertainment': 'fa-film',
    'music': 'fa-music',
    'books': 'fa-book',
    'pets': 'fa-paw',
    'garden': 'fa-leaf',
    'art': 'fa-palette',
    'photography': 'fa-camera',
    'automotive': 'fa-car-side',
    'default': 'fa-tag'
}


def get_category_icon(slug: str, name: str) -> str:
    """Get icon for a category based on slug or name"""
    slug_lower = slug.lower() if slug else ''
    name_lower = name.lower() if name else ''

    for key, icon in CATEGORY_ICONS.items():
        if key != 'default' and (key in slug_lower or key in name_lower):
            return icon
    return CATEGORY_ICONS['default']


def get_categories_with_icons(db: Session):
    """Fetch categories with icons"""
    categories = db.query(Category).all()
    return [
        {
            "id": cat.category_id,
            "slug": cat.category_slug,
            "name": cat.category_name,
            "description": cat.description,
            "icon": get_category_icon(cat.category_slug, cat.category_name)
        }
        for cat in categories
    ]


@app.get("/register", response_class=HTMLResponse)
@app.get("/signup", response_class=HTMLResponse)
async def register_page(request: Request, db: Session = Depends(get_db)):
    """User registration page - GET"""
    categories = get_categories_with_icons(db)

    return templates.TemplateResponse("register.html", {
        "request": request,
        "categories": categories,
        "form_data": None,
        "error": None,
        "success": None,
        "current_year": datetime.now().year
    })


@app.post("/register", response_class=HTMLResponse)
@app.post("/signup", response_class=HTMLResponse)
async def register_submit(request: Request, db: Session = Depends(get_db)):
    """User registration page - POST"""
    from python_system.models import User
    import hashlib
    import uuid

    categories = get_categories_with_icons(db)
    form = await request.form()

    form_data = {
        "full_name": form.get("full_name", ""),
        "email": form.get("email", ""),
        "interests": form.getlist("interests[]") or []
    }

    error = None
    success = None

    # Validation
    full_name = form_data["full_name"].strip()
    email = form_data["email"].strip()
    password = form.get("password", "")
    confirm_password = form.get("confirm_password", "")
    agree_terms = form.get("agree_terms")

    if not full_name or not email or not password:
        error = "Please fill in all required fields."
    elif len(password) < 8:
        error = "Password must be at least 8 characters long."
    elif password != confirm_password:
        error = "Passwords do not match."
    elif not agree_terms:
        error = "You must agree to the Terms of Service."
    else:
        # Check if user exists
        try:
            existing = db.query(User).filter(User.email == email).first()
            if existing:
                error = "An account with this email already exists."
            else:
                # Create user
                user_id = f"USR_{uuid.uuid4().hex[:12]}"
                password_hash = hashlib.sha256(password.encode()).hexdigest()  # Use proper hashing in production

                new_user = User(
                    email=email,
                    password_hash=password_hash,
                    full_name=full_name,
                    preferences=str(form_data["interests"]),
                    created_at=get_current_timestamp()
                )
                db.add(new_user)
                db.commit()
                success = "Account created successfully! You can now login."
        except Exception as e:
            error = f"Failed to create account. Please try again."
            print(f"Registration error: {e}")

    return templates.TemplateResponse("register.html", {
        "request": request,
        "categories": categories,
        "form_data": form_data if error else None,
        "error": error,
        "success": success,
        "current_year": datetime.now().year
    })


@app.get("/login", response_class=HTMLResponse)
@app.get("/signin", response_class=HTMLResponse)
async def login_page(request: Request, registered: bool = False):
    """User login page"""
    return templates.TemplateResponse("login.html", {
        "request": request,
        "error": None,
        "registered": registered,
        "form_data": None,
        "current_year": datetime.now().year
    })


@app.get("/terms", response_class=HTMLResponse)
@app.get("/terms-of-service", response_class=HTMLResponse)
async def terms_page(request: Request):
    """Terms of service page"""
    return templates.TemplateResponse("terms.html", {
        "request": request,
        "current_year": datetime.now().year
    })


@app.get("/privacy", response_class=HTMLResponse)
@app.get("/privacy-policy", response_class=HTMLResponse)
async def privacy_page(request: Request):
    """Privacy policy page"""
    return templates.TemplateResponse("privacy.html", {
        "request": request,
        "current_year": datetime.now().year
    })


# ============================================================================
# API ROUTES (JSON responses)
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "public", "port": 8001}


@app.get("/api/ads")
async def api_get_ads(
    category: str = None,
    search: str = None,
    page: int = 1,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """API: Get ads with filters"""
    offset = (page - 1) * limit
    ads_data = get_ads_from_db(db, category=category, search=search, limit=limit, offset=offset)

    return {
        "status": "success",
        "total": ads_data["total"],
        "page": page,
        "limit": limit,
        "ads": ads_data["ads"]
    }


@app.get("/api/ads/{ad_id}")
async def api_get_ad(ad_id: str, db: Session = Depends(get_db)):
    """API: Get single ad"""
    ad = db.query(Ad).filter(Ad.ad_id == ad_id).first()

    if not ad:
        raise HTTPException(status_code=404, detail="Ad not found")

    # Build proper media URL
    media_url = f"/company/data/{ad.media_path}" if ad.media_path else ""

    return {
        "status": "success",
        "ad": {
            "id": ad.ad_id,
            "title": ad.title,
            "description": ad.description,
            "category": ad.category_slug,
            "company": ad.company_slug,
            "views": ad.views_count or 0,
            "likes": ad.likes_count or 0,
            "favorites": ad.favorites_count or 0,
            "contacts": ad.contacts_count or 0,
            "media_path": media_url,
            "media_type": ad.media_type or "image",
            "contact": {
                "phone": ad.contact_phone or "",
                "sms": ad.contact_sms or "",
                "email": ad.contact_email or "",
                "whatsapp": ad.contact_whatsapp or ""
            }
        }
    }


@app.get("/api/categories")
async def api_get_categories(db: Session = Depends(get_db)):
    """API: Get all categories"""
    categories = get_categories_from_db(db)
    return {"status": "success", "categories": categories}


@app.get("/api/dashboard_stats")
async def api_dashboard_stats(db: Session = Depends(get_db)):
    """API: Get dashboard statistics"""
    stats = get_stats_from_db(db)
    return {"status": "success", **stats}


@app.post("/api/track_interaction")
async def api_track_interaction(
    ad_id: str,
    event_type: str,
    duration_seconds: int = 0,
    db: Session = Depends(get_db)
):
    """API: Track user interactions"""
    ad = db.query(Ad).filter(Ad.ad_id == ad_id).first()

    if not ad:
        raise HTTPException(status_code=404, detail="Ad not found")

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

    return {"status": "success", "message": f"Tracked {event_type}"}


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    """404 error page"""
    if "api" in str(request.url):
        return JSONResponse({"error": "Not found"}, status_code=404)

    return templates.TemplateResponse("404.html", {
        "request": request,
        "current_year": datetime.now().year
    }, status_code=404)


@app.exception_handler(500)
async def server_error_handler(request: Request, exc: Exception):
    """500 error page"""
    if "api" in str(request.url):
        return JSONResponse({"error": "Internal server error"}, status_code=500)

    return templates.TemplateResponse("500.html", {
        "request": request,
        "current_year": datetime.now().year
    }, status_code=500)


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting AdSphere Public Service on Port 8001...")
    uvicorn.run(app, host="0.0.0.0", port=8001, reload=False)

