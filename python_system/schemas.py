"""
Pydantic schemas for AdSphere Python System
Request/Response validation models
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime


# ============================================================================
# AUTH SCHEMAS
# ============================================================================

class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    full_name: Optional[str] = None


class CompanyLogin(BaseModel):
    slug: str
    password: str = Field(..., min_length=6)


class AdminLogin(BaseModel):
    username: str
    password: str = Field(..., min_length=6)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ============================================================================
# AD SCHEMAS
# ============================================================================

class AdCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=10)
    category: str
    price: Optional[float] = None
    images: Optional[List[str]] = []
    video: Optional[str] = None


class AdResponse(BaseModel):
    id: str
    title: str
    description: str
    category: str
    status: str
    view_count: int
    contact_count: int
    favorite_count: int
    like_count: int
    dislike_count: int = 0
    created_at: datetime

    class Config:
        from_attributes = True


class AdDetailResponse(AdResponse):
    images: Optional[List[str]] = []
    video: Optional[str] = None
    price: Optional[float] = None


# ============================================================================
# USER SCHEMAS
# ============================================================================

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    full_name: str


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    created_at: datetime

    class Config:
        from_attributes = True


class UserProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    preferences: Optional[dict] = None


# ============================================================================
# COMPANY SCHEMAS
# ============================================================================

class CompanyCreate(BaseModel):
    slug: str = Field(..., min_length=3)
    name: str
    email: EmailStr
    password: str = Field(..., min_length=6)
    category: str


class CompanyResponse(BaseModel):
    id: int
    slug: str
    name: str
    email: str
    verified: bool
    suspended: bool
    category: str
    logo: Optional[str] = None
    description: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class CompanyProfileUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    logo: Optional[str] = None
    phone: Optional[str] = None


# ============================================================================
# ADMIN SCHEMAS
# ============================================================================

class AdminCreate(BaseModel):
    username: str = Field(..., min_length=3)
    email: EmailStr
    password: str = Field(..., min_length=6)


class AdminResponse(BaseModel):
    id: int
    username: str
    email: str
    two_factor_enabled: bool
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================================================
# INTERACTION SCHEMAS
# ============================================================================

class InteractionTrack(BaseModel):
    ad_id: str
    event_type: str  # view, contact, favorite, like, dislike, call, sms, email, whatsapp
    duration_seconds: Optional[int] = 0
    scroll_depth: Optional[float] = 0.0
    device_id: Optional[str] = None


class InteractionResponse(BaseModel):
    ad_id: str
    interaction_type: str
    timestamp: datetime

    class Config:
        from_attributes = True


# ============================================================================
# ANALYTICS SCHEMAS
# ============================================================================

class AdAnalyticsResponse(BaseModel):
    ad_id: str
    views: int
    contacts: int
    favorites: int
    likes: int
    dislikes: int
    contact_methods: dict  # {call, sms, email, whatsapp}


class DashboardStatsResponse(BaseModel):
    total_ads: int
    total_views: int
    total_companies: int
    total_contacts: int
    active_users: int


class AdminDashboardResponse(BaseModel):
    total_ads: int
    active_ads: int
    blocked_ads: int
    pending_review: int
    total_views: int
    total_companies: int
    total_users: int


# ============================================================================
# MODERATION SCHEMAS
# ============================================================================

class ModerationAction(BaseModel):
    ad_id: str
    decision: str  # approve, block, review
    reason: Optional[str] = None
    scores: Optional[dict] = None


class ModerationLogResponse(BaseModel):
    id: int
    ad_id: str
    action: str
    reason: Optional[str] = None
    timestamp: datetime

    class Config:
        from_attributes = True


# ============================================================================
# CATEGORY SCHEMAS
# ============================================================================

class CategoryCreate(BaseModel):
    name: str
    slug: str
    description: str
    icon: Optional[str] = None


class CategoryResponse(BaseModel):
    id: int
    name: str
    slug: str
    description: str
    icon: Optional[str] = None

    class Config:
        from_attributes = True

