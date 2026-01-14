"""
Entropy Detector
================

Detects anomalies using entropy analysis:
- High entropy regions (encrypted/compressed data)
- Low entropy regions (padding attacks)
- Entropy distribution anomalies
"""

import os
import math
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass, field
from collections import Counter


@dataclass
class EntropyResult:
    """Result from entropy analysis"""
    overall_entropy: float = 0.0
    is_anomalous: bool = False
    high_entropy_regions: List[Dict[str, Any]] = field(default_factory=list)
    low_entropy_regions: List[Dict[str, Any]] = field(default_factory=list)
    entropy_distribution: List[float] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class EntropyDetector:
    """
    Analyzes file entropy to detect hidden data.

    Encrypted or compressed hidden data typically has
    higher entropy than natural image data.

    Detection methods:
    1. Overall file entropy
    2. Sliding window entropy analysis
    3. Entropy spike detection
    4. Trailing region entropy
    """

    # Entropy thresholds
    HIGH_ENTROPY_THRESHOLD = 7.5  # Max is 8.0 for random data
    LOW_ENTROPY_THRESHOLD = 1.0   # Suspicious if too uniform
    ANOMALY_SPIKE_THRESHOLD = 1.5  # Difference from average

    # Expected entropy ranges by format
    EXPECTED_ENTROPY = {
        'JPEG': (7.0, 7.9),    # JPEG is compressed, high entropy
        'PNG': (5.0, 7.8),     # PNG varies more
        'GIF': (4.0, 7.5),     # GIF can have lower entropy
        'BMP': (3.0, 7.0),     # BMP uncompressed, varies widely
        'WEBP': (6.5, 7.9),    # WEBP compressed
    }

    def __init__(self, window_size: int = 1024, step_size: int = 512):
        """
        Initialize entropy detector.

        Args:
            window_size: Size of sliding window for local entropy
            step_size: Step size for sliding window
        """
        self.window_size = window_size
        self.step_size = step_size

    def analyze(self, image_path: str, image_format: str = None) -> EntropyResult:
        """
        Perform entropy analysis on image file.

        Args:
            image_path: Path to image file
            image_format: Optional format hint (JPEG, PNG, etc.)

        Returns:
            EntropyResult with findings
        """
        result = EntropyResult()

        if not os.path.exists(image_path):
            result.warnings.append("File not found")
            return result

        try:
            with open(image_path, 'rb') as f:
                content = f.read()
        except Exception as e:
            result.warnings.append(f"Failed to read file: {e}")
            return result

        if len(content) < 100:
            result.warnings.append("File too small for entropy analysis")
            return result

        # Calculate overall entropy
        result.overall_entropy = self._calculate_entropy(content)

        # Detect format if not provided
        if not image_format:
            image_format = self._detect_format(content)

        # Check if overall entropy is anomalous
        self._check_overall_entropy(result, image_format)

        # Sliding window analysis
        self._analyze_entropy_distribution(content, result)

        # Check for entropy spikes
        self._detect_entropy_spikes(result)

        # Analyze trailing region
        self._analyze_trailing_entropy(content, result)

        return result

    def _calculate_entropy(self, data: bytes) -> float:
        """Calculate Shannon entropy of data"""
        if not data:
            return 0.0

        # Count byte frequencies
        freq = Counter(data)
        length = len(data)

        # Calculate entropy
        entropy = 0.0
        for count in freq.values():
            if count > 0:
                p = count / length
                entropy -= p * math.log2(p)

        return entropy

    def _detect_format(self, content: bytes) -> str:
        """Detect image format from magic bytes"""
        if content[:3] == b'\xff\xd8\xff':
            return 'JPEG'
        elif content[:4] == b'\x89PNG':
            return 'PNG'
        elif content[:6] in [b'GIF87a', b'GIF89a']:
            return 'GIF'
        elif content[:2] == b'BM':
            return 'BMP'
        elif content[:4] == b'RIFF' and len(content) >= 12 and content[8:12] == b'WEBP':
            return 'WEBP'
        return 'UNKNOWN'

    def _check_overall_entropy(self, result: EntropyResult, image_format: str):
        """Check if overall entropy is within expected range"""
        expected = self.EXPECTED_ENTROPY.get(image_format, (3.0, 7.9))

        if result.overall_entropy > self.HIGH_ENTROPY_THRESHOLD:
            result.is_anomalous = True
            result.warnings.append(
                f"Very high entropy ({result.overall_entropy:.2f}), "
                "possible encrypted hidden data"
            )
        elif result.overall_entropy < expected[0]:
            result.warnings.append(
                f"Entropy ({result.overall_entropy:.2f}) below expected "
                f"for {image_format} ({expected[0]:.1f}-{expected[1]:.1f})"
            )

    def _analyze_entropy_distribution(self, content: bytes, result: EntropyResult):
        """Analyze entropy across file using sliding window"""
        file_size = len(content)

        if file_size < self.window_size:
            return

        entropies = []
        positions = []

        for pos in range(0, file_size - self.window_size, self.step_size):
            window = content[pos:pos + self.window_size]
            entropy = self._calculate_entropy(window)
            entropies.append(entropy)
            positions.append(pos)

        result.entropy_distribution = entropies

        if not entropies:
            return

        avg_entropy = sum(entropies) / len(entropies)

        # Find high entropy regions
        for i, (entropy, pos) in enumerate(zip(entropies, positions)):
            if entropy > self.HIGH_ENTROPY_THRESHOLD:
                result.high_entropy_regions.append({
                    'offset': pos,
                    'entropy': entropy,
                    'size': self.window_size
                })
            elif entropy < self.LOW_ENTROPY_THRESHOLD:
                result.low_entropy_regions.append({
                    'offset': pos,
                    'entropy': entropy,
                    'size': self.window_size
                })

    def _detect_entropy_spikes(self, result: EntropyResult):
        """Detect sudden changes in entropy (possible hidden data boundaries)"""
        if len(result.entropy_distribution) < 3:
            return

        avg = sum(result.entropy_distribution) / len(result.entropy_distribution)

        spikes = []
        for i in range(1, len(result.entropy_distribution) - 1):
            prev_e = result.entropy_distribution[i - 1]
            curr_e = result.entropy_distribution[i]
            next_e = result.entropy_distribution[i + 1]

            # Check for sudden spike
            if abs(curr_e - prev_e) > self.ANOMALY_SPIKE_THRESHOLD:
                spikes.append({
                    'index': i,
                    'offset': i * self.step_size,
                    'change': curr_e - prev_e
                })

        if len(spikes) > 3:
            result.is_anomalous = True
            result.warnings.append(
                f"Multiple entropy spikes detected ({len(spikes)}), "
                "possible hidden data boundaries"
            )

    def _analyze_trailing_entropy(self, content: bytes, result: EntropyResult):
        """Analyze entropy of data after expected EOF"""
        file_size = len(content)

        # Find EOF marker position
        eof_pos = -1

        if content[:3] == b'\xff\xd8\xff':  # JPEG
            eof_pos = content.rfind(b'\xff\xd9')
            if eof_pos != -1:
                eof_pos += 2
        elif content[:4] == b'\x89PNG':  # PNG
            iend = content.rfind(b'IEND')
            if iend != -1:
                eof_pos = iend + 8  # IEND + CRC

        if eof_pos == -1 or eof_pos >= file_size - 100:
            return

        trailing = content[eof_pos:]
        if len(trailing) < 50:
            return

        trailing_entropy = self._calculate_entropy(trailing)

        # High entropy in trailing data is suspicious
        if trailing_entropy > 7.0:
            result.is_anomalous = True
            result.warnings.append(
                f"High entropy ({trailing_entropy:.2f}) in trailing data "
                f"({len(trailing)} bytes after EOF)"
            )
        elif trailing_entropy > 5.0:
            result.warnings.append(
                f"Moderate entropy ({trailing_entropy:.2f}) in trailing data"
            )

