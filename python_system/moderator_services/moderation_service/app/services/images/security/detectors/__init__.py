"""
Security Detectors Package
==========================

Individual detectors for image security analysis:
- file_structure: File signature, EOF, hidden markers
- file_size: File size and compression anomalies
- entropy: Entropy-based anomaly detection
- lsb: LSB steganography detection
- dct: DCT-domain steganography (JPEG)
- metadata: EXIF/XMP/IPTC analysis
- heuristics: Combined heuristic analysis
- ml_steg: ML-enhanced steganography detection
- ml_forensics: ML-enhanced image forensics
- ml_hidden: ML-enhanced hidden data detection
"""

import sys
from pathlib import Path

# Set up paths for model_registry import
# Path: detectors/__init__.py -> detectors -> security -> images -> services -> app -> moderation_service -> moderator_services
CURRENT_DIR = Path(__file__).parent.resolve()
SECURITY_DIR = CURRENT_DIR.parent.resolve()
IMAGES_DIR = SECURITY_DIR.parent.resolve()
SERVICES_DIR = IMAGES_DIR.parent.resolve()
APP_DIR = SERVICES_DIR.parent.resolve()
MODERATION_SERVICE_DIR = APP_DIR.parent.resolve()
MODERATOR_SERVICES_DIR = MODERATION_SERVICE_DIR.parent.resolve()

for _path in [str(MODERATOR_SERVICES_DIR), str(MODERATION_SERVICE_DIR), str(APP_DIR)]:
    if _path not in sys.path:
        sys.path.insert(0, _path)

from .file_structure import FileStructureDetector, FileStructureResult
from .file_size import FileSizeDetector
from .entropy import EntropyDetector, EntropyResult
from .lsb import LSBDetector, LSBResult
from .dct import DCTDetector, DCTResult
from .metadata import MetadataDetector, MetadataResult
from .heuristics import HeuristicsDetector, HeuristicsResult
from .ml_steg import MLStegDetector, MLStegResult
from .ml_forensics import MLForensicsDetector, ForensicsResult
from .ml_hidden import MLHiddenDataDetector, HiddenDataResult

__all__ = [
    # Detectors
    'FileStructureDetector',
    'FileSizeDetector',
    'EntropyDetector',
    'LSBDetector',
    'DCTDetector',
    'MetadataDetector',
    'HeuristicsDetector',
    'MLStegDetector',
    'MLForensicsDetector',
    'MLHiddenDataDetector',

    # Results
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

