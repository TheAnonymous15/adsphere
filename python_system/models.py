"""
SQLAlchemy Models for AdSphere Python System
These models MATCH the existing database schema exactly
"""

from sqlalchemy import Column, Integer, String, Text, Float, Boolean, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


# ============================================================================
# COMPANIES TABLE - Matches existing schema
# ============================================================================
class Company(Base):
    __tablename__ = "companies"

    company_slug = Column(String, primary_key=True)
    company_name = Column(String, nullable=False)
    email = Column(String)
    phone = Column(String)
    sms = Column(String)
    whatsapp = Column(String)
    created_at = Column(Integer, nullable=False)
    updated_at = Column(Integer, nullable=False)
    status = Column(String, default='active')  # active, inactive, suspended

    # For authentication (may not exist in DB - optional)
    password_hash = Column(String, nullable=True)

    # Relationships
    ads = relationship("Ad", back_populates="company")


# ============================================================================
# CATEGORIES TABLE - Matches existing schema
# ============================================================================
class Category(Base):
    __tablename__ = "categories"

    category_id = Column(Integer, primary_key=True, autoincrement=True)
    category_slug = Column(String, unique=True, nullable=False)
    category_name = Column(String, nullable=False)
    description = Column(Text)
    created_at = Column(Integer, nullable=False)

    # Relationships
    ads = relationship("Ad", back_populates="category")


# ============================================================================
# ADS TABLE - Matches existing schema exactly
# ============================================================================
class Ad(Base):
    __tablename__ = "ads"

    ad_id = Column(String, primary_key=True)
    company_slug = Column(String, ForeignKey('companies.company_slug'), nullable=False)
    category_slug = Column(String, ForeignKey('categories.category_slug'), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text)
    media_filename = Column(String, nullable=False)
    media_type = Column(String)  # image, video, audio
    media_path = Column(String, nullable=False)

    # Contact info
    contact_phone = Column(String)
    contact_sms = Column(String)
    contact_email = Column(String)
    contact_whatsapp = Column(String)

    # Timestamps (stored as INTEGER/Unix timestamps)
    created_at = Column(Integer, nullable=False)
    updated_at = Column(Integer, nullable=False)

    # Status
    status = Column(String, default='active')  # active, inactive, scheduled, expired
    scheduled_at = Column(Integer)
    expires_at = Column(Integer)

    # Counters (cached from analytics)
    views_count = Column(Integer, default=0)
    likes_count = Column(Integer, default=0)
    dislikes_count = Column(Integer, default=0)
    favorites_count = Column(Integer, default=0)
    contacts_count = Column(Integer, default=0)

    # Relationships
    company = relationship("Company", back_populates="ads")
    category = relationship("Category", back_populates="ads")


# ============================================================================
# COMPANY CATEGORIES (many-to-many relationship)
# ============================================================================
class CompanyCategory(Base):
    __tablename__ = "company_categories"

    company_slug = Column(String, ForeignKey('companies.company_slug'), primary_key=True)
    category_slug = Column(String, ForeignKey('categories.category_slug'), primary_key=True)
    assigned_at = Column(Integer, nullable=False)


# ============================================================================
# AD VIEWS TABLE
# ============================================================================
class AdView(Base):
    __tablename__ = "ad_views"

    view_id = Column(Integer, primary_key=True, autoincrement=True)
    ad_id = Column(String, ForeignKey('ads.ad_id'), nullable=False)
    device_id = Column(String)
    session_id = Column(String)
    user_agent = Column(String)
    ip_address = Column(String)
    referrer = Column(String)
    duration_seconds = Column(Integer, default=0)
    scroll_depth = Column(Float, default=0.0)
    viewed_at = Column(Integer, nullable=False)


# ============================================================================
# INTERACTIONS TABLE (for contact events)
# ============================================================================
class Interaction(Base):
    __tablename__ = "interactions"

    interaction_id = Column(Integer, primary_key=True, autoincrement=True)
    ad_id = Column(String, ForeignKey('ads.ad_id'), nullable=False)
    interaction_type = Column(String, nullable=False)  # call, sms, email, whatsapp, favorite, like, dislike
    device_id = Column(String)
    session_id = Column(String)
    created_at = Column(Integer, nullable=False)


# ============================================================================
# FAVORITES TABLE
# ============================================================================
class Favorite(Base):
    __tablename__ = "favorites"

    favorite_id = Column(Integer, primary_key=True, autoincrement=True)
    ad_id = Column(String, ForeignKey('ads.ad_id'), nullable=False)
    user_id = Column(String)  # Can be device_id for anonymous users
    device_id = Column(String)
    created_at = Column(Integer, nullable=False)


# ============================================================================
# USERS TABLE (Public users - may not exist yet)
# ============================================================================
class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    full_name = Column(String)
    phone = Column(String)
    preferences = Column(Text)  # JSON string
    created_at = Column(Integer, nullable=False)
    updated_at = Column(Integer)


# ============================================================================
# ADMINS TABLE (Platform admins - may not exist yet)
# ============================================================================
class Admin(Base):
    __tablename__ = "admins"

    admin_id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    two_factor_enabled = Column(Boolean, default=False)
    two_factor_secret = Column(String)
    created_at = Column(Integer, nullable=False)
    last_login = Column(Integer)


# ============================================================================
# MODERATION LOGS TABLE (may not exist yet)
# ============================================================================
class ModerationLog(Base):
    __tablename__ = "moderation_logs"

    log_id = Column(Integer, primary_key=True, autoincrement=True)
    ad_id = Column(String, ForeignKey('ads.ad_id'), nullable=False)
    action = Column(String, nullable=False)  # approve, block, review
    reason = Column(Text)
    admin_id = Column(Integer)
    scores = Column(Text)  # JSON string with moderation scores
    created_at = Column(Integer, nullable=False)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================
def get_current_timestamp():
    """Get current Unix timestamp"""
    return int(datetime.now().timestamp())


def timestamp_to_datetime(ts):
    """Convert Unix timestamp to datetime"""
    if ts:
        return datetime.fromtimestamp(ts)
    return None


def datetime_to_timestamp(dt):
    """Convert datetime to Unix timestamp"""
    if dt:
        return int(dt.timestamp())
    return None

