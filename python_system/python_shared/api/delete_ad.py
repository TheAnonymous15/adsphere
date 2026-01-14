"""
delete_ad.py - Delete Ad API
Handles single and bulk ad deletion
Converted from PHP to Python
"""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pathlib import Path
import shutil

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from models import Ad
from database import get_db

router = APIRouter()

DATA_PATH = Path(__file__).parent.parent / "companies" / "data"
ANALYTICS_PATH = Path(__file__).parent.parent / "companies" / "analytics"


def delete_directory(path: Path) -> bool:
    """Delete directory recursively - matches PHP deleteDirectory function"""
    if not path.is_dir():
        return False
    try:
        shutil.rmtree(path)
        return True
    except Exception:
        return False


@router.delete("/delete_ad/{ad_id}")
async def delete_ad(ad_id: str, db: Session = Depends(get_db)):
    """Delete an ad by ID"""
    try:
        # Find ad
        ad = db.query(Ad).filter(Ad.ad_id == ad_id).first()

        if not ad:
            return JSONResponse(
                status_code=404,
                content={"success": False, "error": "Ad not found"}
            )

        # Store info before deletion
        category = ad.category_slug
        company = ad.company_slug
        title = ad.title

        # Delete from database
        db.delete(ad)
        db.commit()

        # Delete media files
        if DATA_PATH.exists():
            ad_path = DATA_PATH / category / company / ad_id
            if ad_path.exists():
                delete_directory(ad_path)

        # Delete analytics file
        analytics_file = ANALYTICS_PATH / f"{ad_id}.json"
        if analytics_file.exists():
            analytics_file.unlink()

        return {
            "success": True,
            "message": f"Ad '{title}' deleted successfully",
            "ad_id": ad_id,
            "deleted_count": 1
        }

    except Exception as e:
        db.rollback()
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


@router.post("/delete_ad")
async def delete_ad_post(request: Request, db: Session = Depends(get_db)):
    """Delete ad(s) via POST request - matches PHP bulk deletion logic"""
    try:
        data = await request.json()

        # Support both single ad_id and bulk ad_ids (matching PHP logic)
        ad_ids = data.get("ad_ids", [])
        if not ad_ids and data.get("ad_id"):
            ad_ids = [data.get("ad_id")]

        # Ensure ad_ids is a list
        if not isinstance(ad_ids, list):
            ad_ids = [ad_ids]

        if not ad_ids:
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "No ad IDs provided"}
            )

        deleted_count = 0
        errors = []

        for ad_id in ad_ids:
            found = False

            # Try database first
            ad = db.query(Ad).filter(Ad.ad_id == ad_id).first()

            if ad:
                category = ad.category_slug
                company = ad.company_slug

                # Delete from database
                db.delete(ad)

                # Delete media files
                if DATA_PATH.exists():
                    ad_path = DATA_PATH / category / company / ad_id
                    if ad_path.exists():
                        delete_directory(ad_path)

                # Delete analytics
                analytics_file = ANALYTICS_PATH / f"{ad_id}.json"
                if analytics_file.exists():
                    analytics_file.unlink()

                deleted_count += 1
                found = True
            else:
                # Search for the ad in all categories (matching PHP file-based approach)
                if DATA_PATH.exists():
                    for category_dir in DATA_PATH.iterdir():
                        if not category_dir.is_dir():
                            continue
                        for company_dir in category_dir.iterdir():
                            if not company_dir.is_dir():
                                continue
                            ad_path = company_dir / ad_id
                            if ad_path.is_dir():
                                # Delete the entire ad directory
                                delete_directory(ad_path)
                                deleted_count += 1
                                found = True
                                break
                        if found:
                            break

            if not found:
                errors.append(f"Ad not found or unauthorized: {ad_id}")

        db.commit()

        # Response (matching PHP response format)
        if deleted_count > 0:
            return {
                "success": True,
                "message": f"{deleted_count} ad(s) deleted successfully",
                "deleted_count": deleted_count,
                "errors": errors
            }
        else:
            return JSONResponse(
                status_code=404,
                content={
                    "success": False,
                    "message": "No ads were deleted",
                    "errors": errors
                }
            )

    except Exception as e:
        db.rollback()
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )
