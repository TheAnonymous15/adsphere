"""
Admin Service - FastAPI Application
Port 8002 - Platform administrators panel
"""

from fastapi import FastAPI, Request, Depends, HTTPException, Form, Response
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from pathlib import Path
import secrets
import json
import time
import hashlib
import hmac
import sqlite3
import os

# App setup
app = FastAPI(title="AdSphere Admin", docs_url="/api/docs")

# Session middleware
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SESSION_SECRET", secrets.token_hex(32)),
    session_cookie="admin_session",
    max_age=3600,  # 1 hour
    same_site="strict",
    https_only=False  # Set to True in production with HTTPS
)

# Templates setup
BASE_DIR = Path(__file__).parent
TEMPLATES_DIR = BASE_DIR / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Static files
STATIC_DIR = BASE_DIR / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Data paths
DATA_DIR = BASE_DIR / "data"
CONFIG_DIR = BASE_DIR / "config"
LOGS_DIR = BASE_DIR / "companies" / "logs"
DATA_DIR.mkdir(exist_ok=True)
CONFIG_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Security config
SECURITY_CONFIG = {
    "max_attempts": 5,
    "lockout_duration": 900,  # 15 minutes
    "session_lifetime": 3600,  # 1 hour
    "enable_2fa": True,
    "require_2fa_for_admins": True,
    "login_delay": 2,
}

# Database paths
SECURITY_DB = DATA_DIR / "security.db"
ADMINS_FILE = CONFIG_DIR / "admins.json"
SECRETS_FILE = CONFIG_DIR / "2fa_secrets.json"

# Initialize security database
def init_security_db():
    conn = sqlite3.connect(str(SECURITY_DB))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS login_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            ip_address TEXT NOT NULL,
            attempt_time INTEGER NOT NULL,
            success INTEGER DEFAULT 0,
            user_agent TEXT
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_username_ip ON login_attempts(username, ip_address)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_attempt_time ON login_attempts(attempt_time)")
    conn.commit()
    conn.close()

init_security_db()


# Helper functions
def get_client_ip(request: Request) -> str:
    """Get client IP address"""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def load_admins() -> dict:
    """Load admin users from JSON file"""
    if ADMINS_FILE.exists():
        return json.loads(ADMINS_FILE.read_text())
    # Default admin if no file exists
    default_admin = {
        "admin": {
            "username": "admin",
            "password_hash": hashlib.sha256("admin123".encode()).hexdigest(),
            "role": "super_admin",
            "email": "admin@adsphere.com",
            "2fa_enabled": False,
            "created_at": int(time.time())
        }
    }
    ADMINS_FILE.write_text(json.dumps(default_admin, indent=2))
    return default_admin


def load_2fa_secrets() -> dict:
    """Load 2FA secrets"""
    if SECRETS_FILE.exists():
        return json.loads(SECRETS_FILE.read_text())
    return {}


def save_2fa_secrets(secrets: dict):
    """Save 2FA secrets"""
    SECRETS_FILE.write_text(json.dumps(secrets, indent=2))


def check_rate_limit(username: str, ip: str) -> dict:
    """Check login rate limiting"""
    conn = sqlite3.connect(str(SECURITY_DB))
    now = int(time.time())
    window = now - 3600

    # Clean old attempts
    conn.execute("DELETE FROM login_attempts WHERE attempt_time < ?", (window,))
    conn.commit()

    # Count failed attempts
    cursor = conn.execute("""
        SELECT COUNT(*) as count, MAX(attempt_time) as last_attempt
        FROM login_attempts
        WHERE username = ? AND ip_address = ? AND success = 0 AND attempt_time > ?
    """, (username, ip, window))
    row = cursor.fetchone()
    conn.close()

    failed_count = row[0] or 0
    last_attempt = row[1] or 0

    if failed_count >= SECURITY_CONFIG["max_attempts"]:
        lockout_end = last_attempt + SECURITY_CONFIG["lockout_duration"]
        if now < lockout_end:
            return {
                "locked": True,
                "remaining_time": (lockout_end - now) // 60 + 1,
                "failed_count": failed_count
            }

    return {"locked": False, "failed_count": failed_count}


