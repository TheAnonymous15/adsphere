"""
============================================================================
COMPANY HANDLERS - Python Route Handlers
============================================================================
Converted from PHP handlers to Python FastAPI/Flask compatible handlers
Handles: ad_upload, login, logout, register_company, update_ad, save_metadata
"""

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File, Form
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime, timezone
from pathlib import Path
from PIL import Image
import shutil
import os
import io
import secrets
import hashlib
import json

# Import from parent
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from database import get_db
from models import Ad, Company, Category, get_current_timestamp
from auth import get_current_company, AuthService, PasswordService

# Create router
router = APIRouter(tags=["Company Handlers"])

# Base paths
DATA_BASE = Path(__file__).parent.parent / "data"
META_BASE = Path(__file__).parent.parent / "metadata"


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def generate_ad_id() -> str:
    """Generate unique ad ID: AD-YYYYMM-HHMMSSXXXX-RANDOM"""
    now = datetime.now(timezone.utc)
    chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    rand = ''.join(secrets.choice(chars) for _ in range(5))
    return f"AD-{now.strftime('%Y%m')}-{now.strftime('%H%M%S%f')[:10]}-{rand}"


def generate_slug(name: str) -> str:
    """Generate URL-friendly slug from name"""
    import re
    slug = name.lower()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'\s+', '-', slug)
    return slug.strip('-')


def compress_image(source_path: Path, dest_path: Path, max_size_kb: int = 1024, quality: int = 90) -> bool:
    """
    Compress image to under max_size_kb while maintaining quality.
    Always saves as JPEG for consistency.
    """
    try:
        with Image.open(source_path) as img:
            # Convert to RGB if necessary (for PNG with transparency)
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')

            # Get original dimensions
            width, height = img.size
            max_dimension = 1920

            # Resize if too large
            if width > max_dimension or height > max_dimension:
                ratio = min(max_dimension / width, max_dimension / height)
                new_size = (int(width * ratio), int(height * ratio))
                img = img.resize(new_size, Image.Resampling.LANCZOS)

            # Progressive compression until under max size
            current_quality = quality
            while current_quality > 40:
                buffer = io.BytesIO()
                img.save(buffer, format='JPEG', quality=current_quality, optimize=True)
                size_kb = buffer.tell() / 1024

                if size_kb <= max_size_kb:
                    # Save to file
                    with open(dest_path, 'wb') as f:
                        buffer.seek(0)
                        f.write(buffer.read())
                    return True

                current_quality -= 5

            # Save with minimum quality if still too large
            img.save(dest_path, format='JPEG', quality=40, optimize=True)
            return dest_path.stat().st_size <= (max_size_kb * 1024)

    except Exception as e:
        print(f"Image compression error: {e}")
        return False


def check_rate_limit(identifier: str, max_attempts: int = 5, lockout_minutes: int = 15) -> dict:
    """Simple file-based rate limiting"""
    import tempfile

    lock_file = Path(tempfile.gettempdir()) / f"login_attempts_{hashlib.md5(identifier.encode()).hexdigest()}.json"
    lockout_seconds = lockout_minutes * 60

    attempts = []
    locked_until = None

    if lock_file.exists():
        try:
            data = json.loads(lock_file.read_text())
            attempts = data.get('attempts', [])
            locked_until = data.get('locked_until')

            # Check if locked
            if locked_until and datetime.now(timezone.utc).timestamp() < locked_until:
                remaining = int((locked_until - datetime.now(timezone.utc).timestamp()) / 60) + 1
                return {
                    'allowed': False,
                    'message': f"Too many failed attempts. Please try again in {remaining} minutes."
                }
        except:
            pass

    # Clean old attempts
    now = datetime.now(timezone.utc).timestamp()
    attempts = [t for t in attempts if now - t < lockout_seconds]

    if len(attempts) >= max_attempts:
        lock_until = now + lockout_seconds
        lock_file.write_text(json.dumps({
            'attempts': attempts,
            'locked_until': lock_until
        }))
        return {
            'allowed': False,
            'message': "Too many failed attempts. Account locked for 15 minutes."
        }

    return {'allowed': True}


def record_failed_attempt(identifier: str):
    """Record a failed login attempt"""
    import tempfile

    lock_file = Path(tempfile.gettempdir()) / f"login_attempts_{hashlib.md5(identifier.encode()).hexdigest()}.json"

    attempts = []
    if lock_file.exists():
        try:
            data = json.loads(lock_file.read_text())
            attempts = data.get('attempts', [])
        except:
            pass

    attempts.append(datetime.now(timezone.utc).timestamp())
    lock_file.write_text(json.dumps({'attempts': attempts}))


def clear_failed_attempts(identifier: str):
    """Clear failed login attempts after successful login"""
    import tempfile

    lock_file = Path(tempfile.gettempdir()) / f"login_attempts_{hashlib.md5(identifier.encode()).hexdigest()}.json"
    if lock_file.exists():
        lock_file.unlink()


