"""
Image Moderation Models
=======================

Data classes and enums for image moderation.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid


class ImageModerationDecision(Enum):
    """Image moderation decision outcomes"""
    APPROVE = "approve"
    REVIEW = "review"
    BLOCK = "block"


class ImageViolationType(Enum):
    """Types of image content violations"""
    NONE = "none"
    NSFW = "nsfw"
    NUDITY = "nudity"
    VIOLENCE = "violence"
    GORE = "gore"
    WEAPONS = "weapons"
    DRUGS = "drugs"
    HATE_SYMBOLS = "hate_symbols"
    ILLEGAL_CONTENT = "illegal_content"
    MALICIOUS_DATA = "malicious_data"
    STEGANOGRAPHY = "steganography"
    TEXT_VIOLATION = "text_violation"
    SPAM = "spam"
    SCAM = "scam"
    SHOCKING = "shocking"


class ImageAnalysisType(Enum):
    """Types of image analysis performed"""
    SECURITY_SCAN = "security_scan"
    OCR = "ocr"
    TEXT_MODERATION = "text_moderation"
    NSFW_DETECTION = "nsfw_detection"
    OBJECT_DETECTION = "object_detection"
    SCENE_CLASSIFICATION = "scene_classification"
    FACE_DETECTION = "face_detection"
    LOGO_DETECTION = "logo_detection"
    QUALITY_CHECK = "quality_check"


@dataclass
class SecurityScanResult:
    """Result from security scan for embedded data"""
    is_safe: bool = True
    has_embedded_data: bool = False
    embedded_type: Optional[str] = None
    malware_detected: bool = False
    suspicious_metadata: bool = False
    exif_data: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)


@dataclass
class OCRResult:
    """Result from OCR text extraction"""
    text: str = ""
    lines: List[Dict[str, Any]] = field(default_factory=list)
    confidence: float = 0.0
    language: str = "unknown"
    num_lines: int = 0
    has_text: bool = False


@dataclass
class ObjectDetection:
    """Single object detection result"""
    label: str
    confidence: float
    bbox: List[float]  # [x1, y1, x2, y2]
    category: str = ""


@dataclass
class SceneClassification:
    """Scene classification result"""
    scene_type: str
    confidence: float
    attributes: List[str] = field(default_factory=list)


@dataclass
class ImageModerationInput:
    """Input for image moderation"""
    image_path: str
    image_url: Optional[str] = None
    image_bytes: Optional[bytes] = None
    context: Optional[Dict[str, Any]] = None
    ad_title: Optional[str] = None
    ad_description: Optional[str] = None
    category: Optional[str] = None


@dataclass
class ImageModerationResult:
    """Complete image moderation result"""
    # Decision
    decision: ImageModerationDecision
    confidence: float

    # Violations found
    violations: List[ImageViolationType] = field(default_factory=list)
    violation_scores: Dict[str, float] = field(default_factory=dict)

    # Analysis results
    security_scan: Optional[SecurityScanResult] = None
    ocr_result: Optional[OCRResult] = None
    text_moderation_result: Optional[Dict[str, Any]] = None

    # Detection results
    nsfw_scores: Dict[str, float] = field(default_factory=dict)
    objects_detected: List[ObjectDetection] = field(default_factory=list)
    scene_classification: Optional[SceneClassification] = None

    # Weapon/violence detection
    weapon_detected: bool = False
    weapon_score: float = 0.0
    violence_detected: bool = False
    violence_score: float = 0.0

    # Quality metrics
    image_quality: Dict[str, Any] = field(default_factory=dict)

    # Explanation
    explanation: str = ""
    detailed_rationale: List[str] = field(default_factory=list)

    # Metadata
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    processing_time_ms: float = 0.0
    analyses_performed: List[str] = field(default_factory=list)
    models_used: List[str] = field(default_factory=list)

