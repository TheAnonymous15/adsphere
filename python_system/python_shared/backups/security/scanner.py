"""
Security Scanner
================

Main orchestrator for image security scanning.
Combines all detectors for comprehensive analysis.
"""

import os
import hashlib
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum

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


class ThreatLevel(Enum):
    """Threat severity levels"""
    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class SecurityScanResult:
    """Complete security scan result"""
    # Overall assessment
    is_safe: bool = True
    threat_level: ThreatLevel = ThreatLevel.SAFE
    risk_score: float = 0.0

    # Threat indicators
    has_embedded_data: bool = False
    embedded_type: str = ""
    malware_detected: bool = False
    steganography_detected: bool = False
    suspicious_metadata: bool = False

    # Individual detector results
    file_structure: Optional[FileStructureResult] = None
    entropy: Optional[EntropyResult] = None
    lsb: Optional[LSBResult] = None
    dct: Optional[DCTResult] = None
    metadata: Optional[MetadataResult] = None
    heuristics: Optional[HeuristicsResult] = None

    # File information
    file_hash_md5: str = ""
    file_hash_sha256: str = ""
    file_size: int = 0

    # Combined warnings and recommendations
    warnings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

    # Legacy compatibility
    exif_data: Dict[str, Any] = field(default_factory=dict)


