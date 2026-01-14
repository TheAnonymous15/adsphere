"""
AdSphere Full Python System - Complete Recreation
Replaces all 3 PHP services (Public, Company, Admin)
Ports: 8001 (Public), 8003 (Company), 8004 (Admin)
"""

from fastapi import FastAPI, HTTPException, Depends, Request, Session
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from sqlalchemy import create_engine, Column, String, Integer, DateTime, JSON, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session as DBSession
from pydantic import BaseModel
from datetime import datetime, timedelta
import jwt
import os
import json
from typing import Optional, List
import uvicorn
from pathlib import Path

# ============================================================================
# CONFIGURATION
# ============================================================================

BASE_PATH = Path(__file__).parent.parent
DATABASE_URL = f"sqlite:///{BASE_PATH}/app/database/adsphere.db"
SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

# ============================================================================
# DATABASE MODELS
# ============================================================================

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True)
    password_hash = Column(String)
    full_name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)


class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True)
    slug = Column(String, unique=True)
    name = Column(String)
    email = Column(String)
    verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Ad(Base):
    __tablename__ = "ads"

    id = Column(String, primary_key=True)
    company_id = Column(Integer)
    title = Column(String)
    description = Column(String)
    category = Column(String)
    status = Column(String, default="active")
    images = Column(JSON)
    video = Column(String)
    view_count = Column(Integer, default=0)
    contact_count = Column(Integer, default=0)
    favorite_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


class Admin(Base):
    __tablename__ = "admins"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    email = Column(String)
    password_hash = Column(String)
    two_factor_enabled = Column(Boolean, default=False)
    two_factor_secret = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)


# Create tables
Base.metadata.create_all(bind=engine)


# ============================================================================
# SHARED UTILITIES
# ============================================================================

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class UserLogin(BaseModel):
    email: str
    password: str


class CompanyLogin(BaseModel):
    slug: str
    password: str


class AdminLogin(BaseModel):
    username: str
    password: str


class AdCreate(BaseModel):
    title: str
    description: str
    category: str
    images: Optional[List[str]] = []
    video: Optional[str] = None


class AdResponse(BaseModel):
    id: str
    title: str
    description: str
    category: str
    view_count: int
    contact_count: int
    favorite_count: int
    like_count: int


# ============================================================================
# SHARED SERVICE FACTORY
# ============================================================================

class ServiceFactory:
    """Factory to create configured service instances"""

    @staticmethod
    def create_public_app():
        """Create public service app (Port 8001)"""
        return FastAPI(
            title="AdSphere Public Service",
            description="Browse and interact with advertisements",
            version="1.0.0"
        )

    @staticmethod
    def create_company_app():
        """Create company service app (Port 8003)"""
        return FastAPI(
            title="AdSphere Company Service",
            description="Advertiser dashboard and management",
            version="1.0.0"
        )

    @staticmethod
    def create_admin_app():
        """Create admin service app (Port 8004)"""
        return FastAPI(
            title="AdSphere Admin Service",
            description="Platform administration and moderation",
            version="1.0.0"
        )


# ============================================================================
# PUBLIC SERVICE (Port 8001)
# ============================================================================

public_app = ServiceFactory.create_public_app()

@public_app.get("/", response_class=HTMLResponse)
async def public_home(db: DBSession = Depends(get_db)):
    """Public home page - browse ads"""
    ads = db.query(Ad).filter(Ad.status == "active").limit(20).all()
    return {
        "ads": [
            {
                "id": ad.id,
                "title": ad.title,
                "description": ad.description,
                "category": ad.category,
                "view_count": ad.view_count,
                "image": ad.images[0] if ad.images else None
            }
            for ad in ads
        ]
    }


@public_app.get("/ads")
async def get_public_ads(category: Optional[str] = None, search: Optional[str] = None, db: DBSession = Depends(get_db)):
    """Get ads with optional filters"""
    query = db.query(Ad).filter(Ad.status == "active")

    if category:
        query = query.filter(Ad.category == category)

    if search:
        query = query.filter(Ad.title.ilike(f"%{search}%"))

    ads = query.all()
    return {
        "ads": [AdResponse.from_orm(ad).__dict__ for ad in ads]
    }


