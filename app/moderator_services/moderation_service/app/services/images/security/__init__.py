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

