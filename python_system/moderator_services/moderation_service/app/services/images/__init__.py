"""
Image Moderation Services
=========================

Comprehensive image moderation pipeline with:
- Security scanning (embedded data, steganography)
- Sanitization (remove hidden data)
- Compression (WebP ≤ 1MB)
- OCR text extraction
- Text moderation (via text pipeline)
- NSFW detection
- Object detection (weapons, etc.)
- Scene analysis
- Violence/gore detection

Pipeline Flow:
    Scanner → Sanitizer → Compressor → OCR → Content Analysis

Module Structure:
- models.py           - Data classes and enums
- security_scanner.py - Security and malware scanning
- image_compressor.py - Compress to WebP ≤ 1MB
- ocr_processor.py    - Text extraction via OCR
- content_analyzers.py - NSFW, object, scene, violence detection
- pipeline.py         - Main pipeline orchestrator
- security/           - Security detectors and sanitizer
"""

import sys
from pathlib import Path

# Set up paths for model_registry import
# Path: images/__init__.py -> images -> services -> app -> moderation_service -> moderator_services
IMAGES_DIR = Path(__file__).parent.resolve()
SERVICES_DIR = IMAGES_DIR.parent.resolve()
APP_DIR = SERVICES_DIR.parent.resolve()
MODERATION_SERVICE_DIR = APP_DIR.parent.resolve()
MODERATOR_SERVICES_DIR = MODERATION_SERVICE_DIR.parent.resolve()

for _path in [str(MODERATOR_SERVICES_DIR), str(MODERATION_SERVICE_DIR), str(APP_DIR)]:
    if _path not in sys.path:
        sys.path.insert(0, _path)

# Import from models
from .models import (
    ImageModerationDecision,
    ImageViolationType,
    ImageAnalysisType,
    SecurityScanResult,
    OCRResult,
    ObjectDetection,
    SceneClassification,
    ImageModerationInput,
    ImageModerationResult
)

# Import from pipeline
from .pipeline import (
    ImageModerationPipeline,
    get_image_moderator,
    moderate_image
)

# Import individual components for advanced usage
from .security_scanner import SecurityScanner
from .ocr_processor import ImageOCRProcessor
from .content_analyzers import (
    NSFWAnalyzer,
    ObjectDetector,
    SceneAnalyzer,
    ViolenceDetector
)

# Import compressor
from .image_compressor import (
    ImageCompressor,
    CompressionResult,
    compress_image,
    compress_file
)

__all__ = [
    # Main exports
    'ImageModerationPipeline',
    'ImageModerationInput',
    'ImageModerationResult',
    'ImageModerationDecision',
    'ImageViolationType',
    'get_image_moderator',
    'moderate_image',

    # Data classes
    'ImageAnalysisType',
    'SecurityScanResult',
    'OCRResult',
    'ObjectDetection',
    'SceneClassification',
    'CompressionResult',

    # Individual components
    'SecurityScanner',
    'ImageOCRProcessor',
    'NSFWAnalyzer',
    'ObjectDetector',
    'SceneAnalyzer',
    'ViolenceDetector',

    # Compressor
    'ImageCompressor',
    'compress_image',
    'compress_file',
]