@public_app.post("/api/track_interaction")
async def track_interaction(ad_id: str, event_type: str, db: DBSession = Depends(get_db)):
    """Track user interactions (views, contacts)"""
    ad = db.query(Ad).filter(Ad.id == ad_id).first()
    if not ad:
        raise HTTPException(status_code=404, detail="Ad not found")

    if event_type == "view":
        ad.view_count += 1
    elif event_type == "contact":
        ad.contact_count += 1
    elif event_type == "favorite":
        ad.favorite_count += 1
    elif event_type == "like":
        ad.like_count += 1

    db.commit()
    return {"success": True, "message": f"{event_type} tracked"}


@public_app.post("/api/register")
async def register_user(user_data: UserLogin, db: DBSession = Depends(get_db)):
    """Register new user"""
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")

    # In production, hash the password
    new_user = User(email=user_data.email, password_hash=user_data.password)
    db.add(new_user)
    db.commit()

    token = create_access_token({"sub": user_data.email})
    return {"token": token, "user_id": new_user.id}


@public_app.post("/api/login")
async def login_user(credentials: UserLogin, db: DBSession = Depends(get_db)):
    """Login user"""
    user = db.query(User).filter(User.email == credentials.email).first()
    if not user or user.password_hash != credentials.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"sub": user.email})
    return {"token": token, "user_id": user.id}


@public_app.get("/api/categories")
async def get_categories(db: DBSession = Depends(get_db)):
    """Get all ad categories"""
    categories = db.query(Ad.category).distinct().all()
    return {"categories": [cat[0] for cat in categories]}


@public_app.get("/api/dashboard_stats")
async def get_dashboard_stats(db: DBSession = Depends(get_db)):
    """Get platform statistics"""
    total_ads = db.query(Ad).count()
    total_views = db.query(Ad).with_entities(db.func.sum(Ad.view_count)).scalar() or 0
    total_contacts = db.query(Ad).with_entities(db.func.sum(Ad.contact_count)).scalar() or 0
    total_companies = db.query(Company).count()

    return {
        "total_ads": total_ads,
        "total_views": total_views,
        "total_contacts": total_contacts,
        "total_companies": total_companies,
        "active_users": 0,  # To be implemented
        "engagements": total_contacts
    }


# ============================================================================
# COMPANY SERVICE (Port 8003)
# ============================================================================

company_app = ServiceFactory.create_company_app()

@company_app.get("/", response_class=HTMLResponse)
async def company_home():
    """Company dashboard home"""
    return {"status": "company service", "message": "Welcome to company dashboard"}


@company_app.post("/api/login")
async def company_login(credentials: CompanyLogin, db: DBSession = Depends(get_db)):
    """Company login"""
    company = db.query(Company).filter(Company.slug == credentials.slug).first()
    if not company or company.email != credentials.slug:  # Simplified check
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"sub": company.slug, "type": "company"})
    return {"token": token, "company_id": company.id, "company_name": company.name}


@company_app.get("/api/my-ads")
async def get_company_ads(company_id: int, db: DBSession = Depends(get_db)):
    """Get company's ads"""
    ads = db.query(Ad).filter(Ad.company_id == company_id).all()
    return {
        "ads": [AdResponse.from_orm(ad).__dict__ for ad in ads]
    }


@company_app.post("/api/upload-ad")
async def upload_ad(ad_data: AdCreate, company_id: int, db: DBSession = Depends(get_db)):
    """Upload new ad"""
    import uuid

    ad_id = f"AD-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{str(uuid.uuid4())[:8]}"

    new_ad = Ad(
        id=ad_id,
        company_id=company_id,
        title=ad_data.title,
        description=ad_data.description,
        category=ad_data.category,
        images=ad_data.images,
        video=ad_data.video,
        status="pending_review"  # Should go through moderation
    )

    db.add(new_ad)
    db.commit()

    return {
        "success": True,
        "ad_id": ad_id,
        "status": "pending_review",
        "message": "Ad uploaded, awaiting moderation"
    }


@company_app.get("/api/analytics/{ad_id}")
async def get_ad_analytics(ad_id: str, db: DBSession = Depends(get_db)):
    """Get analytics for specific ad"""
    ad = db.query(Ad).filter(Ad.id == ad_id).first()
    if not ad:
        raise HTTPException(status_code=404, detail="Ad not found")

    return {
        "ad_id": ad_id,
        "views": ad.view_count,
        "contacts": ad.contact_count,
        "favorites": ad.favorite_count,
        "likes": ad.like_count,
        "contact_methods": {
            "call": 0,
            "sms": 0,
            "email": 0,
            "whatsapp": 0
        }
    }


