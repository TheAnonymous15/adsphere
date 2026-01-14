"""
Image Security Package
======================

Comprehensive image security scanning with modular detectors.

Usage:
    from .security import SecurityScanner, scan_image

    # Quick scan
    result = scan_image("image.jpg")
    if not result.is_safe:
        print(f"Threat: {result.threat_level.value}")

    # Custom scanner
    scanner = SecurityScanner(
        enable_file_size=True,
        enable_entropy=True,
        enable_lsb=True,
        enable_dct=True,
        enable_metadata=True,
        enable_heuristics=True,
    )
    result = scanner.scan("image.jpg", deep_scan=True)

Detectors:
    - FileStructureDetector: File signatures, EOF, hidden markers
    - FileSizeDetector: File size and compression anomalies
    - EntropyDetector: Statistical entropy anomalies
    - LSBDetector: LSB steganography detection
    - DCTDetector: JPEG DCT-domain steganography
    - MetadataDetector: EXIF/XMP/IPTC analysis
    - HeuristicsDetector: Combined risk assessment
"""

from .scanner import SecurityScanner, SecurityScanResult, ThreatLevel, scan_image

from .detectors import (
    FileStructureDetector,
    FileSizeDetector,
    EntropyDetector,
    LSBDetector,
    DCTDetector,
    MetadataDetector,
    HeuristicsDetector,
    FileStructureResult,
    EntropyResult,
    LSBResult,
    DCTResult,
    MetadataResult,
    HeuristicsResult,
)

__all__ = [
    # Main scanner
    'SecurityScanner',
    'SecurityScanResult',
    'ThreatLevel',
    'scan_image',

    # Individual detectors
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
]