# ============================================================================
# LOGIN HANDLER
# ============================================================================

@router.post("/login")
async def handle_login(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Handle company login
    Expects: email, password
    Returns: JWT token on success
    """
    try:
        # Get form data or JSON
        try:
            data = await request.json()
        except:
            form = await request.form()
            data = dict(form)

        email = data.get('email', '').strip()
        password = data.get('password', '')

        # Validate inputs
        if not email or not password:
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "Please enter both email and password."}
            )

        # Check rate limit
        rate_check = check_rate_limit(email)
        if not rate_check['allowed']:
            return JSONResponse(
                status_code=429,
                content={"success": False, "error": rate_check['message']}
            )

        # Find company by email
        company = db.query(Company).filter(Company.email == email).first()

        if not company:
            record_failed_attempt(email)
            return JSONResponse(
                status_code=401,
                content={"success": False, "error": "Invalid email or password."}
            )

        # Verify password
        if company.password_hash:
            if not PasswordService.verify_password(password, company.password_hash):
                record_failed_attempt(email)
                return JSONResponse(
                    status_code=401,
                    content={"success": False, "error": "Invalid email or password."}
                )
        else:
            # Temporary fallback - remove in production
            if password != "1234":
                record_failed_attempt(email)
                return JSONResponse(
                    status_code=401,
                    content={"success": False, "error": "Invalid email or password."}
                )

        # Clear failed attempts
        clear_failed_attempts(email)

        # Generate token
        token = AuthService.create_company_token(company.company_slug, company.company_name)

        return {
            "success": True,
            "message": "Login successful",
            "token": token,
            "company_slug": company.company_slug,
            "company_name": company.company_name,
            "redirect": "/dashboard"
        }

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


# ============================================================================
# LOGOUT HANDLER
# ============================================================================

@router.post("/logout")
@router.get("/logout")
async def handle_logout():
    """
    Handle logout - client should discard token
    """
    return {
        "success": True,
        "message": "Logged out successfully. Please discard your token.",
        "redirect": "/login"
    }


# ============================================================================
# REGISTER COMPANY HANDLER
# ============================================================================

@router.post("/register")
async def handle_register_company(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Register a new company
    Creates entry in database + file system for backward compatibility
    """
    try:
        # Get form data or JSON
        try:
            data = await request.json()
        except:
            form = await request.form()
            data = dict(form)

        company_name = data.get('company_name', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        phone = data.get('phone', '').strip()
        sms = data.get('sms', '').strip()
        whatsapp = data.get('whatsapp', '').strip()
        website = data.get('website', '').strip()
        description = data.get('description', '').strip()
        category = data.get('category', '').strip()

        # Validate required fields
        if not company_name:
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "Company name is required"}
            )

        if not email:
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "Email is required"}
            )

        if not category:
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "Please select a category"}
            )

        # Generate slug
        company_slug = generate_slug(company_name)

        # Check if company exists
        existing = db.query(Company).filter(
            (Company.company_slug == company_slug) | (Company.email == email)
        ).first()

        if existing:
            if existing.email == email:
                return JSONResponse(
                    status_code=400,
                    content={"success": False, "error": "Email already registered"}
                )
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "Company with this name already exists"}
            )

        # Hash password
        password_hash = PasswordService.hash_password(password) if password else None

        # Create company in database
        new_company = Company(
            company_slug=company_slug,
            company_name=company_name,
            email=email,
            phone=phone or None,
            sms=sms or None,
            whatsapp=whatsapp or None,
            website=website or None,
            description=description or None,
            password_hash=password_hash,
            status='active',
            created_at=get_current_timestamp(),
            updated_at=get_current_timestamp()
        )

        db.add(new_company)
        db.commit()

        # Create metadata file for backward compatibility
        META_BASE.mkdir(parents=True, exist_ok=True)
        meta_data = {
            "company_name": company_name,
            "company_slug": company_slug,
            "email": email,
            "website": website,
            "description": description,
            "contact": {
                "phone": phone,
                "sms": sms,
                "email": email,
                "whatsapp": whatsapp
            },
            "categories": [category],
            "created_at": datetime.now(timezone.utc).isoformat()
        }

        meta_file = META_BASE / f"{company_slug}.json"
        meta_file.write_text(json.dumps(meta_data, indent=2))

        # Create company directories
        for cat in [category]:
            cat_dir = DATA_BASE / cat / company_slug
            cat_dir.mkdir(parents=True, exist_ok=True)

        return {
            "success": True,
            "message": "Company registered successfully",
            "company_slug": company_slug,
            "redirect": "/login"
        }

    except Exception as e:
        db.rollback()
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


# ============================================================================
# AD UPLOAD HANDLER
# ============================================================================

