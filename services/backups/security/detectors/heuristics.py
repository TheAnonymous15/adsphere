"""
Heuristics Detector - Enhanced Version
=====================================

Improved heuristic detection for steganography/security anomalies:

Signals evaluated:
- File size vs dimensions vs format
- Compression anomalies cross-checked w/ entropy
- Structure ranges and aspect ratio
- LSB / trailing data / metadata anomalies from other detectors
- Optional EXIF + thumbnail analysis
- Hash reputation lookup (optional future hook)

This detector assigns risk scores & recommendations.
"""

import os
import hashlib
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field


@dataclass
class HeuristicsResult:
    risk_score: float = 0.0
    risk_level: str = "low"
    anomalies_detected: int = 0

    file_size_anomaly: bool = False
    compression_anomaly: bool = False
    quality_anomaly: bool = False
    structure_anomaly: bool = False
    entropy_anomaly: bool = False

    features: Dict[str, float] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


class HeuristicsDetector:

    EXPECTED_BPP = {
        'JPEG': (0.35, 2.0),
        'PNG': (0.4, 4.2),
        'GIF': (0.15, 1.0),
        'BMP': (2.5, 5.0),
        'WEBP': (0.25, 1.8),
        'TIFF': (1.0, 5.0),
    }

    # Risk weights
    WEIGHTS = {
        'file_size': 0.10,
        'compression': 0.15,
        'quality': 0.10,
        'structure': 0.15,
        'entropy': 0.20,
        'trailing': 0.30,
        'hidden_markers': 0.30,
        'lsb': 0.25,
        'metadata': 0.15,
        'embedded_exec': 0.50,
    }

    def __init__(self):
        self.pillow_available = False
        self._load_dependencies()

    def _load_dependencies(self):
        try:
            from PIL import Image
            self.pillow_available = True
        except ImportError:
            pass

    def analyze(self, image_path: str, other_results: Dict[str, Any] = None) -> HeuristicsResult:
        result = HeuristicsResult()

        if not os.path.exists(image_path):
            result.warnings.append("File does not exist")
            return result

        file_size = os.path.getsize(image_path)
        result.features["file_size_bytes"] = file_size

        self._check_file_size(file_size, result)

        if self.pillow_available:
            self._image_stats(image_path, file_size, result)

        if other_results:
            self._merge_detector_results(other_results, result)

        self._compute_score(result)
        self._derive_risk_level(result)
        self._recommendations(result)

        return result

    # ---------------------------
    #  file heuristics
    # ---------------------------
    def _check_file_size(self, size: int, result: HeuristicsResult):
        if size < 100:
            result.file_size_anomaly = True
            result.anomalies_detected += 1
            result.warnings.append("Extremely small file – likely abnormal")

        if size > 50 * 1024 * 1024:
            result.file_size_anomaly = True
            result.anomalies_detected += 1
            result.warnings.append("Very large file – check for embedded content")

    # ---------------------------
    #  image-based heuristics
    # ---------------------------
    def _image_stats(self, path: str, file_size: int, res: HeuristicsResult):
        try:
            from PIL import Image
            from PIL.ExifTags import TAGS

            with Image.open(path) as img:
                w, h = img.size
                fmt = img.format or "UNKNOWN"

                res.features.update({
                    "width": w,
                    "height": h,
                    "format": fmt,
                    "mode": img.mode,
                })

                pixels = w * h
                if pixels > 0:
                    bpp = file_size / pixels
                    res.features["bpp"] = bpp

                    # main compression heuristic
                    low, high = self.EXPECTED_BPP.get(fmt, (0.2, 5.0))

                    if bpp < low * 0.5:
                        res.compression_anomaly = True
                        res.anomalies_detected += 1
                        res.warnings.append(f"High compression ratio ({bpp:.3f} BPP)")

                    if bpp > high * 1.4:
                        res.compression_anomaly = True
                        res.anomalies_detected += 1
                        res.warnings.append(f"BPP unusually high ({bpp:.3f}) – suspicious padding")

                # extreme dimension risks
                if w < 10 or h < 10:
                    res.structure_anomaly = True
                    res.anomalies_detected += 1

                if w > 10000 or h > 10000:
                    res.structure_anomaly = True
                    res.anomalies_detected += 1

                # aspect ratio
                if min(w, h) > 0:
                    ar = max(w, h) / min(w, h)
                    res.features["aspect_ratio"] = ar
                    if ar > 20:
                        res.quality_anomaly = True
                        res.warnings.append(f"Extreme aspect ratio: {ar:.1f}")

                # optional: EXIF thumbnail anomaly
                try:
                    exif = img.getexif()
                    if exif:
                        for k, v in exif.items():
                            tag = TAGS.get(k, k)
                            if tag == 'JPEGThumbnail' and v and len(v) > 50_000:
                                res.quality_anomaly = True
                                res.warnings.append(
                                    f"EXIF thumbnail unusually large ({len(v)})"
                                )
                except Exception:
                    pass

        except Exception as e:
            res.structure_anomaly = True
            res.anomalies_detected += 1
            res.warnings.append(f"Image decode error: {e}")

    # ---------------------------
    #  merge detector results
    # ---------------------------
    def _merge_detector_results(self, others, res: HeuristicsResult):
        # example – plug LSB, entropy, metadata, file structure
        if fs := others.get("file_structure"):
            if getattr(fs, "has_trailing_data", False):
                res.features["trailing"] = 1
            if getattr(fs, "has_hidden_markers", False):
                res.features["hidden_markers"] = 1
            if getattr(fs, "has_embedded_data", False):
                res.features["embedded_exec"] = 1

        if ent := others.get("entropy"):
            res.entropy_anomaly = getattr(ent, "is_anomalous", False)
            if ent.overall_entropy:
                res.features["entropy"] = ent.overall_entropy

        if lsb := others.get("lsb"):
            if getattr(lsb, "has_lsb_anomaly", False):
                res.features["lsb"] = 1
            res.features["lsb_ratio"] = getattr(lsb, "lsb_ratio", 0)

        if meta := others.get("metadata"):
            if getattr(meta, "has_suspicious_metadata", False):
                res.features["metadata"] = 1

    # ---------------------------
    #  scoring + risk
    # ---------------------------
    def _compute_score(self, r):
        score = 0

        if r.file_size_anomaly:
            score += self.WEIGHTS["file_size"]
        if r.compression_anomaly:
            score += self.WEIGHTS["compression"]
        if r.quality_anomaly:
            score += self.WEIGHTS["quality"]
        if r.structure_anomaly:
            score += self.WEIGHTS["structure"]
        if r.entropy_anomaly:
            score += self.WEIGHTS["entropy"]

        # combined risk propagation
        for feat, val in r.features.items():
            if val and feat in self.WEIGHTS:
                score += self.WEIGHTS[feat]

        r.risk_score = min(1.0, score)

    def _derive_risk_level(self, r):
        if r.risk_score >= 0.7:
            r.risk_level = "critical"
        elif r.risk_score >= 0.45:
            r.risk_level = "high"
        elif r.risk_score >= 0.25:
            r.risk_level = "medium"
        else:
            r.risk_level = "low"

    def _recommendations(self, r):
        if r.risk_level == "critical":
            r.recommendations += [
                "Block immediately",
                "Quarantine the file",
                "Do not decode or serve to clients"
            ]
        elif r.risk_level == "high":
            r.recommendations.append("Manual review required")
        elif r.risk_level == "medium":
            r.recommendations.append("Reprocess/re-encode recommended")
        else:
            r.recommendations.append("No action required")

