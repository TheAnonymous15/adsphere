"""
Pydantic models for requests and responses
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime


class MediaItem(BaseModel):
    """Media item (image or video)"""
    type: str = Field(..., description="Type: 'image' or 'video'")
    url: Optional[str] = Field(None, description="Public URL to media")
    data: Optional[str] = Field(None, description="Base64 encoded data")


class UserContext(BaseModel):
    """User context"""
    id: Optional[str] = None
    company: Optional[str] = None


class RequestContext(BaseModel):
    """Request context"""
    ad_id: Optional[str] = None
    source: Optional[str] = "api"
    ip: Optional[str] = None


class ModerationRequest(BaseModel):
    """Realtime moderation request"""
    title: str = Field(..., max_length=500)
    description: str = Field(..., max_length=5000)
    category: str = Field(default="general", max_length=100)
    language: str = Field(default="auto", max_length=10)
    media: List[MediaItem] = Field(default_factory=list)
    user: Optional[UserContext] = None
    context: Optional[RequestContext] = None


class CategoryScores(BaseModel):
    """Category-level moderation scores"""
    nudity: float = 0.0
    sexual_content: float = 0.0
    violence: float = 0.0
    weapons: float = 0.0
    blood: float = 0.0
    hate: float = 0.0
    self_harm: float = 0.0
    drugs: float = 0.0
    scam_fraud: float = 0.0
    spam: float = 0.0
    minors: float = 0.0


class AISourceResult(BaseModel):
    """Individual AI model result"""
    model_name: str
    score: float
    details: Optional[Dict] = None

    model_config = {"protected_namespaces": ()}


class ModerationResponse(BaseModel):
    """Moderation response"""
    success: bool = True
    decision: str = Field(..., description="approve, review, or block")
    global_score: float = Field(..., description="Overall safety score (0.0-1.0)")
    risk_level: str = Field(..., description="low, medium, high, or critical")
    category_scores: CategoryScores
    flags: List[str] = Field(default_factory=list)
    reasons: List[str] = Field(default_factory=list)
    ai_sources: Optional[Dict[str, AISourceResult]] = None
    job: Optional[Dict] = None
    audit_id: str
    processing_time: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class JobStatusResponse(BaseModel):
    """Job status response"""
    job_id: str
    status: str = Field(..., description="queued, running, completed, failed, cancelled")
    progress: Optional[float] = Field(None, description="Progress percentage (0-100)")
    created_at: datetime
    updated_at: datetime
    error: Optional[str] = None

