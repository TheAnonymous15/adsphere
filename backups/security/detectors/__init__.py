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
"""

from .file_structure import FileStructureDetector, FileStructureResult
from .file_size import FileSizeDetector
from .entropy import EntropyDetector, EntropyResult
from .lsb import LSBDetector, LSBResult
from .dct import DCTDetector, DCTResult
from .metadata import MetadataDetector, MetadataResult
from .heuristics import HeuristicsDetector, HeuristicsResult

__all__ = [
    # Detectors
    'FileStructureDetector',
    'FileSizeDetector',
    'EntropyDetector',
    'LSBDetector',
    'DCTDetector',
    'MetadataDetector',
    'HeuristicsDetector',

    # Results
    'FileStructureResult',
    'EntropyResult',
    'LSBResult',
    'DCTResult',
    'MetadataResult',
    'HeuristicsResult',
]

