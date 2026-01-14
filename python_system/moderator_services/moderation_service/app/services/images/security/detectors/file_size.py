"""
File Size + Compression Ratio Detector
--------------------------------------
Detects:
 - Abnormally large file sizes
 - Suspicious file size per megapixel (under-compressed or embedding)

Safe to integrate into your moderation pipeline.
"""

import os
from PIL import Image


class FileSizeDetector:
    def __init__(
        self,
        warn_threshold_mb=20,      # anomaly
        block_threshold_mb=50,     # extreme anomaly
        max_mb_per_megapixel=3.0   # compression ratio threshold
    ):
        self.warn_threshold = warn_threshold_mb * 1024 * 1024
        self.block_threshold = block_threshold_mb * 1024 * 1024
        self.max_ratio = max_mb_per_megapixel

    def analyze(self, image_path, result):
        """
        result must have fields:
          - warnings []
          - recommendations []
          - file_size (optional)
          - steganography_detected (bool)
          - malware_detected (bool)
          - is_safe (bool)
        """
        file_size = os.path.getsize(image_path)
        result.file_size = file_size

        # --- absolute file size anomaly ------------
        if file_size > self.block_threshold:
            result.is_safe = False
            result.malware_detected = True
            result.warnings.append(
                f"File size extremely large ({file_size/1024/1024:.2f}MB)"
            )
            result.recommendations.append(
                "BLOCK: suspiciously large file, likely embedded payload"
            )
            return result  # stop analysis, critical alert

        if file_size > self.warn_threshold:
            result.steganography_detected = True
            result.warnings.append(
                f"File size abnormal ({file_size/1024/1024:.2f}MB)"
            )
            result.recommendations.append(
                "Investigate: possible appended payload"
            )

        # --- compression ratio analysis ------------
        try:
            with Image.open(image_path) as img:
                width, height = img.size
                megapixels = (width * height) / 1_000_000
                if megapixels == 0:
                    return result

                ratio = (file_size / 1024 / 1024) / megapixels

                if ratio > self.max_ratio:
                    result.steganography_detected = True
                    result.warnings.append(
                        f"Suspicious size per megapixel: {ratio:.2f}MB/MP"
                    )
                    result.recommendations.append(
                        "Image appears under-compressed or padded"
                    )

        except Exception:
            # ignore: the main size check already happened
            pass

        return result