class SecurityScanner:
    """
    Comprehensive image security scanner.

    Orchestrates multiple detectors:
    1. File Structure - signatures, EOF, hidden markers
    2. Entropy - statistical anomalies
    3. LSB - least significant bit steganography
    4. DCT - JPEG steganography
    5. Metadata - EXIF/XMP malware
    6. Heuristics - combined risk assessment

    Usage:
        scanner = SecurityScanner()
        result = scanner.scan("image.jpg")

        if not result.is_safe:
            print(f"Threat detected: {result.threat_level.value}")
            for warning in result.warnings:
                print(f"  - {warning}")
    """

    def __init__(
        self,
        enable_file_size: bool = True,
        enable_entropy: bool = True,
        enable_lsb: bool = True,
        enable_dct: bool = True,
        enable_metadata: bool = True,
        enable_heuristics: bool = True,
    ):
        """
        Initialize security scanner with optional detectors.

        Args:
            enable_file_size: Enable file size/compression analysis
            enable_entropy: Enable entropy analysis
            enable_lsb: Enable LSB steganography detection
            enable_dct: Enable DCT steganography detection
            enable_metadata: Enable metadata analysis
            enable_heuristics: Enable heuristic analysis
        """
        # Always enable file structure (core detector)
        self.file_structure_detector = FileStructureDetector()

        # Optional detectors
        self.file_size_detector = FileSizeDetector() if enable_file_size else None
        self.entropy_detector = EntropyDetector() if enable_entropy else None
        self.lsb_detector = LSBDetector() if enable_lsb else None
        self.dct_detector = DCTDetector() if enable_dct else None
        self.metadata_detector = MetadataDetector() if enable_metadata else None
        self.heuristics_detector = HeuristicsDetector() if enable_heuristics else None

    def scan(self, image_path: str, deep_scan: bool = False) -> SecurityScanResult:
        """
        Perform security scan on image.

        Args:
            image_path: Path to image file
            deep_scan: Enable more thorough (slower) analysis

        Returns:
            SecurityScanResult with complete analysis
        """
        result = SecurityScanResult()

        # Validate file exists
        if not os.path.exists(image_path):
            result.is_safe = False
            result.threat_level = ThreatLevel.CRITICAL
            result.warnings.append("File not found")
            return result

        # Get file info
        result.file_size = os.path.getsize(image_path)
        self._compute_hashes(image_path, result)

        # Run detectors
        detector_results = {}

        # 1. File Structure (always run)
        result.file_structure = self.file_structure_detector.analyze(image_path)
        detector_results['file_structure'] = result.file_structure
        self._process_file_structure_result(result)

        # 2. File Size Analysis
        if self.file_size_detector:
            self.file_size_detector.analyze(image_path, result)

        # 3. Entropy Analysis
        if self.entropy_detector:
            result.entropy = self.entropy_detector.analyze(
                image_path,
                result.file_structure.detected_format if result.file_structure else None
            )
            detector_results['entropy'] = result.entropy
            self._process_entropy_result(result)

        # 3. LSB Analysis
        if self.lsb_detector:
            result.lsb = self.lsb_detector.analyze(image_path)
            detector_results['lsb'] = result.lsb
            self._process_lsb_result(result)

        # 4. DCT Analysis (JPEG only)
        if self.dct_detector and result.file_structure:
            if result.file_structure.detected_format == 'JPEG':
                result.dct = self.dct_detector.analyze(image_path)
                detector_results['dct'] = result.dct
                self._process_dct_result(result)

        # 5. Metadata Analysis
        if self.metadata_detector:
            result.metadata = self.metadata_detector.analyze(image_path)
            detector_results['metadata'] = result.metadata
            self._process_metadata_result(result)

        # 6. Heuristics (combines all results)
        if self.heuristics_detector:
            result.heuristics = self.heuristics_detector.analyze(
                image_path, detector_results
            )
            self._process_heuristics_result(result)

        # Calculate final threat level
        self._calculate_threat_level(result)

        # Generate recommendations
        self._generate_recommendations(result)

        return result

    def _compute_hashes(self, image_path: str, result: SecurityScanResult):
        """Compute file hashes"""
        try:
            with open(image_path, 'rb') as f:
                content = f.read()
                result.file_hash_md5 = hashlib.md5(content).hexdigest()
                result.file_hash_sha256 = hashlib.sha256(content).hexdigest()
        except Exception:
            pass

    def _process_file_structure_result(self, result: SecurityScanResult):
        """Process file structure detector results"""
        fs = result.file_structure
        if not fs:
            return

        if not fs.is_valid_image:
            result.is_safe = False
            result.warnings.append("Invalid image file structure")

        if fs.has_embedded_data:
            result.is_safe = False
            result.has_embedded_data = True
            result.embedded_type = fs.embedded_type
            result.malware_detected = True

        if fs.has_trailing_data:
            result.is_safe = False
            result.has_embedded_data = True

        if fs.has_hidden_markers:
            result.is_safe = False
            result.has_embedded_data = True
            result.malware_detected = True

        # New interface uses 'suspicious' and 'confidence'
        if hasattr(fs, 'suspicious') and fs.suspicious:
            result.is_safe = False

        if hasattr(fs, 'confidence') and fs.confidence > 0.5:
            result.is_safe = False

        result.warnings.extend(fs.warnings)

    def _process_entropy_result(self, result: SecurityScanResult):
        """Process entropy detector results"""
        ent = result.entropy
        if not ent:
            return

        if ent.is_anomalous:
            result.steganography_detected = True

        result.warnings.extend(ent.warnings)

    def _process_lsb_result(self, result: SecurityScanResult):
        """Process LSB detector results"""
        lsb = result.lsb
        if not lsb:
            return

        if lsb.has_lsb_anomaly:
            result.steganography_detected = True

        if lsb.chi_square_suspicious:
            result.steganography_detected = True

        result.warnings.extend(lsb.warnings)

    def _process_dct_result(self, result: SecurityScanResult):
        """Process DCT detector results"""
        dct = result.dct
        if not dct:
            return

        # New interface uses 'suspicious' and 'confidence'
        if hasattr(dct, 'suspicious') and dct.suspicious:
            result.steganography_detected = True

        # Also check confidence score
        if hasattr(dct, 'confidence') and dct.confidence > 0.5:
            result.steganography_detected = True

        # Legacy attribute support
        if hasattr(dct, 'has_dct_anomaly') and dct.has_dct_anomaly:
            result.steganography_detected = True

        if hasattr(dct, 'jsteg_suspicious') and dct.jsteg_suspicious:
            result.steganography_detected = True

        if hasattr(dct, 'f5_suspicious') and dct.f5_suspicious:
            result.steganography_detected = True

        result.warnings.extend(dct.warnings)

    def _process_metadata_result(self, result: SecurityScanResult):
        """Process metadata detector results"""
        meta = result.metadata
        if not meta:
            return

        # New interface uses 'has_script' and 'suspicious'
        if hasattr(meta, 'has_script') and meta.has_script:
            result.is_safe = False
            result.malware_detected = True
            result.suspicious_metadata = True

        if hasattr(meta, 'suspicious') and meta.suspicious:
            result.suspicious_metadata = True

        # Legacy attribute support
        if hasattr(meta, 'has_script_injection') and meta.has_script_injection:
            result.is_safe = False
            result.malware_detected = True
            result.suspicious_metadata = True

        if hasattr(meta, 'has_suspicious_metadata') and meta.has_suspicious_metadata:
            result.suspicious_metadata = True

        # Copy EXIF for legacy compatibility
        if hasattr(meta, 'exif_data'):
            result.exif_data = meta.exif_data
        elif hasattr(meta, 'exif'):
            result.exif_data = meta.exif

        result.warnings.extend(meta.warnings)

    def _process_heuristics_result(self, result: SecurityScanResult):
        """Process heuristics detector results"""
        heur = result.heuristics
        if not heur:
            return

        result.risk_score = heur.risk_score

        if heur.risk_level in ['high', 'critical']:
            result.is_safe = False

        result.warnings.extend(heur.warnings)
        result.recommendations.extend(heur.recommendations)

    def _calculate_threat_level(self, result: SecurityScanResult):
        """Calculate overall threat level"""
        if result.malware_detected:
            result.threat_level = ThreatLevel.CRITICAL
            result.is_safe = False
        elif result.has_embedded_data:
            result.threat_level = ThreatLevel.HIGH
            result.is_safe = False
        elif result.steganography_detected:
            result.threat_level = ThreatLevel.MEDIUM
        elif result.suspicious_metadata:
            result.threat_level = ThreatLevel.LOW
        elif result.risk_score > 0.4:
            result.threat_level = ThreatLevel.MEDIUM
        elif result.risk_score > 0.2:
            result.threat_level = ThreatLevel.LOW
        else:
            result.threat_level = ThreatLevel.SAFE
            result.is_safe = True

    def _generate_recommendations(self, result: SecurityScanResult):
        """Generate security recommendations"""
        if result.threat_level == ThreatLevel.CRITICAL:
            if "BLOCK" not in str(result.recommendations):
                result.recommendations.insert(0, "BLOCK: Do not process this image")
        elif result.threat_level == ThreatLevel.HIGH:
            if "REVIEW" not in str(result.recommendations):
                result.recommendations.insert(0, "REVIEW: Manual inspection required")
        elif result.threat_level == ThreatLevel.MEDIUM:
            if "CAUTION" not in str(result.recommendations):
                result.recommendations.insert(0, "CAUTION: Additional verification recommended")

    # Legacy method for compatibility
    def compute_hash(self, image_path: str) -> Dict[str, str]:
        """Compute file hashes (legacy method)"""
        hashes = {}
        try:
            with open(image_path, 'rb') as f:
                content = f.read()
                hashes['md5'] = hashlib.md5(content).hexdigest()
                hashes['sha256'] = hashlib.sha256(content).hexdigest()
        except Exception as e:
            hashes['error'] = str(e)
        return hashes


# Convenience function
def scan_image(image_path: str, deep_scan: bool = False) -> SecurityScanResult:
    """
    Quick function to scan an image for security threats.

    Args:
        image_path: Path to image file
        deep_scan: Enable thorough analysis

    Returns:
        SecurityScanResult
    """
    scanner = SecurityScanner()
    return scanner.scan(image_path, deep_scan)