def record_login_attempt(username: str, ip: str, success: bool, user_agent: str):
    """Record a login attempt"""
    conn = sqlite3.connect(str(SECURITY_DB))
    conn.execute("""
        INSERT INTO login_attempts (username, ip_address, attempt_time, success, user_agent)
        VALUES (?, ?, ?, ?, ?)
    """, (username, ip, int(time.time()), 1 if success else 0, user_agent))
    conn.commit()
    conn.close()


def clear_failed_attempts(username: str, ip: str):
    """Clear failed login attempts"""
    conn = sqlite3.connect(str(SECURITY_DB))
    conn.execute("""
        DELETE FROM login_attempts WHERE username = ? AND ip_address = ? AND success = 0
    """, (username, ip))
    conn.commit()
    conn.close()


def verify_password(stored_hash: str, password: str) -> bool:
    """Verify password using constant-time comparison"""
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    return hmac.compare_digest(stored_hash, password_hash)


def generate_totp_secret() -> str:
    """Generate a new TOTP secret"""
    chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567"
    return "".join(secrets.choice(chars) for _ in range(32))


def base32_decode(input_str: str) -> bytes:
    """Decode base32 string"""
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567"
    output = bytearray()
    buffer = 0
    bits_left = 0

    for char in input_str.upper():
        val = alphabet.find(char)
        if val == -1:
            continue
        buffer = (buffer << 5) | val
        bits_left += 5
        if bits_left >= 8:
            bits_left -= 8
            output.append((buffer >> bits_left) & 0xFF)

    return bytes(output)


def get_totp_code(secret: str, time_slice: int) -> str:
    """Generate TOTP code"""
    import struct
    secret_key = base32_decode(secret)
    time_bytes = struct.pack(">Q", time_slice)
    h = hmac.new(secret_key, time_bytes, "sha1").digest()
    offset = h[-1] & 0x0F
    code = ((h[offset] & 0x7F) << 24 |
            (h[offset + 1] & 0xFF) << 16 |
            (h[offset + 2] & 0xFF) << 8 |
            (h[offset + 3] & 0xFF)) % 1000000
    return str(code).zfill(6)


def verify_totp(secret: str, code: str, window: int = 1) -> bool:
    """Verify TOTP code"""
    time_slice = int(time.time()) // 30
    code = code.replace(" ", "").zfill(6)

    for i in range(-window, window + 1):
        calculated = get_totp_code(secret, time_slice + i)
        if hmac.compare_digest(calculated, code):
            return True
    return False


def log_security_event(event: str, username: str, status: str, ip: str):
    """Log security events"""
    log_file = LOGS_DIR / f"security_{time.strftime('%Y-%m-%d')}.log"
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {event} | User: {username} | IP: {ip} | Status: {status}\n"
    with open(log_file, "a") as f:
        f.write(log_entry)


# Auth dependency
async def require_auth(request: Request):
    """Require admin authentication"""
    session = request.session
    if not session.get("admin_logged_in"):
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Check 2FA
    if SECURITY_CONFIG["require_2fa_for_admins"] and not session.get("admin_2fa_verified"):
        raise HTTPException(status_code=401, detail="2FA required")

    # Check session timeout
    last_activity = session.get("admin_last_activity", 0)
    if time.time() - last_activity > SECURITY_CONFIG["session_lifetime"]:
        session.clear()
        raise HTTPException(status_code=401, detail="Session expired")

    session["admin_last_activity"] = int(time.time())
    return session