@router.post("/upload_ad")
async def handle_ad_upload(
    request: Request,
    title: str = Form(...),
    description: str = Form(""),
    category: str = Form(...),
    phone: str = Form(""),
    whatsapp: str = Form(""),
    email: str = Form(""),
    sms: str = Form(""),
    db: Session = Depends(get_db),
    current_company: dict = Depends(get_current_company)
):
    """
    Handle ad upload with image compression
    Supports: up to 4 images or 1 video
    Images are compressed to <1MB
    """
    company_slug = current_company.get("sub")
    uploaded_files = []
    ad_dir = None

    try:
        # Validate required fields
        if not title.strip():
            raise HTTPException(status_code=400, detail="Title is required")

        if not category:
            raise HTTPException(status_code=400, detail="Category is required")

        # Generate ad ID
        ad_id = generate_ad_id()

        # Create ad directory
        ad_dir = DATA_BASE / category / company_slug / ad_id
        ad_dir.mkdir(parents=True, exist_ok=True)

        # Get uploaded files from form
        form = await request.form()
        media_files = []

        # Check for media files (media_0, media_1, etc.)
        for i in range(4):
            file = form.get(f'media_{i}')
            if file and hasattr(file, 'filename') and file.filename:
                media_files.append(file)

        # Also check for single 'media' field
        single_media = form.get('media')
        if single_media and hasattr(single_media, 'filename') and single_media.filename:
            media_files.append(single_media)

        if not media_files:
            raise HTTPException(status_code=400, detail="Please upload at least one image or video")

        # Determine media type
        first_file = media_files[0]
        is_video = first_file.content_type and first_file.content_type.startswith('video/')

        media_info = {'type': 'video' if is_video else 'image', 'files': [], 'primary': ''}

        if is_video:
            # Handle video upload (only 1 allowed)
            file = media_files[0]
            ext = Path(file.filename).suffix.lower()
            allowed_video_exts = ['.mp4', '.webm', '.mov', '.avi', '.mkv']

            if ext not in allowed_video_exts:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported video format. Allowed: {', '.join(allowed_video_exts)}"
                )

            video_name = f"{ad_id}{ext}"
            dest_path = ad_dir / video_name

            # Save video
            content = await file.read()
            dest_path.write_bytes(content)

            uploaded_files.append(video_name)
            media_info['files'] = [video_name]
            media_info['primary'] = video_name

        else:
            # Handle image uploads (up to 4)
            allowed_image_exts = ['.jpg', '.jpeg', '.png', '.gif', '.webp']

            for i, file in enumerate(media_files[:4]):
                ext = Path(file.filename).suffix.lower()

                if ext not in allowed_image_exts:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Unsupported image format for image {i+1}"
                    )

                # Save to temp then compress
                image_name = f"{ad_id}_{i+1}.jpg"  # Always save as JPG
                temp_path = ad_dir / f"temp_{i}{ext}"
                dest_path = ad_dir / image_name

                # Save temp file
                content = await file.read()
                temp_path.write_bytes(content)

                # Check if compression needed
                file_size_kb = temp_path.stat().st_size / 1024

                if file_size_kb <= 1024 and ext in ['.jpg', '.jpeg']:
                    # Already small enough, just rename
                    temp_path.rename(dest_path)
                else:
                    # Compress image
                    if not compress_image(temp_path, dest_path, 1024, 90):
                        # Try harder compression
                        compress_image(temp_path, dest_path, 1024, 75)

                    # Clean up temp
                    if temp_path.exists():
                        temp_path.unlink()

                uploaded_files.append(image_name)

            media_info['files'] = uploaded_files
            media_info['primary'] = uploaded_files[0] if uploaded_files else ''

        # Create ad in database
        new_ad = Ad(
            ad_id=ad_id,
            company_slug=company_slug,
            category_slug=category,
            title=title.strip(),
            description=description.strip(),
            media_type=media_info['type'],
            media_path=f"{category}/{company_slug}/{ad_id}/{media_info['primary']}",
            contact_phone=phone or None,
            contact_email=email or None,
            contact_whatsapp=whatsapp or None,
            status='active',
            created_at=get_current_timestamp()
        )

        db.add(new_ad)
        db.commit()

        # Create meta.json for backward compatibility
        meta_data = {
            "ad_id": ad_id,
            "title": title.strip(),
            "description": description.strip(),
            "category": category,
            "company": company_slug,
            "media": media_info['files'],
            "media_type": media_info['type'],
            "primary_media": media_info['primary'],
            "timestamp": int(datetime.now(timezone.utc).timestamp()),
            "contact": {
                "phone": phone or None,
                "sms": sms or None,
                "email": email or None,
                "whatsapp": whatsapp or None
            }
        }

        meta_file = ad_dir / "meta.json"
        meta_file.write_text(json.dumps(meta_data, indent=2))

        return {
            "success": True,
            "message": f"Ad published successfully with {len(uploaded_files)} file(s)",
            "ad_id": ad_id,
            "redirect": "/my-ads"
        }

    except HTTPException:
        raise
    except Exception as e:
        # Rollback: delete uploaded files
        db.rollback()
        if ad_dir and ad_dir.exists():
            shutil.rmtree(ad_dir, ignore_errors=True)

        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


