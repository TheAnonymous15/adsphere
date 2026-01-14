"""
============================================================================
COMPANY PORTAL SERVICE - Port 8003
============================================================================
Entry point for company users (advertisers)
Requires company authentication

Start: python app.py
============================================================================
"""

from fastapi import FastAPI, Request, HTTPException, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session
from pathlib import Path
from datetime import datetime
import hashlib
import json
import time
import secrets
import sys

# Add parent path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from models import Company, Ad, Category
    from database import SessionLocal, get_db
except ImportError:
    # Fallback - create stubs if imports fail
    Company = None
    Ad = None
    Category = None
    SessionLocal = None

    def get_db():
        yield None

# ============================================================================
# PATHS CONFIGURATION
# ============================================================================
BASE_PATH = Path(__file__).parent
PARENT_PATH = BASE_PATH.parent
TEMPLATES_PATH = BASE_PATH / "templates"
TEMPLATES_PATH.mkdir(exist_ok=True)
ASSETS_PATH = PARENT_PATH / "assets"
METADATA_PATH = BASE_PATH / "metadata"
DATA_PATH = BASE_PATH / "data"
ANALYTICS_PATH = BASE_PATH / "analytics"

# Create directories
METADATA_PATH.mkdir(exist_ok=True)
DATA_PATH.mkdir(exist_ok=True)
ANALYTICS_PATH.mkdir(exist_ok=True)

# ============================================================================
# APP INITIALIZATION
# ============================================================================
app = FastAPI(
    title="AdSphere Company Portal",
    description="Company dashboard for advertisers",
    version="1.0.0"
)

# Session middleware
app.add_middleware(
    SessionMiddleware,
    secret_key=secrets.token_hex(32),
    session_cookie="company_session",
    max_age=7200  # 2 hours
)

# Mount static files
if ASSETS_PATH.exists():
    app.mount("/assets", StaticFiles(directory=str(ASSETS_PATH)), name="assets")
    app.mount("/static", StaticFiles(directory=str(ASSETS_PATH)), name="static")

# Company data directory
if DATA_PATH.exists():
    app.mount("/company/data", StaticFiles(directory=str(DATA_PATH)), name="company_data")

# Setup Jinja2 templates
templates = Jinja2Templates(directory=str(TEMPLATES_PATH))

# ============================================================================
# AUTHENTICATION HELPERS
# ============================================================================
PUBLIC_ROUTES = ["/login", "/register", "/forgot-password", "/health", "/api/auth"]


def get_session_company(request: Request):
    """Get company from session"""
    return request.session.get("company")


def require_auth(request: Request):
    """Check if user is authenticated"""
    if not request.session.get("company_logged_in"):
        raise HTTPException(status_code=401, detail="Not authenticated")
    return request.session.get("company")


def check_rate_limit(email: str) -> dict:
    """Check login rate limit"""
    lock_file = Path(f"/tmp/login_attempts_{hashlib.md5(email.encode()).hexdigest()}.json")
    max_attempts = 5
    lockout_time = 900  # 15 minutes

    attempts = []
    if lock_file.exists():
        data = json.loads(lock_file.read_text())
        attempts = data.get("attempts", [])

        if "locked_until" in data and time.time() < data["locked_until"]:
            remaining = int((data["locked_until"] - time.time()) / 60) + 1
            return {"allowed": False, "message": f"Too many failed attempts. Try again in {remaining} minutes."}

    # Clean old attempts
    attempts = [t for t in attempts if time.time() - t < lockout_time]

    if len(attempts) >= max_attempts:
        lock_until = time.time() + lockout_time
        lock_file.write_text(json.dumps({"attempts": attempts, "locked_until": lock_until}))
        return {"allowed": False, "message": "Too many failed attempts. Account locked for 15 minutes."}

    return {"allowed": True}


