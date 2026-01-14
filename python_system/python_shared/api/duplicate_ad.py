"""
duplicate_ad.py - Duplicate Ad API
Create a copy of an existing ad
Converted from PHP to Python
"""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from datetime import datetime
from pathlib import Path
import shutil
import uuid

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from models import Ad
from database import get_db

router = APIRouter()

DATA_PATH = Path(__file__).parent.parent / "companies" / "data"


def generate_ad_id() -> str:
    """Generate unique ad ID"""
    now = datetime.now()
    unique = uuid.uuid4().hex[:5].upper()
    return f"AD-{now.strftime('%Y%m')}-{now.strftime('%d%H%M%S%f')[:10]}-{unique}"


@router.post("/duplicate_ad")
async def duplicate_ad(request: Request, db: Session = Depends(get_db)):
    """Duplicate an existing ad"""
    try:
        data = await request.json()
        ad_id = data.get("ad_id", "")

        if not ad_id:
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "Missing ad_id"}
            )

        # Find original ad
        original = db.query(Ad).filter(Ad.ad_id == ad_id).first()

        if not original:
            return JSONResponse(
                status_code=404,
                content={"success": False, "error": "Ad not found"}
            )

        # Generate new ID
        new_ad_id = generate_ad_id()

        # Create duplicate
        duplicate = Ad(
            ad_id=new_ad_id,
            title=f"{original.title} (Copy)",
            description=original.description,
            category_slug=original.category_slug,
            company_slug=original.company_slug,
            status="draft",  # New ads start as draft
            media_type=original.media_type,
            contact_phone=original.contact_phone,
            contact_sms=original.contact_sms,
            contact_email=original.contact_email,
            contact_whatsapp=original.contact_whatsapp,
            views_count=0,
            likes_count=0,
            favorites_count=0,
            contacts_count=0,
            created_at=datetime.now()
        )

        # Copy media files if they exist
        if original.media_path:
            original_path = DATA_PATH / original.category_slug / original.company_slug / ad_id
            new_path = DATA_PATH / original.category_slug / original.company_slug / new_ad_id

            if original_path.exists():
                shutil.copytree(original_path, new_path)

                # Update media path
                duplicate.media_path = f"{original.category_slug}/{original.company_slug}/{new_ad_id}/{original.media_filename}"
                duplicate.media_filename = original.media_filename

        db.add(duplicate)
        db.commit()

        return {
            "success": True,
            "message": "Ad duplicated successfully",
            "original_id": ad_id,
            "new_id": new_ad_id
        }

    except Exception as e:
        db.rollback()
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

