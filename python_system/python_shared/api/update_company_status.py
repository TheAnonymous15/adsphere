"""
update_company_status.py - Update Company Status API
Handles company status changes
Converted from PHP to Python
"""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from datetime import datetime

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from models import Company, Ad
from database import get_db

router = APIRouter()

# Map actions to statuses (matching PHP logic)
STATUS_MAP = {
    'suspend': 'suspended',
    'activate': 'active',
    'block': 'blocked',
    'unblock': 'active',
    'verify': 'verified'
}


@router.post("/update_company_status")
async def update_company_status(request: Request, db: Session = Depends(get_db)):
    """Update company status - matches PHP logic exactly"""
    try:
        # Support both JSON and form data (like PHP does with $_POST)
        content_type = request.headers.get("content-type", "")

        if "application/json" in content_type:
            data = await request.json()
            company_slug = data.get("company_slug", "")
            action = data.get("action", "")
        else:
            form = await request.form()
            company_slug = form.get("company_slug", "")
            action = form.get("action", "")

        if not company_slug or not action:
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "Missing required parameters"}
            )

        # Validate action
        if action not in STATUS_MAP:
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "Invalid action"}
            )

        new_status = STATUS_MAP[action]

        # Find company
        company = db.query(Company).filter(Company.company_slug == company_slug).first()

        if not company:
            return JSONResponse(
                status_code=404,
                content={"success": False, "error": "Company not found"}
            )

        # Update company status
        company.status = new_status
        company.updated_at = datetime.now()

        # If blocking, also deactivate all their ads (matching PHP logic)
        if action == 'block':
            db.query(Ad).filter(Ad.company_slug == company_slug).update(
                {"status": "inactive"},
                synchronize_session=False
            )

        # If activating/unblocking, reactivate their ads (matching PHP logic)
        if action in ['activate', 'unblock']:
            db.query(Ad).filter(Ad.company_slug == company_slug).update(
                {"status": "active"},
                synchronize_session=False
            )

        db.commit()

        return {
            "success": True,
            "message": f"Company {action}d successfully",
            "company_slug": company_slug,
            "new_status": new_status
        }

    except Exception as e:
        db.rollback()
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


@router.post("/update_company_status/{company_slug}/{action}")
async def update_company_status_path(
    company_slug: str,
    action: str,
    db: Session = Depends(get_db)
):
    """Update company status via path parameters"""
    try:
        if action not in STATUS_MAP:
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "Invalid action"}
            )

        new_status = STATUS_MAP[action]

        company = db.query(Company).filter(Company.company_slug == company_slug).first()

        if not company:
            return JSONResponse(
                status_code=404,
                content={"success": False, "error": "Company not found"}
            )

        company.status = new_status
        company.updated_at = datetime.now()

        # Handle related ads
        if action == 'block':
            db.query(Ad).filter(Ad.company_slug == company_slug).update(
                {"status": "inactive"},
                synchronize_session=False
            )
        elif action in ['activate', 'unblock']:
            db.query(Ad).filter(Ad.company_slug == company_slug).update(
                {"status": "active"},
                synchronize_session=False
            )

        db.commit()

        return {
            "success": True,
            "message": f"Company {action}d successfully",
            "company_slug": company_slug,
            "new_status": new_status
        }

    except Exception as e:
        db.rollback()
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