def record_failed_attempt(email: str):
    """Record a failed login attempt"""
    lock_file = Path(f"/tmp/login_attempts_{hashlib.md5(email.encode()).hexdigest()}.json")

    attempts = []
    if lock_file.exists():
        data = json.loads(lock_file.read_text())
        attempts = data.get("attempts", [])

    attempts.append(time.time())
    lock_file.write_text(json.dumps({"attempts": attempts}))


def clear_failed_attempts(email: str):
    """Clear failed login attempts"""
    lock_file = Path(f"/tmp/login_attempts_{hashlib.md5(email.encode()).hexdigest()}.json")
    if lock_file.exists():
        lock_file.unlink()


def verify_password(input_password: str, company_data: dict) -> bool:
    """Verify password against stored hash"""
    if "password_hash" in company_data:
        import bcrypt
        return bcrypt.checkpw(input_password.encode(), company_data["password_hash"].encode())
    # Fallback for development
    return input_password == "1234"


# ============================================================================
# MIDDLEWARE - Auth Check
# ============================================================================
@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    """Check authentication for protected routes"""
    path = request.url.path

    # Skip auth for public routes and static files
    if any(path.startswith(route) for route in PUBLIC_ROUTES) or path.startswith("/assets") or path.startswith("/services"):
        return await call_next(request)

    # Check if authenticated
    if not request.session.get("company_logged_in"):
        if path.startswith("/api/"):
            return JSONResponse({"success": False, "error": "Unauthorized"}, status_code=401)
        return RedirectResponse(url="/login", status_code=302)

    # Check session timeout
    last_activity = request.session.get("last_activity", 0)
    if time.time() - last_activity > 7200:  # 2 hours
        request.session.clear()
        return RedirectResponse(url="/login?timeout=1", status_code=302)

    request.session["last_activity"] = time.time()
    return await call_next(request)


# ============================================================================
# PUBLIC ROUTES
# ============================================================================
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, timeout: int = None, error: str = None):
    """Login page"""
    if request.session.get("company_logged_in"):
        return RedirectResponse(url="/dashboard", status_code=302)

    return templates.TemplateResponse("login.html", {
        "request": request,
        "timeout": timeout,
        "error": error,
        "csrf_token": secrets.token_hex(16)
    })


@app.post("/login")
async def login_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    remember: bool = Form(False)
):
    """Process login"""
    # Rate limiting
    rate_check = check_rate_limit(email)
    if not rate_check["allowed"]:
        return RedirectResponse(url=f"/login?error={rate_check['message']}", status_code=302)

    # Find company by email
    company_data = None
    company_slug = None

    for meta_file in METADATA_PATH.glob("*.json"):
        data = json.loads(meta_file.read_text())
        if data.get("contact_email", "").lower() == email.lower():
            company_data = data
            company_slug = meta_file.stem
            break

    if not company_data:
        record_failed_attempt(email)
        return RedirectResponse(url="/login?error=Invalid email or password", status_code=302)

    # Verify password
    if not verify_password(password, company_data):
        record_failed_attempt(email)
        return RedirectResponse(url="/login?error=Invalid email or password", status_code=302)

    # Clear failed attempts and set session
    clear_failed_attempts(email)

    request.session["company_logged_in"] = True
    request.session["company"] = company_slug
    request.session["company_name"] = company_data.get("company_name", company_slug.title())
    request.session["company_email"] = email
    request.session["login_time"] = time.time()
    request.session["last_activity"] = time.time()

    return RedirectResponse(url="/dashboard", status_code=302)


@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """Registration page"""
    return templates.TemplateResponse("register.html", {
        "request": request
    })


@app.get("/forgot-password", response_class=HTMLResponse)
async def forgot_password_page(request: Request):
    """Forgot password page"""
    return templates.TemplateResponse("forgot_password.html", {
        "request": request
    })


@app.get("/logout")
async def logout(request: Request):
    """Logout and clear session"""
    request.session.clear()
    return RedirectResponse(url="/login", status_code=302)


