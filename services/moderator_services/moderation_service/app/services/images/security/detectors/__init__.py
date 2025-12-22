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

