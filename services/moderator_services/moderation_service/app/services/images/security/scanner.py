"""
Security Scanner
================

Main orchestrator for image security scanning with integrated sanitization
and compression. Uses ML-powered detectors for comprehensive analysis.

Pipeline:
1. Scan image for threats (ML detectors)
2. Sanitize image (remove hidden data, re-encode)
3. Compress to WebP ≤ 1MB (reduce processing time)
4. Pass compressed image to OCR processor

    ┌──────────┐   ┌───────────┐   ┌────────────┐   ┌─────────┐
    │ SCANNER  │──▶│ SANITIZER │──▶│ COMPRESSOR │──▶│   OCR   │
    └──────────┘   └───────────┘   └────────────┘   └─────────┘

The scanner ensures that only clean, safe, optimized images reach
downstream processors like OCR.
"""

import os
import io
import hashlib
from typing import Dict, List, Any, Optional, Tuple, Callable
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
from .image_sanitizer import ImageSanitizer, SanitizeResult

# Import compressor from parent images directory
import sys
from pathlib import Path
_images_dir = str(Path(__file__).parent.parent)
if _images_dir not in sys.path:
    sys.path.insert(0, _images_dir)

try:
    from image_compressor import ImageCompressor, CompressionResult
except ImportError:
    # Fallback if import fails
    ImageCompressor = None
    CompressionResult = None