# Template context helper
def get_template_context(request: Request, **kwargs) -> dict:
    """Build template context with common data"""
    session = request.session
    return {
        "request": request,
        "admin_username": session.get("admin_username", "Admin"),
        "admin_role": session.get("admin_role", "admin"),
        "is_super_admin": session.get("admin_role") == "super_admin",
        "current_page": request.url.path.strip("/") or "dashboard",
        **kwargs
    }


# ============================================
# PUBLIC ROUTES (No auth required)
# ============================================

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Root redirect"""
    if request.session.get("admin_logged_in"):
        if not request.session.get("admin_2fa_verified"):
            return RedirectResponse(url="/2fa", status_code=302)
        return RedirectResponse(url="/dashboard", status_code=302)
    return RedirectResponse(url="/login", status_code=302)


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, logout: str = None, timeout: str = None):
    """Login page"""
    error_msg = ""
    success_msg = ""

    if logout == "1":
        success_msg = "You have been logged out successfully."
    if timeout == "1":
        error_msg = "Your session has expired. Please login again."

    # Generate CSRF token
    if "csrf_token" not in request.session:
        request.session["csrf_token"] = secrets.token_hex(32)

    return templates.TemplateResponse("login.html", {
        "request": request,
        "error_msg": error_msg,
        "success_msg": success_msg,
        "csrf_token": request.session["csrf_token"]
    })


@app.post("/login")
async def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    csrf_token: str = Form(...)
):
    """Handle login form submission"""
    ip = get_client_ip(request)
    user_agent = request.headers.get("user-agent", "Unknown")

    # Verify CSRF
    if csrf_token != request.session.get("csrf_token"):
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error_msg": "Invalid request. Please try again.",
            "csrf_token": request.session.get("csrf_token", "")
        })

    # Check rate limiting
    rate_check = check_rate_limit(username, ip)
    if rate_check["locked"]:
        log_security_event("LOGIN_BLOCKED", username, "rate_limited", ip)
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error_msg": f"Account locked. Try again in {rate_check['remaining_time']} minutes.",
            "csrf_token": request.session.get("csrf_token", "")
        })

    # Verify credentials
    admins = load_admins()
    admin = admins.get(username)

    generic_error = "Invalid credentials or too many failed attempts. Please try again."

    if not admin or not verify_password(admin.get("password_hash", ""), password):
        record_login_attempt(username, ip, False, user_agent)
        log_security_event("LOGIN_FAILED", username, "invalid_credentials", ip)
        time.sleep(SECURITY_CONFIG["login_delay"])  # Timing attack mitigation
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error_msg": generic_error,
            "csrf_token": request.session.get("csrf_token", "")
        })

    # Check if 2FA is required
    secrets_2fa = load_2fa_secrets()
    has_2fa = username in secrets_2fa

    if SECURITY_CONFIG["enable_2fa"]:
        if has_2fa:
            # 2FA verification needed
            request.session["pending_2fa"] = {"username": username}
            log_security_event("LOGIN_PASSWORD_OK", username, "awaiting_2fa", ip)
            return RedirectResponse(url="/2fa", status_code=302)
        else:
            # 2FA setup needed
            request.session["pending_2fa_setup"] = {"username": username}
            log_security_event("LOGIN_PASSWORD_OK", username, "awaiting_2fa_setup", ip)
            return RedirectResponse(url="/2fa", status_code=302)

    # No 2FA required - complete login
    clear_failed_attempts(username, ip)
    record_login_attempt(username, ip, True, user_agent)

    request.session["admin_logged_in"] = True
    request.session["admin_username"] = username
    request.session["admin_role"] = admin.get("role", "admin")
    request.session["admin_2fa_verified"] = True
    request.session["admin_last_activity"] = int(time.time())

    log_security_event("LOGIN_SUCCESS", username, "success", ip)
    return RedirectResponse(url="/dashboard", status_code=302)


@app.get("/2fa", response_class=HTMLResponse)
async def twofa_page(request: Request):
    """2FA setup/verification page"""
    session = request.session

    # Check for pending states
    is_pending_setup = "pending_2fa_setup" in session
    is_pending_verify = "pending_2fa" in session
    is_logged_in = session.get("admin_logged_in", False)

    if not is_logged_in and not is_pending_setup and not is_pending_verify:
        return RedirectResponse(url="/login", status_code=302)

    # Already verified
    if session.get("admin_2fa_verified"):
        return RedirectResponse(url="/dashboard", status_code=302)

    # Get username
    if is_pending_setup:
        username = session["pending_2fa_setup"]["username"]
    elif is_pending_verify:
        username = session["pending_2fa"]["username"]
    else:
        username = session.get("admin_username", "")

    if not username:
        return RedirectResponse(url="/login", status_code=302)

    # Check if user needs setup or verification
    secrets_2fa = load_2fa_secrets()
    has_2fa = username in secrets_2fa
    show_setup = not has_2fa

    secret = None
    otp_auth_url = None

    if show_setup:
        if "temp_2fa_secret" not in session:
            session["temp_2fa_secret"] = generate_totp_secret()
        secret = session["temp_2fa_secret"]
        otp_auth_url = f"otpauth://totp/AdSphere%20Admin:{username}?secret={secret}&issuer=AdSphere%20Admin"

    return templates.TemplateResponse("2fa.html", {
        "request": request,
        "username": username,
        "show_setup": show_setup,
        "secret": secret,
        "otp_auth_url": otp_auth_url,
        "error": ""
    })


@app.post("/2fa")
async def twofa_verify(request: Request, code: str = Form(...)):
    """Verify 2FA code"""
    session = request.session
    ip = get_client_ip(request)

    # Get username
    is_pending_setup = "pending_2fa_setup" in session
    is_pending_verify = "pending_2fa" in session

    if is_pending_setup:
        username = session["pending_2fa_setup"]["username"]
    elif is_pending_verify:
        username = session["pending_2fa"]["username"]
    else:
        username = session.get("admin_username", "")

    if not username:
        return RedirectResponse(url="/login", status_code=302)

    # Get secret
    secrets_2fa = load_2fa_secrets()
    user_secret = secrets_2fa.get(username)
    temp_secret = session.get("temp_2fa_secret")

    secret_to_verify = user_secret or temp_secret

    if not secret_to_verify:
        return RedirectResponse(url="/login", status_code=302)

    # Verify code
    code = code.replace(" ", "")
    if verify_totp(secret_to_verify, code):
        # Save secret if setup
        if not user_secret and temp_secret:
            secrets_2fa[username] = temp_secret
            save_2fa_secrets(secrets_2fa)

            # Update admins.json
            admins = load_admins()
            if username in admins:
                admins[username]["2fa_enabled"] = True
                ADMINS_FILE.write_text(json.dumps(admins, indent=2))

            session.pop("temp_2fa_secret", None)

        # Complete login
        session["admin_logged_in"] = True
        session["admin_username"] = username

        admins = load_admins()
        session["admin_role"] = admins.get(username, {}).get("role", "admin")
        session["admin_2fa_verified"] = True
        session["admin_last_activity"] = int(time.time())

        # Clear pending states
        session.pop("pending_2fa_setup", None)
        session.pop("pending_2fa", None)

        log_security_event("2FA_SUCCESS", username, "verified", ip)
        return RedirectResponse(url="/dashboard", status_code=302)

    # Invalid code
    log_security_event("2FA_FAILED", username, "invalid_code", ip)

    show_setup = not user_secret
    secret = temp_secret if show_setup else None
    otp_auth_url = f"otpauth://totp/AdSphere%20Admin:{username}?secret={secret}&issuer=AdSphere%20Admin" if secret else None

    return templates.TemplateResponse("2fa.html", {
        "request": request,
        "username": username,
        "show_setup": show_setup,
        "secret": secret,
        "otp_auth_url": otp_auth_url,
        "error": "Invalid verification code. Please try again."
    })


@app.get("/logout")
async def logout(request: Request):
    """Logout"""
    username = request.session.get("admin_username", "unknown")
    ip = get_client_ip(request)
    log_security_event("LOGOUT", username, "success", ip)
    request.session.clear()
    return RedirectResponse(url="/login?logout=1", status_code=302)


@app.get("/health")
async def health():
    """Health check"""
    return {"status": "healthy", "service": "admin", "port": 8002}


# ============================================
# PROTECTED ROUTES (Auth required)
# ============================================

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, session: dict = Depends(require_auth)):
    """Dashboard page"""
    return templates.TemplateResponse("dashboard.html", get_template_context(request))


@app.get("/companies", response_class=HTMLResponse)
async def companies_page(request: Request, session: dict = Depends(require_auth)):
    """Companies management page"""
    # Load companies from database
    companies = []
    try:
        import sys
        sys.path.insert(0, str(BASE_DIR.parent / "python_shared"))
        from database import SessionLocal
        from models import Company

        db = SessionLocal()
        companies = db.query(Company).order_by(Company.created_at.desc()).all()
        db.close()
    except Exception as e:
        print(f"Error loading companies: {e}")

    return templates.TemplateResponse("companies.html", get_template_context(request, companies=companies))


@app.get("/ads", response_class=HTMLResponse)
async def ads_page(request: Request, session: dict = Depends(require_auth)):
    """Ads management page"""
    ads = []
    try:
        import sys
        sys.path.insert(0, str(BASE_DIR.parent / "python_shared"))
        from database import SessionLocal
        from models import Ad

        db = SessionLocal()
        ads = db.query(Ad).order_by(Ad.created_at.desc()).limit(100).all()
        db.close()
    except Exception as e:
        print(f"Error loading ads: {e}")

    return templates.TemplateResponse("ads.html", get_template_context(request, ads=ads))


@app.get("/categories", response_class=HTMLResponse)
async def categories_page(request: Request, session: dict = Depends(require_auth)):
    """Categories page"""
    categories = []
    try:
        import sys
        sys.path.insert(0, str(BASE_DIR.parent / "python_shared"))
        from database import SessionLocal
        from models import Category

        db = SessionLocal()
        categories = db.query(Category).order_by(Category.category_name).all()
        db.close()
    except Exception as e:
        print(f"Error loading categories: {e}")

    return templates.TemplateResponse("categories.html", get_template_context(request, categories=categories))


@app.get("/moderation", response_class=HTMLResponse)
async def moderation_page(request: Request, session: dict = Depends(require_auth)):
    """Content moderation page"""
    return templates.TemplateResponse("moderation.html", get_template_context(request))


@app.get("/flagged", response_class=HTMLResponse)
async def flagged_page(request: Request, session: dict = Depends(require_auth)):
    """Flagged content page"""
    flagged_ads = []
    flagged_file = BASE_DIR.parent / "python_shared" / "data" / "flagged_ads.json"
    if flagged_file.exists():
        flagged_ads = json.loads(flagged_file.read_text())

    return templates.TemplateResponse("flagged.html", get_template_context(request, flagged_ads=flagged_ads))


@app.get("/scanner", response_class=HTMLResponse)
async def scanner_page(request: Request, session: dict = Depends(require_auth)):
    """Ad scanner page"""
    return templates.TemplateResponse("scanner.html", get_template_context(request))


@app.get("/analytics", response_class=HTMLResponse)
async def analytics_page(request: Request, session: dict = Depends(require_auth)):
    """Analytics page"""
    return templates.TemplateResponse("analytics.html", get_template_context(request))


@app.get("/users", response_class=HTMLResponse)
async def users_page(request: Request, session: dict = Depends(require_auth)):
    """Admin users page"""
    admins = load_admins()
    return templates.TemplateResponse("users.html", get_template_context(request, admins=admins))


@app.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request, session: dict = Depends(require_auth)):
    """Settings page"""
    return templates.TemplateResponse("settings.html", get_template_context(request))


@app.get("/logs", response_class=HTMLResponse)
async def logs_page(request: Request, file: str = None, session: dict = Depends(require_auth)):
    """System logs page"""
    log_files = sorted(LOGS_DIR.glob("*.log"), reverse=True)[:10]
    log_content = ""
    selected_log = file or ""

    if selected_log:
        log_path = LOGS_DIR / Path(selected_log).name
        if log_path.exists():
            log_content = log_path.read_text()

    return templates.TemplateResponse("logs.html", get_template_context(
        request,
        log_files=[f.name for f in log_files],
        selected_log=selected_log,
        log_content=log_content
    ))


# ============================================
# API ROUTES
# ============================================

@app.get("/api/stats")
async def api_stats(session: dict = Depends(require_auth)):
    """Get dashboard stats"""
    stats = {
        "total_companies": 0,
        "total_ads": 0,
        "active_ads": 0,
        "flagged_ads": 0,
        "total_views": 0,
        "total_contacts": 0
    }

    try:
        import sys
        sys.path.insert(0, str(BASE_DIR.parent / "python_shared"))
        from database import SessionLocal
        from models import Company, Ad
        from sqlalchemy import func

        db = SessionLocal()
        stats["total_companies"] = db.query(func.count(Company.company_slug)).scalar() or 0
        stats["total_ads"] = db.query(func.count(Ad.ad_id)).scalar() or 0
        stats["active_ads"] = db.query(func.count(Ad.ad_id)).filter(Ad.status == "active").scalar() or 0
        stats["flagged_ads"] = db.query(func.count(Ad.ad_id)).filter(Ad.status == "review").scalar() or 0
        stats["total_views"] = db.query(func.sum(Ad.views_count)).scalar() or 0
        stats["total_contacts"] = db.query(func.sum(Ad.contacts_count)).scalar() or 0
        db.close()
    except Exception as e:
        print(f"Error getting stats: {e}")

    return {"success": True, "stats": stats}


@app.get("/api/analytics")
async def api_analytics(session: dict = Depends(require_auth)):
    """Get analytics data"""
    data = {
        "views": 0,
        "contacts": 0,
        "favorites": 0,
        "likes": 0
    }

    try:
        import sys
        sys.path.insert(0, str(BASE_DIR.parent / "python_shared"))
        from database import SessionLocal
        from models import Ad
        from sqlalchemy import func

        db = SessionLocal()
        data["views"] = db.query(func.sum(Ad.views_count)).scalar() or 0
        data["contacts"] = db.query(func.sum(Ad.contacts_count)).scalar() or 0
        data["favorites"] = db.query(func.sum(Ad.favorites_count)).scalar() or 0
        data["likes"] = db.query(func.sum(Ad.likes_count)).scalar() or 0
        db.close()
    except Exception as e:
        print(f"Error getting analytics: {e}")

    return {"success": True, "data": data}


@app.post("/api/scanner/run")
async def api_scanner_run(request: Request, session: dict = Depends(require_auth)):
    """Run ad scanner"""
    try:
        data = await request.json()
    except:
        data = {"mode": "incremental"}

    mode = data.get("mode", "incremental")

    # TODO: Implement actual scanner integration
    return {
        "success": True,
        "message": f"Scanner started in {mode} mode",
        "data": {
            "scanned": 0,
            "flagged": 0,
            "clean": 0
        }
    }


@app.get("/api/moderation/flagged")
async def api_moderation_flagged(session: dict = Depends(require_auth)):
    """Get flagged content"""
    flagged_file = BASE_DIR.parent / "python_shared" / "data" / "moderation_violations"
    flagged_items = []

    if flagged_file.exists():
        for f in flagged_file.glob("*.json"):
            try:
                items = json.loads(f.read_text())
                if isinstance(items, list):
                    flagged_items.extend(items)
            except:
                pass

    return {"success": True, "data": flagged_items}


# Run the app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)