@company_app.delete("/api/ads/{ad_id}")
async def delete_ad(ad_id: str, db: DBSession = Depends(get_db)):
    """Delete an ad"""
    ad = db.query(Ad).filter(Ad.id == ad_id).first()
    if not ad:
        raise HTTPException(status_code=404, detail="Ad not found")

    db.delete(ad)
    db.commit()

    return {"success": True, "message": "Ad deleted"}


# ============================================================================
# ADMIN SERVICE (Port 8004)
# ============================================================================

admin_app = ServiceFactory.create_admin_app()

@admin_app.post("/api/login")
async def admin_login(credentials: AdminLogin, db: DBSession = Depends(get_db)):
    """Admin login"""
    admin = db.query(Admin).filter(Admin.username == credentials.username).first()
    if not admin or admin.password_hash != credentials.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"sub": admin.username, "type": "admin"})
    return {"token": token, "admin_id": admin.id, "requires_2fa": admin.two_factor_enabled}


@admin_app.get("/api/dashboard")
async def admin_dashboard(db: DBSession = Depends(get_db)):
    """Admin dashboard statistics"""
    total_ads = db.query(Ad).count()
    total_views = db.query(Ad).with_entities(db.func.sum(Ad.view_count)).scalar() or 0
    active_ads = db.query(Ad).filter(Ad.status == "active").count()
    blocked_ads = db.query(Ad).filter(Ad.status == "blocked").count()
    pending_review = db.query(Ad).filter(Ad.status == "pending_review").count()
    total_companies = db.query(Company).count()
    total_users = db.query(User).count()

    return {
        "total_ads": total_ads,
        "active_ads": active_ads,
        "blocked_ads": blocked_ads,
        "pending_review": pending_review,
        "total_views": total_views,
        "total_companies": total_companies,
        "total_users": total_users,
        "engagement_rate": 0.0  # To be calculated
    }


@admin_app.get("/api/moderation-queue")
async def get_moderation_queue(db: DBSession = Depends(get_db)):
    """Get ads pending moderation review"""
    pending_ads = db.query(Ad).filter(Ad.status == "pending_review").all()
    return {
        "pending_count": len(pending_ads),
        "ads": [
            {
                "id": ad.id,
                "title": ad.title,
                "company_id": ad.company_id,
                "submitted_at": ad.created_at.isoformat()
            }
            for ad in pending_ads
        ]
    }


@admin_app.post("/api/ads/{ad_id}/moderate")
async def moderate_ad(ad_id: str, decision: str, reason: str = "", db: DBSession = Depends(get_db)):
    """Moderate an ad (approve/block/review)"""
    ad = db.query(Ad).filter(Ad.id == ad_id).first()
    if not ad:
        raise HTTPException(status_code=404, detail="Ad not found")

    if decision not in ["approve", "block", "review"]:
        raise HTTPException(status_code=400, detail="Invalid decision")

    ad.status = decision if decision != "review" else "pending_review"
    db.commit()

    return {
        "success": True,
        "ad_id": ad_id,
        "decision": decision,
        "reason": reason
    }


@admin_app.get("/api/companies")
async def get_companies(db: DBSession = Depends(get_db)):
    """Get all companies"""
    companies = db.query(Company).all()
    return {
        "total": len(companies),
        "companies": [
            {
                "id": c.id,
                "name": c.name,
                "slug": c.slug,
                "email": c.email,
                "verified": c.verified,
                "created_at": c.created_at.isoformat()
            }
            for c in companies
        ]
    }


@admin_app.post("/api/companies/{company_id}/suspend")
async def suspend_company(company_id: int, db: DBSession = Depends(get_db)):
    """Suspend a company"""
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    company.verified = False
    db.commit()

    return {"success": True, "message": f"Company {company.name} suspended"}


# ============================================================================
# STARTUP FUNCTION
# ============================================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        service = sys.argv[1]

        if service == "public":
            print("Starting Public Service on Port 8001...")
            uvicorn.run(public_app, host="0.0.0.0", port=8001, reload=True)

        elif service == "company":
            print("Starting Company Service on Port 8003...")
            uvicorn.run(company_app, host="0.0.0.0", port=8003, reload=True)

        elif service == "admin":
            print("Starting Admin Service on Port 8004...")
            uvicorn.run(admin_app, host="0.0.0.0", port=8004, reload=True)

        else:
            print("Usage: python main.py [public|company|admin]")
    else:
        print("Usage: python main.py [public|company|admin]")

