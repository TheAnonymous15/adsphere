"""
Improved LSB (Least Significant Bit) Detector
=============================================

Detects LSB-based steganography through:

1. LSB bit distribution analysis
2. Chi-square distribution flattening test
3. Sample pairs analysis (SPA)
4. Pairwise moment deviation (detects LSB matching)
5. Payload estimation + confidence score
6. Random pixel subsampling to detect dispersed embedding

Intended for lossless spatial-domain formats (BMP, PNG, TIFF).
JPEG steganography should be handled separately in DCT domain.
"""

import os
import math
import random
from typing import Dict, List, Any
from dataclasses import dataclass, field
from collections import Counter


@dataclass
class LSBResult:
    has_lsb_anomaly: bool = False

    # basic stats
    lsb_ratio: float = 0.5
    channel_analysis: Dict[str, float] = field(default_factory=dict)

    # χ² detection
    chi_square_value: float = 0.0
    chi_square_suspicious: bool = False

    # SPA
    sample_pairs_ratio: float = 0.0

    # additional improvements
    pairwise_moment_value: float = 0.0
    pairwise_suspicious: bool = False

    estimated_payload: float = 0.0      # percentage
    payload_confidence: float = 0.0     # probability estimate 0–1

    warnings: List[str] = field(default_factory=list)


class LSBDetector:

    # configurable thresholds
    LSB_RATIO_TOLERANCE = 0.15
    CHI_SQUARE_THRESHOLD = 0.05
    SAMPLE_PAIR_THRESHOLD = 0.10
    PAIRWISE_THRESHOLD = 1.4
    PAYLOAD_DETECTION_MIN = 0.05  # 5%
    SUBSAMPLE_SIZE = 60_000       # max pixels to sample

    def __init__(self):
        self.pillow_available = False
        self._load_dependencies()

    def _load_dependencies(self):
        try:
            from PIL import Image
            self.pillow_available = True
        except ImportError:
            pass

    # ------------------------------------------------------------
    # MAIN ANALYSIS ENTRYPOINT
    # ------------------------------------------------------------
    def analyze(self, image_path: str) -> LSBResult:
        result = LSBResult()

        if not self.pillow_available:
            result.warnings.append("PIL required for LSB analysis")
            return result

        if not os.path.exists(image_path):
            result.warnings.append("File not found")
            return result

        try:
            from PIL import Image

            with Image.open(image_path) as img:
                img = img.convert('RGB')
                pixels_full = list(img.getdata())

                # randomized subsampling
                pixels = self._subsample_pixels(pixels_full)

                if len(pixels) < 500:
                    result.warnings.append("Insufficient pixels for analysis")
                    return result

                self._analyze_lsb_ratio(pixels, result)
                self._chi_square_analysis(pixels, result)
                self._sample_pairs_analysis(pixels, result)
                self._pairwise_moment_test(pixels, result)

                self._estimate_payload(result)

        except Exception as e:
            result.warnings.append(f"LSB analysis failed: {e}")

        return result

    # ------------------------------------------------------------
    # RANDOM SUBSAMPLING
    # ------------------------------------------------------------
    def _subsample_pixels(self, pixels):
        """
        Random uniform sampling instead of sequential
        Helps detect dispersed LSB embedding.
        """
        if len(pixels) <= self.SUBSAMPLE_SIZE:
            return pixels

        return random.sample(pixels, self.SUBSAMPLE_SIZE)

    # ------------------------------------------------------------
    # ANALYSIS METHODS
    # ------------------------------------------------------------
    def _analyze_lsb_ratio(self, pixels, result):
        total = 0
        ones = 0
        channels = ['R','G','B']
        per_channel = {}

        for ci, channel_name in enumerate(channels):
            ch_total = ch_ones = 0

            for p in pixels:
                value = p[ci]
                ch_total += 1
                if value & 1:
                    ch_ones += 1

            per_channel[channel_name] = ch_ones / ch_total if ch_total else 0.5
            total += ch_total
            ones += ch_ones

        result.channel_analysis = per_channel
        result.lsb_ratio = ones / total if total else 0.5

        if abs(result.lsb_ratio - 0.5) > self.LSB_RATIO_TOLERANCE:
            result.has_lsb_anomaly = True
            result.warnings.append(
                f"Unusual LSB distribution ratio: {result.lsb_ratio:.3f}"
            )

    def _chi_square_analysis(self, pixels, result):
        freq = Counter()

        for p in pixels:
            for c in range(3):
                freq[p[c]] += 1

        chi = 0.0
        pairs = 0
        for k in range(128):
            a = freq.get(2*k, 0)
            b = freq.get(2*k+1, 0)
            exp = (a+b)/2
            if exp>0:
                chi += ((a-exp)**2)/exp + ((b-exp)**2)/exp
                pairs+=1

        if pairs>0:
            result.chi_square_value = chi/pairs

            if result.chi_square_value < self.CHI_SQUARE_THRESHOLD:
                result.chi_square_suspicious = True
                result.has_lsb_anomaly = True
                result.warnings.append(
                    "Chi-square suspicious — equalization detected"
                )

    def _sample_pairs_analysis(self, pixels, result):
        flips = count = 0
        N = min(len(pixels)-1, 20000)

        for i in range(0, N, 2):
            for c in range(3):
                v1 = pixels[i][c]
                v2 = pixels[i+1][c]
                if (v1 & 1) != (v2 & 1):
                    flips += 1
                count += 1

        if count>0:
            result.sample_pairs_ratio = flips/count

            if result.sample_pairs_ratio > self.SAMPLE_PAIR_THRESHOLD:
                result.has_lsb_anomaly = True
                result.warnings.append(
                    "High SPA flipped ratio detected"
                )

    def _pairwise_moment_test(self, pixels, result):
        stripped=[]
        for p in pixels[:40000]:
            for c in range(3):
                stripped.append(p[c]>>1)

        diffs=[]
        for i in range(len(stripped)-1):
            diffs.append(abs(stripped[i]-stripped[i+1]))

        if not diffs:
            return

        mean_diff = sum(diffs)/len(diffs)
        result.pairwise_moment_value = mean_diff

        if mean_diff < self.PAIRWISE_THRESHOLD:
            result.has_lsb_anomaly = True
            result.pairwise_suspicious = True
            result.warnings.append(
                "Pairwise moment deviation suspicious — possible LSB matching"
            )

    # ------------------------------------------------------------
    # PAYLOAD ESTIMATION
    # ------------------------------------------------------------
    def _estimate_payload(self, result):
        """
        Combine anomaly indicators into payload estimate.
        Provides approximate size + probability.
        """
        suspicious_signals = 0
        if abs(result.lsb_ratio - 0.5) > self.LSB_RATIO_TOLERANCE: suspicious_signals+=1
        if result.chi_square_suspicious: suspicious_signals+=1
        if result.sample_pairs_ratio > self.SAMPLE_PAIR_THRESHOLD: suspicious_signals+=1
        if result.pairwise_suspicious: suspicious_signals+=1

        result.payload_confidence = suspicious_signals / 4.0

        # crude payload estimate from ratio deviation
        deviation = abs(result.lsb_ratio - 0.5)
        result.estimated_payload = max(deviation * 2, 0.0)

        if result.estimated_payload > self.PAYLOAD_DETECTION_MIN:
            result.warnings.append(
                f"Estimated hidden payload ~{result.estimated_payload*100:.1f}%"
            )
