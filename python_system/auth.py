"""
Authentication and Authorization for AdSphere Python System
Handles JWT tokens, session management, and role-based access
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from fastapi.security.http import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import jwt
from passlib.context import CryptContext
from typing import Optional, Dict, Any
import os

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()


class PasswordService:
    """Handle password hashing and verification"""

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password"""
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password"""
        return pwd_context.verify(plain_password, hashed_password)


class TokenService:
    """Handle JWT token creation and verification"""

    @staticmethod
    def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)

        to_encode.update({"exp": expire, "iat": datetime.utcnow()})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    @staticmethod
    def verify_token(token: str) -> Dict[str, Any]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )


class AuthService:
    """High-level authentication service"""

    @staticmethod
    def create_user_token(user_id: int, email: str) -> str:
        """Create token for public user"""
        data = {
            "sub": str(user_id),
            "email": email,
            "type": "user"
        }
        return TokenService.create_access_token(data)

    @staticmethod
    def create_company_token(company_id: int, slug: str) -> str:
        """Create token for company"""
        data = {
            "sub": str(company_id),
            "slug": slug,
            "type": "company"
        }
        return TokenService.create_access_token(data)

    @staticmethod
    def create_admin_token(admin_id: int, username: str, two_factor_verified: bool = False) -> str:
        """Create token for admin"""
        data = {
            "sub": str(admin_id),
            "username": username,
            "type": "admin",
            "2fa_verified": two_factor_verified
        }
        return TokenService.create_access_token(data)


# ============================================================================
# DEPENDENCY FUNCTIONS FOR FASTAPI
# ============================================================================

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Get and verify current user from token"""
    token = credentials.credentials
    payload = TokenService.verify_token(token)

    if payload.get("type") != "user":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not a user token"
        )

    return payload


async def get_current_company(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Get and verify current company from token"""
    token = credentials.credentials
    payload = TokenService.verify_token(token)

    if payload.get("type") != "company":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not a company token"
        )

    return payload


async def get_current_admin(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Get and verify current admin from token"""
    token = credentials.credentials
    payload = TokenService.verify_token(token)

    if payload.get("type") != "admin":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not an admin token"
        )

    # Check if 2FA is verified
    if not payload.get("2fa_verified", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="2FA verification required"
        )

    return payload


async def get_current_admin_pending_2fa(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Get admin token that may not have 2FA verified yet"""
    token = credentials.credentials
    payload = TokenService.verify_token(token)

    if payload.get("type") != "admin":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not an admin token"
        )

    return payload


# ============================================================================
# ROLE-BASED ACCESS CONTROL
# ============================================================================

class RoleChecker:
    """Check user roles and permissions"""

    def __init__(self, allowed_roles: list):
        self.allowed_roles = allowed_roles

    async def __call__(self, current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        if current_user.get("type") not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user