# ============================================================================
# PROTECTED ROUTES
# ============================================================================
@app.get("/", response_class=HTMLResponse)
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    """Company dashboard"""
    company_slug = request.session.get("company")
    company_name = request.session.get("company_name", "Company")
    company_email = request.session.get("company_email", "")
    login_time = request.session.get("login_time", "Recently")

    # Load company data
    company_data = {}
    meta_file = METADATA_PATH / f"{company_slug}.json"
    if meta_file.exists():
        company_data = json.loads(meta_file.read_text())

    # Get categories from company data
    categories = company_data.get("categories", [])

    # Get stats from database (with fallback)
    total_ads = 0
    active_ads = 0

    if db and Ad:
        try:
            total_ads = db.query(Ad).filter(Ad.company_slug == company_slug).count()
            active_ads = db.query(Ad).filter(Ad.company_slug == company_slug, Ad.status == "active").count()
        except Exception:
            pass

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "company_slug": company_slug,
        "company_name": company_name,
        "company_email": company_email,
        "login_time": login_time,
        "company_data": company_data,
        "categories": categories,
        "total_ads": total_ads,
        "active_ads": active_ads,
        "current_year": datetime.now().year
    })


@app.get("/ads", response_class=HTMLResponse)
@app.get("/my-ads", response_class=HTMLResponse)
async def my_ads(request: Request, db: Session = Depends(get_db)):
    """My ads page"""
    company_slug = request.session.get("company")
    company_name = request.session.get("company_name", "Company")

    # Get categories (with fallback)
    categories = []
    if db and Category:
        try:
            categories = db.query(Category).all()
        except Exception:
            pass

    return templates.TemplateResponse("my_ads.html", {
        "request": request,
        "company_slug": company_slug,
        "company_name": company_name,
        "categories": categories,
        "current_year": datetime.now().year
    })


@app.get("/upload", response_class=HTMLResponse)
@app.get("/new-ad", response_class=HTMLResponse)
async def upload_ad(request: Request, db: Session = Depends(get_db)):
    """Upload new ad page"""
    company_slug = request.session.get("company")

    # Load company metadata
    company_data = {}
    meta_file = METADATA_PATH / f"{company_slug}.json"
    if meta_file.exists():
        company_data = json.loads(meta_file.read_text())

    # Get categories - first from company data, then from database
    categories = company_data.get("categories", [])

    # If categories is a list of strings, convert to dict format for template
    if categories and isinstance(categories[0], str):
        categories = [{"category_slug": cat, "category_name": cat.replace("-", " ").title()} for cat in categories]

    # If no categories from company data, try database
    if not categories and db and Category:
        try:
            db_categories = db.query(Category).all()
            categories = [{"category_slug": cat.category_slug, "category_name": cat.category_name} for cat in db_categories]
        except Exception:
            pass

    # Get flash message from session (if any)
    msg = request.session.pop("message", None)
    msg_type = request.session.pop("message_type", "success")

    return templates.TemplateResponse("upload_ad.html", {
        "request": request,
        "logged_company": company_slug,
        "categories": categories,
        "msg": msg,
        "msg_type": msg_type
    })


@app.get("/ad-upload", response_class=HTMLResponse)
async def ad_upload_page(request: Request, db: Session = Depends(get_db)):
    """Ad upload page (alternative design)"""
    company_slug = request.session.get("company")

    # Load company metadata
    company_data = {}
    meta_file = METADATA_PATH / f"{company_slug}.json"
    if meta_file.exists():
        company_data = json.loads(meta_file.read_text())

    # Get categories - first from company data, then from database
    categories = company_data.get("categories", [])

    # If categories is a list of strings, convert to dict format for template
    if categories and isinstance(categories[0], str):
        categories = [{"category_slug": cat, "category_name": cat.replace("-", " ").title()} for cat in categories]

    # If no categories from company data, try database
    if not categories and db and Category:
        try:
            db_categories = db.query(Category).all()
            categories = [{"category_slug": cat.category_slug, "category_name": cat.category_name} for cat in db_categories]
        except Exception:
            pass

    # Get flash message from session (if any)
    msg = request.session.pop("message", None)
    msg_type = request.session.pop("message_type", "success")

    return templates.TemplateResponse("ad_upload.html", {
        "request": request,
        "logged_company": company_slug,
        "categories": categories,
        "msg": msg,
        "msg_type": msg_type
    })