class ThreatLevel(Enum):
    """Threat severity levels"""
    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class SecurityScanResult:
    """Complete security scan result with sanitization and compression"""
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
    manipulation_detected: bool = False

    # Individual detector results
    file_structure: Optional[FileStructureResult] = None
    entropy: Optional[EntropyResult] = None
    lsb: Optional[LSBResult] = None
    dct: Optional[DCTResult] = None
    metadata: Optional[MetadataResult] = None
    heuristics: Optional[HeuristicsResult] = None
    ml_steg: Optional[MLStegResult] = None
    ml_forensics: Optional[ForensicsResult] = None
    ml_hidden: Optional[HiddenDataResult] = None

    # Sanitization results
    sanitized: bool = False
    sanitize_result: Optional[SanitizeResult] = None
    sanitized_data: Optional[bytes] = None  # Clean image data after sanitization
    sanitized_path: Optional[str] = None  # Path to sanitized file (if saved)

    # Compression results
    compressed: bool = False
    compression_result: Optional[Any] = None  # CompressionResult
    compressed_data: Optional[bytes] = None  # Final compressed image for OCR
    compressed_size: int = 0
    compression_ratio: float = 0.0

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
    ML-Powered Image Security Scanner with Integrated Sanitization & Compression.

    Pipeline: Scan → Sanitize → Compress → OCR

    ┌──────────┐   ┌───────────┐   ┌────────────┐   ┌─────────┐
    │ SCANNER  │──▶│ SANITIZER │──▶│ COMPRESSOR │──▶│   OCR   │
    └──────────┘   └───────────┘   └────────────┘   └─────────┘

    Primary detectors (ML-based):
    1. ML Steg - Deep learning steganography detection
    2. ML Forensics - Image manipulation/forgery detection
    3. ML Hidden - Hidden/embedded data detection

    Optional traditional detectors:
    - File Structure - signatures, EOF, hidden markers
    - File Size - size and compression anomalies
    - Entropy - statistical anomalies
    - LSB - least significant bit steganography
    - DCT - JPEG steganography
    - Metadata - EXIF/XMP malware
    - Heuristics - combined risk assessment

    Usage:
        # Full pipeline: Scan → Sanitize → Compress → OCR
        scanner = SecurityScanner()
        result, ocr_result = scanner.scan_and_process(
            "image.jpg",
            ocr_callback=my_ocr_processor
        )

        # Access compressed data (WebP ≤ 1MB)
        if result.compressed:
            compressed_webp = result.compressed_data
    """

    def __init__(
        self,
        # ML detectors (enabled by default)
        enable_ml_steg: bool = True,
        enable_ml_forensics: bool = True,
        enable_ml_hidden: bool = True,
        use_gpu: bool = False,
        # Sanitization (enabled by default)
        auto_sanitize: bool = True,
        # Compression (enabled by default)
        auto_compress: bool = True,
        target_size: int = 1024 * 1024,  # 1 MB
        # Traditional detectors (disabled by default)
        enable_traditional: bool = False,
        enable_file_structure: bool = None,
        enable_file_size: bool = None,
        enable_entropy: bool = None,
        enable_lsb: bool = None,
        enable_dct: bool = None,
        enable_metadata: bool = None,
        enable_heuristics: bool = None,
    ):
        """
        Initialize security scanner.

        Args:
            enable_ml_steg: Enable ML steganography detection (default: True)
            enable_ml_forensics: Enable ML forensics detection (default: True)
            enable_ml_hidden: Enable ML hidden data detection (default: True)
            use_gpu: Use GPU acceleration for ML models
            auto_sanitize: Automatically sanitize images after scanning (default: True)
            auto_compress: Automatically compress to WebP ≤ target_size (default: True)
            target_size: Target compression size in bytes (default: 1MB)
            enable_traditional: Enable all traditional detectors (default: False)
            enable_file_structure: Enable file structure analysis
            enable_file_size: Enable file size analysis
            enable_entropy: Enable entropy analysis
            enable_lsb: Enable LSB steganography detection
            enable_dct: Enable DCT steganography detection
            enable_metadata: Enable metadata analysis
            enable_heuristics: Enable heuristic analysis
        """
        self.auto_sanitize = auto_sanitize
        self.auto_compress = auto_compress
        self.target_size = target_size

        # Initialize sanitizer
        self.sanitizer = ImageSanitizer(strip_metadata=True, re_encode=True)

        # Initialize compressor
        self.compressor = None
        if ImageCompressor is not None:
            self.compressor = ImageCompressor(target_size=target_size, output_format="webp")

        # ML-enhanced detectors (primary)
        self.ml_steg_detector = MLStegDetector(use_gpu=use_gpu) if enable_ml_steg else None
        self.ml_forensics_detector = MLForensicsDetector(use_gpu=use_gpu) if enable_ml_forensics else None
        self.ml_hidden_detector = MLHiddenDataDetector(use_gpu=use_gpu) if enable_ml_hidden else None

        # Traditional detectors (optional)
        # If enable_traditional is True, enable all unless explicitly disabled
        # If enable_traditional is False, only enable if explicitly enabled
        def should_enable(specific_flag, default_when_traditional=True):
            if specific_flag is not None:
                return specific_flag
            return enable_traditional and default_when_traditional

        # File structure is always enabled for basic validation
        self.file_structure_detector = FileStructureDetector() if should_enable(enable_file_structure, True) or enable_traditional else None
        self.file_size_detector = FileSizeDetector() if should_enable(enable_file_size) else None
        self.entropy_detector = EntropyDetector() if should_enable(enable_entropy) else None
        self.lsb_detector = LSBDetector() if should_enable(enable_lsb) else None
        self.dct_detector = DCTDetector() if should_enable(enable_dct) else None
        self.metadata_detector = MetadataDetector() if should_enable(enable_metadata) else None
        self.heuristics_detector = HeuristicsDetector() if should_enable(enable_heuristics) else None

    def scan(self, image_path: str, deep_scan: bool = False) -> SecurityScanResult:
        """
        Perform security scan on image.

        Args:
            image_path: Path to image file
            deep_scan: Enable more thorough analysis

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

        # === ML DETECTORS (Primary) ===

        # 1. ML Steganography Detection
        if self.ml_steg_detector:
            result.ml_steg = self.ml_steg_detector.analyze(image_path)
            detector_results['ml_steg'] = result.ml_steg
            self._process_ml_steg_result(result)

        # 2. ML Forensics Detection
        if self.ml_forensics_detector:
            result.ml_forensics = self.ml_forensics_detector.analyze(image_path)
            detector_results['ml_forensics'] = result.ml_forensics
            self._process_ml_forensics_result(result)

        # 3. ML Hidden Data Detection
        if self.ml_hidden_detector:
            result.ml_hidden = self.ml_hidden_detector.analyze(image_path)
            detector_results['ml_hidden'] = result.ml_hidden
            self._process_ml_hidden_result(result)

        # === TRADITIONAL DETECTORS (Optional) ===

        # 4. File Structure
        if self.file_structure_detector:
            result.file_structure = self.file_structure_detector.analyze(image_path)
            detector_results['file_structure'] = result.file_structure
            self._process_file_structure_result(result)

        # 4. File Size Analysis
        if self.file_size_detector:
            self.file_size_detector.analyze(image_path, result)

        # 5. Entropy Analysis
        if self.entropy_detector:
            fmt = result.file_structure.detected_format if result.file_structure else None
            result.entropy = self.entropy_detector.analyze(image_path, fmt)
            detector_results['entropy'] = result.entropy
            self._process_entropy_result(result)

        # 6. LSB Analysis
        if self.lsb_detector:
            result.lsb = self.lsb_detector.analyze(image_path)
            detector_results['lsb'] = result.lsb
            self._process_lsb_result(result)

        # 7. DCT Analysis (JPEG only)
        if self.dct_detector:
            fmt = result.file_structure.detected_format if result.file_structure else None
            if fmt == 'JPEG' or self._is_jpeg(image_path):
                result.dct = self.dct_detector.analyze(image_path)
                detector_results['dct'] = result.dct
                self._process_dct_result(result)

        # 8. Metadata Analysis
        if self.metadata_detector:
            result.metadata = self.metadata_detector.analyze(image_path)
            detector_results['metadata'] = result.metadata
            self._process_metadata_result(result)

        # 9. Heuristics (combines all results)
        if self.heuristics_detector:
            result.heuristics = self.heuristics_detector.analyze(image_path, detector_results)
            self._process_heuristics_result(result)

        # Calculate final threat level
        self._calculate_threat_level(result)

        # Generate recommendations
        self._generate_recommendations(result)

        # Auto-sanitize if enabled
        if self.auto_sanitize:
            self._sanitize_image(image_path, result)

        # Auto-compress if enabled (after sanitization)
        if self.auto_compress and result.sanitized:
            self._compress_image(result)

        return result

    def scan_and_sanitize(
        self,
        image_path: str,
        output_path: Optional[str] = None,
        deep_scan: bool = False
    ) -> SecurityScanResult:
        """
        Scan image and return sanitized version.

        Args:
            image_path: Path to image file
            output_path: Optional path to save sanitized image
            deep_scan: Enable thorough analysis

        Returns:
            SecurityScanResult with sanitized_data containing clean image
        """
        # Ensure auto_sanitize is on for this call
        original_auto_sanitize = self.auto_sanitize
        self.auto_sanitize = True

        try:
            result = self.scan(image_path, deep_scan)

            # Save to output path if specified
            if output_path and result.sanitized_data:
                with open(output_path, 'wb') as f:
                    f.write(result.sanitized_data)
                result.sanitized_path = output_path

            return result
        finally:
            self.auto_sanitize = original_auto_sanitize

    def scan_and_process(
        self,
        image_path: str,
        ocr_callback: Optional[Callable[[bytes], Any]] = None,
        deep_scan: bool = False
    ) -> Tuple[SecurityScanResult, Any]:
        """
        Full pipeline: Scan → Sanitize → Compress → OCR

        This is the main pipeline entry point:
        1. Scan for security threats (ML detectors)
        2. Sanitize to remove hidden data
        3. Compress to WebP ≤ 1MB
        4. Pass compressed image to OCR processor

        Args:
            image_path: Path to image file
            ocr_callback: Function that receives compressed image bytes (WebP ≤ 1MB)
                         and returns OCR/processing results
            deep_scan: Enable thorough analysis

        Returns:
            Tuple of (SecurityScanResult, OCR results or None)
        """
        # Ensure both sanitize and compress are enabled for this call
        original_auto_sanitize = self.auto_sanitize
        original_auto_compress = self.auto_compress
        self.auto_sanitize = True
        self.auto_compress = True

        try:
            # Run full pipeline: Scan → Sanitize → Compress
            result = self.scan(image_path, deep_scan)

            ocr_result = None

            # Pass compressed data to OCR (preferred) or fall back to sanitized
            image_for_ocr = result.compressed_data or result.sanitized_data

            if image_for_ocr and ocr_callback:
                try:
                    ocr_result = ocr_callback(image_for_ocr)
                except Exception as e:
                    result.warnings.append(f"OCR processing failed: {e}")

            return result, ocr_result

        finally:
            self.auto_sanitize = original_auto_sanitize
            self.auto_compress = original_auto_compress

    def _sanitize_image(self, image_path: str, result: SecurityScanResult):
        """Sanitize image and store result"""
        try:
            # Read original image
            with open(image_path, 'rb') as f:
                image_data = f.read()

            # Sanitize in memory
            sanitized_data, sanitize_result = self.sanitizer.sanitize_bytes(image_data)

            result.sanitize_result = sanitize_result

            if sanitize_result.success:
                result.sanitized = True
                result.sanitized_data = sanitized_data

                # Log what was cleaned
                if sanitize_result.appended_data_removed:
                    result.warnings.append(
                        f"Sanitizer: Removed {sanitize_result.bytes_removed} bytes of appended data"
                    )
                if sanitize_result.markers_removed:
                    result.warnings.append(
                        f"Sanitizer: Removed hidden markers: {sanitize_result.markers_removed}"
                    )
                if sanitize_result.re_encoded:
                    result.warnings.append("Sanitizer: Image re-encoded (LSB stego removed)")
            else:
                result.warnings.append(f"Sanitization failed: {sanitize_result.error}")
                # Still store original data if sanitization failed
                result.sanitized_data = image_data

        except Exception as e:
            result.warnings.append(f"Sanitization error: {e}")

    def _compress_image(self, result: SecurityScanResult):
        """Compress sanitized image to WebP ≤ target size"""
        if not self.compressor:
            result.warnings.append("Compressor not available")
            return

        if not result.sanitized_data:
            result.warnings.append("No sanitized data to compress")
            return

        try:
            # Compress sanitized image
            compression_result = self.compressor.compress(result.sanitized_data)

            result.compression_result = compression_result

            if compression_result.success:
                result.compressed = True
                result.compressed_data = compression_result.compressed_data
                result.compressed_size = compression_result.compressed_size
                result.compression_ratio = compression_result.compression_ratio

                # Log compression info
                original_kb = len(result.sanitized_data) / 1024
                compressed_kb = compression_result.compressed_size / 1024

                result.warnings.append(
                    f"Compressor: {original_kb:.0f}KB → {compressed_kb:.0f}KB "
                    f"({compression_result.compression_ratio:.1f}x, quality={compression_result.final_quality})"
                )

                if compression_result.was_resized:
                    result.warnings.append(
                        f"Compressor: Image resized from {compression_result.original_dimensions} "
                        f"to {compression_result.final_dimensions}"
                    )
            else:
                result.warnings.append(f"Compression failed: {compression_result.error}")
                # Fall back to sanitized data
                result.compressed_data = result.sanitized_data
                result.compressed_size = len(result.sanitized_data)

        except Exception as e:
            result.warnings.append(f"Compression error: {e}")
            # Fall back to sanitized data
            result.compressed_data = result.sanitized_data

    def _is_jpeg(self, image_path: str) -> bool:
        """Check if file is JPEG"""
        try:
            with open(image_path, 'rb') as f:
                return f.read(3) == b'\xff\xd8\xff'
        except:
            return False

    def _compute_hashes(self, image_path: str, result: SecurityScanResult):
        """Compute file hashes"""
        try:
            with open(image_path, 'rb') as f:
                content = f.read()
                result.file_hash_md5 = hashlib.md5(content).hexdigest()
                result.file_hash_sha256 = hashlib.sha256(content).hexdigest()
        except Exception:
            pass

    # === ML RESULT PROCESSORS ===

    def _process_ml_steg_result(self, result: SecurityScanResult):
        """Process ML steganography detector results"""
        ml_steg = result.ml_steg
        if not ml_steg:
            return

        if ml_steg.has_steganography:
            result.steganography_detected = True
            result.risk_score = max(result.risk_score, ml_steg.confidence)

            if ml_steg.confidence > 0.7:
                result.is_safe = False
                result.warnings.append(
                    f"ML steganalysis: hidden data detected "
                    f"(confidence: {ml_steg.confidence:.1%}, type: {ml_steg.detected_type})"
                )
            elif ml_steg.confidence > 0.5:
                result.warnings.append(
                    f"ML steganalysis: possible hidden data "
                    f"(confidence: {ml_steg.confidence:.1%})"
                )

        if ml_steg.srm_features_anomaly:
            result.warnings.append("SRM features indicate potential steganography")

        result.warnings.extend(ml_steg.warnings)

    def _process_ml_forensics_result(self, result: SecurityScanResult):
        """Process ML forensics detector results"""
        forensics = result.ml_forensics
        if not forensics:
            return

        if forensics.is_manipulated:
            result.manipulation_detected = True
            result.risk_score = max(result.risk_score, forensics.manipulation_confidence)

            if forensics.manipulation_confidence > 0.7:
                result.warnings.append(
                    f"ML forensics: image manipulation detected "
                    f"(confidence: {forensics.manipulation_confidence:.1%})"
                )

        if forensics.ela_anomaly:
            result.warnings.append("ELA analysis detected manipulation regions")

        if forensics.copy_move_detected:
            result.warnings.append(
                f"Copy-move forgery detected ({len(forensics.copy_move_regions)} regions)"
            )

        if forensics.jpeg_ghost_detected:
            result.warnings.append("JPEG ghost artifacts (double compression detected)")

        if forensics.splicing_detected:
            result.warnings.append(
                f"Image splicing detected (confidence: {forensics.splicing_confidence:.1%})"
            )

        result.warnings.extend(forensics.warnings)

    def _process_ml_hidden_result(self, result: SecurityScanResult):
        """Process ML hidden data detector results"""
        hidden = result.ml_hidden
        if not hidden:
            return

        if hidden.has_hidden_data:
            result.has_embedded_data = True
            result.risk_score = max(result.risk_score, hidden.confidence)

            if hidden.confidence > 0.7:
                result.is_safe = False
                result.malware_detected = True

        # Check specific hidden data types
        if hidden.has_appended_data:
            result.has_embedded_data = True
            result.embedded_type = "appended_data"
            result.warnings.append(
                f"Data appended after EOF ({hidden.appended_size} bytes, "
                f"entropy: {hidden.appended_entropy:.2f})"
            )

        if hidden.has_hidden_markers:
            result.has_embedded_data = True
            result.is_safe = False
            result.malware_detected = True
            result.warnings.append(
                f"Hidden data markers detected: {', '.join(hidden.markers_found[:3])}"
            )
            if hidden.marker_content:
                result.warnings.append(f"Hidden content: {hidden.marker_content[:50]}...")

        if hidden.has_embedded_file:
            result.has_embedded_data = True
            result.is_safe = False
            result.malware_detected = True
            result.embedded_type = hidden.embedded_file_type
            result.warnings.append(
                f"Embedded {hidden.embedded_file_type} at offset {hidden.embedded_file_offset}"
            )

        if hidden.has_covert_channel:
            result.has_embedded_data = True
            result.warnings.append(
                f"Covert channel detected: {hidden.covert_channel_type}"
            )

        if hidden.has_steganographic_payload:
            result.steganography_detected = True
            result.warnings.append(
                f"Steganographic payload: {hidden.payload_type} "
                f"(confidence: {hidden.payload_confidence:.1%})"
            )

        result.warnings.extend(hidden.warnings)

    # === TRADITIONAL RESULT PROCESSORS ===

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

        if hasattr(fs, 'suspicious') and fs.suspicious:
            result.is_safe = False

        if hasattr(fs, 'confidence') and fs.confidence > 0.5:
            result.risk_score = max(result.risk_score, fs.confidence)

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

        if hasattr(dct, 'suspicious') and dct.suspicious:
            result.steganography_detected = True

        if hasattr(dct, 'confidence') and dct.confidence > 0.5:
            result.steganography_detected = True

        result.warnings.extend(dct.warnings)

    def _process_metadata_result(self, result: SecurityScanResult):
        """Process metadata detector results"""
        meta = result.metadata
        if not meta:
            return

        if hasattr(meta, 'has_script') and meta.has_script:
            result.is_safe = False
            result.malware_detected = True
            result.suspicious_metadata = True

        if hasattr(meta, 'suspicious') and meta.suspicious:
            result.suspicious_metadata = True

        if hasattr(meta, 'exif'):
            result.exif_data = meta.exif

        result.warnings.extend(meta.warnings)

    def _process_heuristics_result(self, result: SecurityScanResult):
        """Process heuristics detector results"""
        heur = result.heuristics
        if not heur:
            return

        result.risk_score = max(result.risk_score, heur.risk_score)

        if heur.risk_level in ['high', 'critical']:
            result.is_safe = False

        result.warnings.extend(heur.warnings)
        result.recommendations.extend(heur.recommendations)

    # === FINAL ASSESSMENT ===

    def _calculate_threat_level(self, result: SecurityScanResult):
        """Calculate overall threat level"""
        if result.malware_detected:
            result.threat_level = ThreatLevel.CRITICAL
            result.is_safe = False
        elif result.has_embedded_data:
            result.threat_level = ThreatLevel.HIGH
            result.is_safe = False
        elif result.steganography_detected and result.risk_score > 0.7:
            result.threat_level = ThreatLevel.HIGH
            result.is_safe = False
        elif result.steganography_detected:
            result.threat_level = ThreatLevel.MEDIUM
        elif result.manipulation_detected and result.risk_score > 0.7:
            result.threat_level = ThreatLevel.MEDIUM
        elif result.suspicious_metadata:
            result.threat_level = ThreatLevel.LOW
        elif result.risk_score > 0.5:
            result.threat_level = ThreatLevel.MEDIUM
        elif result.risk_score > 0.3:
            result.threat_level = ThreatLevel.LOW
        else:
            result.threat_level = ThreatLevel.SAFE
            result.is_safe = True

    def _generate_recommendations(self, result: SecurityScanResult):
        """Generate security recommendations"""
        if result.threat_level == ThreatLevel.CRITICAL:
            result.recommendations.insert(0, "BLOCK: Do not process this image")
        elif result.threat_level == ThreatLevel.HIGH:
            result.recommendations.insert(0, "REVIEW: Manual inspection required")
        elif result.threat_level == ThreatLevel.MEDIUM:
            result.recommendations.insert(0, "CAUTION: Additional verification recommended")
        elif result.threat_level == ThreatLevel.LOW:
            result.recommendations.insert(0, "NOTICE: Minor anomalies detected")

    # === LEGACY METHODS ===

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


# === CONVENIENCE FUNCTIONS ===

def scan_image(image_path: str, ml_only: bool = True) -> SecurityScanResult:
    """
    Quick function to scan an image for security threats.

    Args:
        image_path: Path to image file
        ml_only: Use only ML detectors (default: True)

    Returns:
        SecurityScanResult
    """
    scanner = SecurityScanner(enable_traditional=not ml_only)
    return scanner.scan(image_path)


def scan_image_full(image_path: str) -> SecurityScanResult:
    """
    Full scan with all detectors enabled.

    Args:
        image_path: Path to image file

    Returns:
        SecurityScanResult
    """
    scanner = SecurityScanner(enable_traditional=True)
    return scanner.scan(image_path)