# ============================================================================
# UPDATE AD HANDLER
# ============================================================================

@router.post("/update_ad")
async def handle_update_ad(
    request: Request,
    db: Session = Depends(get_db),
    current_company: dict = Depends(get_current_company)
):
    """
    Update an existing ad
    """
    company_slug = current_company.get("sub")

    try:
        # Get form data
        form = await request.form()

        ad_id = form.get('ad_id', '')
        old_category = form.get('old_category', '')
        new_category = form.get('category', '')
        title = form.get('title', '').strip()
        description = form.get('description', '').strip()

        # Validate required fields
        if not ad_id or not new_category or not title:
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "Missing required fields"}
            )

        # Find ad in database
        ad = db.query(Ad).filter(
            Ad.ad_id == ad_id,
            Ad.company_slug == company_slug
        ).first()

        if not ad:
            return JSONResponse(
                status_code=404,
                content={"success": False, "error": "Ad not found or unauthorized"}
            )

        # Update ad fields
        ad.title = title
        ad.description = description
        ad.category_slug = new_category
        ad.updated_at = get_current_timestamp()

        # Handle media upload if provided
        media_file = form.get('media')
        if media_file and hasattr(media_file, 'filename') and media_file.filename:
            old_ad_path = DATA_BASE / old_category / company_slug / ad_id

            # Save new media
            ext = Path(media_file.filename).suffix.lower()
            new_media_name = f"{ad_id}{ext}"
            dest_path = old_ad_path / new_media_name

            content = await media_file.read()
            dest_path.write_bytes(content)

            ad.media_path = f"{new_category}/{company_slug}/{ad_id}/{new_media_name}"

        # Handle category change
        if old_category and old_category != new_category:
            old_ad_path = DATA_BASE / old_category / company_slug / ad_id
            new_ad_path = DATA_BASE / new_category / company_slug / ad_id

            if old_ad_path.exists():
                new_ad_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(old_ad_path), str(new_ad_path))

                # Update media path
                if ad.media_path:
                    media_filename = Path(ad.media_path).name
                    ad.media_path = f"{new_category}/{company_slug}/{ad_id}/{media_filename}"

        db.commit()

        # Update meta.json
        ad_path = DATA_BASE / new_category / company_slug / ad_id
        meta_file = ad_path / "meta.json"

        if meta_file.exists():
            meta = json.loads(meta_file.read_text())
            meta['title'] = title
            meta['description'] = description
            meta['category'] = new_category
            meta['updated_at'] = int(datetime.now(timezone.utc).timestamp())
            meta_file.write_text(json.dumps(meta, indent=2))

        return {
            "success": True,
            "message": "Ad updated successfully",
            "ad_id": ad_id,
            "redirect": f"/edit-ad?id={ad_id}"
        }

    except Exception as e:
        db.rollback()
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


# ============================================================================
# SAVE METADATA HANDLER (Legacy support)
# ============================================================================

@router.post("/save_metadata")
async def handle_save_metadata(request: Request):
    """
    Legacy endpoint for saving company metadata to file
    """
    try:
        form = await request.form()

        company_name = form.get('company_name', '').strip()
        if not company_name:
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "company_name is required"}
            )

        # Generate slug
        slug = generate_slug(company_name)

        # Build metadata
        meta = {
            "company_name": company_name,
            "slug": slug,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "website": form.get('website', ''),
            "description": form.get('description', ''),
            "contact": {
                "phone": form.get('phone', ''),
                "sms": form.get('sms', ''),
                "email": form.get('email', ''),
                "whatsapp": form.get('whatsapp', '')
            },
            "promotion": {
                "allow_social_share": bool(form.get('promo_social')),
                "allow_featured": bool(form.get('promo_featured'))
            },
            "categories": form.getlist('categories') if hasattr(form, 'getlist') else []
        }

        # Save to file
        META_BASE.mkdir(parents=True, exist_ok=True)
        save_path = META_BASE / f"{slug}.json"
        save_path.write_text(json.dumps(meta, indent=2))

        # Create directories for categories
        categories = meta.get('categories', [])
        for cat in categories:
            cat_dir = DATA_BASE / cat / slug
            cat_dir.mkdir(parents=True, exist_ok=True)

        return {
            "success": True,
            "message": "Company registered successfully",
            "slug": slug,
            "saved_to": str(save_path)
        }

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": str(e)}
        )

