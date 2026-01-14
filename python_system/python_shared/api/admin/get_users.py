"""
Admin API Module - get_users.py
Get all users for admin dashboard
Converted from PHP to Python
"""

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pathlib import Path
from datetime import datetime
import json
import time

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from models import Company, Ad
from database import get_db

router = APIRouter()

METADATA_PATH = Path(__file__).parent.parent.parent / "companies" / "metadata"
DATA_PATH = Path(__file__).parent.parent.parent / "companies" / "data"


def calculate_last_active(company_slug: str) -> str:
    """Calculate when user was last active based on ad activity"""
    latest_timestamp = 0

    if not DATA_PATH.exists():
        return "Never"

    # Scan all categories
    for category_dir in DATA_PATH.iterdir():
        if not category_dir.is_dir():
            continue

        company_path = category_dir / company_slug
        if not company_path.exists():
            continue

        # Check for recent ad folders
        for ad_folder in company_path.iterdir():
            if not ad_folder.is_dir():
                continue

            meta_file = ad_folder / "meta.json"
            if meta_file.exists():
                try:
                    with open(meta_file, "r") as f:
                        meta = json.load(f)
                        ts = meta.get("timestamp", 0)
                        latest_timestamp = max(latest_timestamp, ts)
                except Exception:
                    pass

    if latest_timestamp == 0:
        return "Never"

    diff = int(time.time()) - latest_timestamp

    if diff < 60:
        return "Just now"
    elif diff < 3600:
        return f"{diff // 60} mins ago"
    elif diff < 86400:
        return f"{diff // 3600} hours ago"
    elif diff < 604800:
        return f"{diff // 86400} days ago"
    else:
        return datetime.fromtimestamp(latest_timestamp).strftime("%b %d, %Y")


@router.get("/admin/users")
async def get_users(db: Session = Depends(get_db)):
    """Get all users (companies) for admin dashboard"""
    try:
        users = []

        # Get from database
        companies = db.query(Company).order_by(Company.created_at.desc()).all()

        for company in companies:
            users.append({
                "id": company.company_slug,
                "name": company.company_name,
                "email": company.email or f"{company.company_slug}@example.com",
                "role": "Company",
                "status": company.status or "active",
                "created_at": str(company.created_at) if company.created_at else "",
                "lastActive": calculate_last_active(company.company_slug)
            })

        # Also check metadata files for any companies not in DB
        if METADATA_PATH.exists():
            db_slugs = {u["id"] for u in users}

            for meta_file in METADATA_PATH.glob("*.json"):
                company_slug = meta_file.stem
                if company_slug in db_slugs:
                    continue

                try:
                    with open(meta_file, "r") as f:
                        metadata = json.load(f)

                    users.append({
                        "id": company_slug,
                        "name": metadata.get("company_name", company_slug.title()),
                        "email": metadata.get("contact_email", f"{company_slug}@example.com"),
                        "role": "Company",
                        "status": metadata.get("status", "active"),
                        "created_at": metadata.get("created_at", ""),
                        "lastActive": calculate_last_active(company_slug)
                    })
                except Exception:
                    continue

        return {
            "success": True,
            "users": users,
            "total": len(users)
        }

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


@router.get("/admin/users/{user_id}")
async def get_user(user_id: str, db: Session = Depends(get_db)):
    """Get single user details"""
    try:
        company = db.query(Company).filter(Company.company_slug == user_id).first()

        if not company:
            return JSONResponse(
                status_code=404,
                content={"success": False, "error": "User not found"}
            )

        # Get ad stats
        ad_count = db.query(Ad).filter(Ad.company_slug == user_id).count()

        return {
            "success": True,
            "user": {
                "id": company.company_slug,
                "name": company.company_name,
                "email": company.email or "",
                "phone": company.phone or "",
                "status": company.status or "active",
                "created_at": str(company.created_at) if company.created_at else "",
                "ad_count": ad_count,
                "lastActive": calculate_last_active(company.company_slug)
            }
        }

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

