"""
Image Security Package
======================

Comprehensive image security scanning with modular detectors.

Usage:
    from .security import SecurityScanner, scan_image

    # Quick scan (ML-only, default)
    result = scan_image("image.jpg")
    if not result.is_safe:
        print(f"Threat: {result.threat_level.value}")

    # Custom scanner with all ML detectors
    scanner = SecurityScanner(
        enable_ml_steg=True,
        enable_ml_forensics=True,
        enable_ml_hidden=True,
    )
    result = scanner.scan("image.jpg")

    # Full scan with traditional detectors
    scanner = SecurityScanner(enable_traditional=True)
    result = scanner.scan("image.jpg")

    # Sanitize a malicious image
    from .security import sanitize_image
    result = sanitize_image("malicious.jpg", "clean.jpg")

Detectors (ML-based, enabled by default):
    - MLStegDetector: ML-enhanced steganography detection
    - MLForensicsDetector: ML-enhanced image forensics
    - MLHiddenDataDetector: Hidden/embedded data detection

Detectors (Traditional, optional):
    - FileStructureDetector: File signatures, EOF, hidden markers
    - FileSizeDetector: File size and compression anomalies
    - EntropyDetector: Statistical entropy anomalies
    - LSBDetector: LSB steganography detection
    - DCTDetector: JPEG DCT-domain steganography
    - MetadataDetector: EXIF/XMP/IPTC analysis
    - HeuristicsDetector: Combined risk assessment

Sanitizer:
    - ImageSanitizer: Remove hidden data and make images safe
"""

import sys
from pathlib import Path

# Set up paths for model_registry import
# Path: security/__init__.py -> security -> images -> services -> app -> moderation_service -> moderator_services
CURRENT_DIR = Path(__file__).parent.resolve()
IMAGES_DIR = CURRENT_DIR.parent.resolve()
SERVICES_DIR = IMAGES_DIR.parent.resolve()
APP_DIR = SERVICES_DIR.parent.resolve()
MODERATION_SERVICE_DIR = APP_DIR.parent.resolve()
MODERATOR_SERVICES_DIR = MODERATION_SERVICE_DIR.parent.resolve()

for _path in [str(MODERATOR_SERVICES_DIR), str(MODERATION_SERVICE_DIR), str(APP_DIR)]:
    if _path not in sys.path:
        sys.path.insert(0, _path)

from .scanner import SecurityScanner, SecurityScanResult, ThreatLevel, scan_image
from .image_sanitizer import ImageSanitizer, SanitizeResult, sanitize_image

from .detectors import (
    FileStructureDetector,
    FileSizeDetector,
    EntropyDetector,
    LSBDetector,
    DCTDetector,
    MetadataDetector,
    HeuristicsDetector,
    MLStegDetector,
    MLForensicsDetector,
    MLHiddenDataDetector,
    FileStructureResult,
    EntropyResult,
    LSBResult,
    DCTResult,
    MetadataResult,
    HeuristicsResult,
    MLStegResult,
    ForensicsResult,
    HiddenDataResult,
)

__all__ = [
    # Main scanner
    'SecurityScanner',
    'SecurityScanResult',
    'ThreatLevel',
    'scan_image',

    # Sanitizer
    'ImageSanitizer',
    'SanitizeResult',
    'sanitize_image',

    # ML Detectors (Primary)
    'MLStegDetector',
    'MLForensicsDetector',
    'MLHiddenDataDetector',

    # Traditional Detectors (Optional)
    'FileStructureDetector',
    'FileSizeDetector',
    'EntropyDetector',
    'LSBDetector',
    'DCTDetector',
    'MetadataDetector',
    'HeuristicsDetector',

    # Result types
    'FileStructureResult',
    'EntropyResult',
    'LSBResult',
    'DCTResult',
    'MetadataResult',
    'HeuristicsResult',
    'MLStegResult',
    'ForensicsResult',
    'HiddenDataResult',
]

