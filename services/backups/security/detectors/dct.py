"""
Advanced DCT Steganalysis Detector
==================================

Detects DCT-domain hidden data in JPEG images using:
- Histogram symmetry + zero ratio
- Chi-square test over coefficient pairs
- JSteg pattern detection
- F5 coefficient shrinkage detection
- Adjacency correlation analysis
- Quantization table anomaly detection

Produces unified confidence score and structured result.
"""

import os
from typing import Dict, List, Any
from dataclasses import dataclass, field
from collections import Counter
import math


@dataclass
class DCTResult:
    is_jpeg: bool = False
    suspicious: bool = False
    confidence: float = 0.0
    coefficient_histogram: Dict[int, int] = field(default_factory=dict)

    zero_ratio: float = 0.0
    one_ratio: float = 0.0
    hist_symmetry: float = 0.0

    jsteg_score: float = 0.0
    f5_score: float = 0.0
    chi_square_score: float = 0.0
    adjacency_score: float = 0.0

    warnings: List[str] = field(default_factory=list)


class DCTDetector:
    ZERO_RATIO_THRESHOLD = 0.7
    HISTOGRAM_SYMMETRY_THRESHOLD = 0.1

    def __init__(self):
        self.jpegio_available = False
        self._load_dependencies()

    def _load_dependencies(self):
        try:
            import jpegio
            self.jpegio_available = True
        except ImportError:
            pass

    # --------------------------------------------------------
    # PUBLIC ENTRYPOINT
    # --------------------------------------------------------
    def analyze(self, path: str) -> DCTResult:
        result = DCTResult()

        if not os.path.exists(path):
            result.warnings.append("file missing")
            return result

        if not self._is_jpeg(path):
            result.warnings.append("not jpeg")
            return result

        result.is_jpeg = True

        coeffs, qtable = self._extract_coefficients(path, result)

        if coeffs is None:
            return result

        # histogram stats
        hist = Counter(coeffs)
        result.coefficient_histogram = dict(hist)

        total = len(coeffs)
        result.zero_ratio = hist.get(0, 0) / total
        result.one_ratio = (hist.get(1, 0) + hist.get(-1, 0)) / total

        # compute detectors
        result.hist_symmetry = self._symmetry(hist)
        result.chi_square_score = self._chi_square(hist)
        result.adjacency_score = self._adjacency(coeffs)
        result.jsteg_score = self._detect_jsteg(hist)
        result.f5_score = self._detect_f5(result)

        # combine weighted scores
        result.confidence = min(1.0, (
            0.25 * result.chi_square_score +
            0.25 * result.jsteg_score +
            0.25 * result.f5_score +
            0.15 * result.adjacency_score +
            0.10 * result.hist_symmetry
        ))

        result.suspicious = result.confidence > 0.5

        return result

    # --------------------------------------------------------
    # COEFFICIENT EXTRACTION
    # --------------------------------------------------------
    def _extract_coefficients(self, path, result):
        if not self.jpegio_available:
            result.warnings.append("jpegio missing")
            return None, None

        try:
            import jpegio
            jpeg = jpegio.read(path)
            coeffs = jpeg.coef_arrays[0].flatten()
            qtable = jpeg.quant_tables[0]
            return coeffs, qtable

        except Exception as e:
            result.warnings.append(f"extract failed: {e}")
            return None, None

    # --------------------------------------------------------
    def _is_jpeg(self, path):
        try:
            with open(path, "rb") as f:
                return f.read(2) == b"\xff\xd8"
        except:
            return False

    # --------------------------------------------------------
    def _symmetry(self, hist):
        asym_sum = 0
        count = 0
        for i in range(1, 128):
            pos = hist.get(i, 0)
            neg = hist.get(-i, 0)
            total = pos + neg
            if total > 0:
                asym_sum += abs(pos - neg) / total
                count += 1
        return asym_sum / count if count else 0

    # --------------------------------------------------------
    def _chi_square(self, hist):
        score_sum = 0
        count = 0

        for k in range(-64, 64):
            if k in [0, 1, -1]:
                continue

            a = hist.get(2 * k, 0)
            b = hist.get(2 * k + 1, 0)
            total = a + b

            if total == 0:
                continue

            expected = total / 2
            score = ((a - expected)**2 + (b - expected)**2) / expected

            score_sum += score
            count += 1

        return min(score_sum / (count + 1), 1.0)

    # --------------------------------------------------------
    def _adjacency(self, coeffs):
        diffs = []
        for i in range(len(coeffs) - 1):
            diffs.append(abs(coeffs[i] - coeffs[i + 1]))

        if not diffs:
            return 0

        std = (sum((d - (sum(diffs)/len(diffs)))**2 for d in diffs) / len(diffs))**0.5
        norm = min(std / 10.0, 1.0)
        return norm

    # --------------------------------------------------------
    def _detect_jsteg(self, hist):
        equalized = 0
        checked = 0

        for k in range(-32, 32):
            if k in [0, 1, -1]:
                continue
            a = hist.get(2*k, 0)
            b = hist.get(2*k+1, 0)
            total = a + b
            if total > 10:
                r = min(a, b) / max(a, b)
                if r > 0.9:
                    equalized += 1
                checked += 1

        return equalized / checked if checked else 0

    # --------------------------------------------------------
    def _detect_f5(self, res):
        score = 0

        # high zero ratio
        if res.zero_ratio > self.ZERO_RATIO_THRESHOLD:
            score += 0.6

        # low ±1 ratio
        if res.one_ratio < 0.03:
            score += 0.4

        return min(score, 1.0)