@app.get("/edit/{ad_id}", response_class=HTMLResponse)
async def edit_ad(request: Request, ad_id: str, db: Session = Depends(get_db)):
    """Edit ad page"""
    company_slug = request.session.get("company")
    company_name = request.session.get("company_name", "Company")

    ad = None
    categories = []

    if db and Ad and Category:
        try:
            ad = db.query(Ad).filter(Ad.ad_id == ad_id, Ad.company_slug == company_slug).first()
            categories = db.query(Category).all()
        except Exception:
            pass

    if not ad:
        raise HTTPException(status_code=404, detail="Ad not found")

    return templates.TemplateResponse("edit_ad.html", {
        "request": request,
        "company_slug": company_slug,
        "company_name": company_name,
        "ad": ad,
        "categories": categories,
        "current_year": datetime.now().year
    })


@app.get("/analytics", response_class=HTMLResponse)
@app.get("/company-analytics", response_class=HTMLResponse)
async def analytics(request: Request):
    """Analytics page"""
    company_slug = request.session.get("company")
    company_name = request.session.get("company_name", "Company")

    return templates.TemplateResponse("company_analytics.html", {
        "request": request,
        "company_slug": company_slug,
        "company_name": company_name,
        "current_year": datetime.now().year
    })


@app.get("/profile", response_class=HTMLResponse)
async def profile(request: Request):
    """Profile page"""
    company_slug = request.session.get("company")
    company_name = request.session.get("company_name", "Company")

    # Load company data
    company_data = {}
    meta_file = METADATA_PATH / f"{company_slug}.json"
    if meta_file.exists():
        company_data = json.loads(meta_file.read_text())

    return templates.TemplateResponse("profile.html", {
        "request": request,
        "company_slug": company_slug,
        "company_name": company_name,
        "company_data": company_data,
        "current_year": datetime.now().year
    })


@app.get("/settings", response_class=HTMLResponse)
async def settings(request: Request):
    """Settings page"""
    company_slug = request.session.get("company")
    company_name = request.session.get("company_name", "Company")

    return templates.TemplateResponse("settings.html", {
        "request": request,
        "company_slug": company_slug,
        "company_name": company_name,
        "current_year": datetime.now().year
    })


@app.get("/notifications", response_class=HTMLResponse)
async def notifications(request: Request):
    """Notifications page"""
    company_slug = request.session.get("company")
    company_name = request.session.get("company_name", "Company")

    return templates.TemplateResponse("notifications.html", {
        "request": request,
        "company_slug": company_slug,
        "company_name": company_name,
        "current_year": datetime.now().year
    })


# ============================================================================
# ERROR PAGES
# ============================================================================
@app.get("/403", response_class=HTMLResponse)
async def forbidden_page(request: Request):
    return templates.TemplateResponse("403.html", {"request": request}, status_code=403)


@app.get("/404", response_class=HTMLResponse)
async def not_found_page(request: Request):
    return templates.TemplateResponse("404.html", {"request": request}, status_code=404)


@app.get("/500", response_class=HTMLResponse)
async def server_error_page(request: Request):
    return templates.TemplateResponse("500.html", {"request": request}, status_code=500)


# ============================================================================
# HEALTH CHECK
# ============================================================================
@app.get("/health")
async def health_check(request: Request):
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "company",
        "port": 8003,
        "authenticated": request.session.get("company_logged_in", False),
        "company": request.session.get("company"),
        "timestamp": datetime.now().isoformat()
    }


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================
if __name__ == "__main__":
    import uvicorn
    print("🏢 Starting AdSphere Company Portal on Port 8003...")
    uvicorn.run(app, host="0.0.0.0", port=8003, reload=False)

