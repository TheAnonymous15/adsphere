"""
Advanced Metadata Detector
==========================

Detects malicious metadata:
- EXIF/XMP/IPTC threats
- Script & encoded payloads
- Oversized/hidden metadata blocks
- High entropy embedded data
- Trailing hidden metadata past EOF
"""

import os
import re
import math
from typing import Dict, List
from dataclasses import dataclass, field


# ------------ Utility helpers --------------

def calculate_entropy(data: bytes) -> float:
    """Shannon entropy"""
    if not data:
        return 0.0
    freq = {b: data.count(b) for b in set(data)}
    length = len(data)
    entropy = -sum((count / length) * math.log2(count / length)
                   for count in freq.values())
    return entropy


@dataclass
class MetadataResult:
    has_metadata: bool = False
    suspicious: bool = False

    # detected issues
    has_script: bool = False
    oversized_metadata: bool = False
    suspicious_urls: bool = False
    suspicious_entropy: bool = False
    suspicious_trailing: bool = False

    # extracted metadata
    exif: Dict[str, str] = field(default_factory=dict)
    xmp: Dict[str, str] = field(default_factory=dict)

    warnings: List[str] = field(default_factory=list)
    suspicious_fields: List[str] = field(default_factory=list)


class MetadataDetector:

    # --- Tunables ---
    MAX_FIELD_SIZE = 8000
    MAX_META_TOTAL = 1_000_000
    EXCESS_ENTROPY_THRESHOLD = 7.3  # near random
    TRAILING_SCAN_SIZE = 4096

    SCRIPT_PATTERNS = [
        r"<script",
        r"javascript:",
        r"eval\s*\(",
        r"system\s*\(",
        r"base64,",
        r"on\w+=",
    ]

    MALICIOUS_URL_PATTERNS = [
        r"https?://[^\"\'<>]+\.exe",
        r"https?://[^\"\'<>]+\.dll",
        r"file://",
    ]

    def __init__(self):
        self._load_optional_libs()

    def _load_optional_libs(self):
        try:
            from PIL import Image
            from PIL.ExifTags import TAGS
            self.pillow = True
        except ImportError:
            self.pillow = False

        try:
            import exifread
            self.exifread = True
        except ImportError:
            self.exifread = False

    # ------------------ PUBLIC --------------------

    def analyze(self, path: str) -> MetadataResult:
        result = MetadataResult()

        if not os.path.exists(path):
            result.warnings.append("File not found")
            return result

        self._extract_exif(path, result)
        self._extract_xmp(path, result)
        self._scan_icc(path, result)
        self._detect_trailing_hidden(path, result)

        self._postprocess(result)

        return result

    # ----------------- EXIF -----------------------

    def _extract_exif(self, path, result):
        if self.exifread:
            try:
                import exifread
                with open(path, "rb") as f:
                    tags = exifread.process_file(f, details=False)

                for tag, value in tags.items():
                    value = str(value)
                    self._inspect_field("EXIF:" + tag, value, result)

                result.exif = {k: v[:200] for k, v in tags.items()}

            except Exception as e:
                result.warnings.append(f"EXIF error: {e}")

    # ------------------ XMP -----------------------

    def _extract_xmp(self, path, result):
        try:
            with open(path, "rb") as f:
                b = f.read()

            start = b.find(b"<x:xmpmeta")
            if start != -1:
                end = b.find(b"</x:xmpmeta>", start)
                if end != -1:
                    block = b[start:end+12]

                    if len(block) > self.MAX_META_TOTAL:
                        result.oversized_metadata = True
                        result.warnings.append("Oversized XMP block")

                    decoded = block.decode("utf-8", errors="ignore")
                    result.xmp["raw"] = decoded[:500]
                    self._inspect_field("XMP", decoded, result)

        except Exception as e:
            result.warnings.append(f"XMP error: {e}")

    # ------------------ ICC -----------------------

    def _scan_icc(self, path, result):
        if not self.pillow:
            return
        try:
            from PIL import Image
            with Image.open(path) as img:
                icc = img.info.get("icc_profile")
                if icc:
                    if len(icc) > 100_000:
                        result.oversized_metadata = True
                        result.warnings.append("Large ICC profile detected")

                    entropy = calculate_entropy(icc)
                    if entropy > self.EXCESS_ENTROPY_THRESHOLD:
                        result.suspicious_entropy = True
                        result.warnings.append("High entropy ICC profile")

        except Exception:
            pass

    # ---- detect vector: appended extra hidden data ----

    def _detect_trailing_hidden(self, path, result):
        with open(path, "rb") as f:
            f.seek(-self.TRAILING_SCAN_SIZE, os.SEEK_END)
            tail = f.read()

        if not tail:
            return

        entropy = calculate_entropy(tail)
        if entropy > self.EXCESS_ENTROPY_THRESHOLD:
            result.suspicious_entropy = True
            result.suspicious_trailing = True
            result.warnings.append("High entropy trailing bytes block detected")

        # detect printable suspicious text fragments
        if re.search(rb"(secret|payload|key)", tail, re.IGNORECASE):
            result.suspicious_trailing = True
            result.warnings.append("Suspicious keywords in trailing bytes")

    # ----------------- Inspect fields ----------------------

    def _inspect_field(self, name, content, result):

        if len(content) > self.MAX_FIELD_SIZE:
            result.oversized_metadata = True
            result.suspicious_fields.append(name)

        c = content.lower()

        for p in self.SCRIPT_PATTERNS:
            if re.search(p, c):
                result.has_script = True
                result.suspicious_fields.append(name)
                result.warnings.append(f"Script marker in {name}")

        for p in self.MALICIOUS_URL_PATTERNS:
            if re.search(p, c):
                result.suspicious_urls = True
                result.warnings.append(f"Suspicious URL in {name}")

    # -------------- final flagging ----------------

    def _postprocess(self, result):
        result.has_metadata = bool(result.exif or result.xmp)
        result.suspicious = any([
            result.has_script,
            result.oversized_metadata,
            result.suspicious_urls,
            result.suspicious_entropy,
            result.suspicious_trailing,
        ])
