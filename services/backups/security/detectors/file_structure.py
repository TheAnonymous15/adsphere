"""
Advanced File Structure Detector
================================

Detects hidden embedded payloads using:

- Invalid/corrupted headers
- Polyglot structure markers
- Trailing bytes after EOF
- Embedded executable signatures
- Archive boundaries injection
- Script injection
- Marker-based stego detection
- High entropy payload detection
- Confidence scoring
"""

import os
import struct
import math
from typing import List, Dict
from dataclasses import dataclass, field


@dataclass
class FileStructureResult:
    is_valid_image: bool = True
    detected_format: str = ""
    suspicious: bool = False
    confidence: float = 0.0

    has_embedded_data: bool = False
    embedded_type: str = ""

    has_trailing_data: bool = False
    trailing_size: int = 0
    trailing_entropy: float = 0.0

    has_hidden_markers: bool = False
    markers_found: List[str] = field(default_factory=list)
    hidden_content: str = ""

    warnings: List[str] = field(default_factory=list)


class FileStructureDetector:

    IMAGE_SIGNATURES = {
        b"\xff\xd8\xff": ("JPEG", 3),
        b"\x89PNG\r\n\x1a\n": ("PNG", 8),
        b"GIF87a": ("GIF87", 6),
        b"GIF89a": ("GIF89", 6),
        b"RIFF": ("WEBP", 4),
        b"BM": ("BMP", 2),
        b"\x00\x00\x01\x00": ("ICO", 4),
        b"II*\x00": ("TIFF-LE", 4),
        b"MM\x00*": ("TIFF-BE", 4),
    }

    DANGEROUS_SIGNATURES = {
        b"MZ": ("Windows PE Executable", 2),
        b"\x7fELF": ("Linux ELF Executable", 4),
        b"PK\x03\x04": ("ZIP Archive", 4),
        b"%PDF": ("PDF Document", 4),
        b"\xca\xfe\xba\xbe": ("Java Class", 4),
        b"\xfe\xed\xfa\xce": ("Mach-O 32-bit", 4),
        b"\xfe\xed\xfa\xcf": ("Mach-O 64-bit", 4),
    }

    SCRIPT_PATTERNS = [
        (b"<script", "JavaScript"),
        (b"<?php", "PHP"),
        (b"<%", "ASP/JSP"),
        (b"#!/", "Shell Script"),
    ]

    HIDDEN_MARKERS = {
        b"##HIDDEN_START##": b"##HIDDEN_END##",
        b"===BEGIN===": b"===END===",
        b"__START__": b"__END__",
        b"PAYLOAD_START": b"PAYLOAD_END",
    }

    JPEG_EOF = b"\xff\xd9"
    PNG_IEND = b"IEND\xae\x42\x60\x82"
    GIF_TRAILER = b"\x3b"

    #-------------------------------------------------------------

    def analyze(self, path: str) -> FileStructureResult:
        result = FileStructureResult()

        if not os.path.exists(path):
            result.is_valid_image = False
            result.warnings.append("file missing")
            return result

        try:
            with open(path, "rb") as f:
                content = f.read()
        except Exception as e:
            result.is_valid_image = False
            result.warnings.append(str(e))
            return result

        size = len(content)

        self._check_magic(content, result)
        self._check_embedded(content, result)
        self._check_script(content, result)

        trailing = self._detect_trailing(content, size, result)

        if trailing:
            entropy = self._entropy(trailing)
            result.trailing_entropy = entropy
            if entropy > 6.5:  # close to crypto/high entropy payload
                result.warnings.append("high entropy trailing region")
                result.has_embedded_data = True
                result.embedded_type = "high entropy payload"

        self._check_markers(content, result)

        # confidence score combined signals
        score = 0
        if result.has_embedded_data:
            score += 0.4
        if result.trailing_size > 0:
            score += 0.2
        if result.trailing_entropy > 6:
            score += 0.2
        if result.has_hidden_markers:
            score += 0.2

        result.confidence = min(score, 1.0)
        result.suspicious = result.confidence > 0.5

        return result

    #-------------------------------------------------------------
    def _check_magic(self, content, result):
        result.is_valid_image = False

        for sig, (fmt, sig_len) in self.IMAGE_SIGNATURES.items():
            if content.startswith(sig):
                result.is_valid_image = True
                result.detected_format = fmt
                return

        result.warnings.append("unknown or invalid image signature")

    #-------------------------------------------------------------
    def _check_embedded(self, content, result):
        search_start = 1024  # skip header

        for sig, (desc, sig_len) in self.DANGEROUS_SIGNATURES.items():
            pos = content.find(sig, search_start)
            if pos == -1:
                continue

            result.has_embedded_data = True
            result.embedded_type = desc
            result.warnings.append(f"{desc} signature found at offset {pos}")

    #-------------------------------------------------------------
    def _check_script(self, content, result):
        content_lower = content.lower()

        for pattern, desc in self.SCRIPT_PATTERNS:
            if pattern.lower() in content_lower:
                result.has_embedded_data = True
                result.embedded_type = f"{desc} code"
                result.warnings.append(f"script injection detected: {desc}")

    #-------------------------------------------------------------
    def _detect_trailing(self, content, size, result):
        eof_pos = -1
        eof_len = 0

        if content.startswith(b"\xff\xd8\xff"):
            eof_pos = content.rfind(self.JPEG_EOF)
            eof_len = 2
        elif content.startswith(b"\x89PNG"):
            eof_pos = content.rfind(self.PNG_IEND)
            eof_len = len(self.PNG_IEND)
        elif content.startswith(b"GIF"):
            eof_pos = content.rfind(self.GIF_TRAILER)
            eof_len = 1

        if eof_pos == -1:
            return None

        start = eof_pos + eof_len
        if start >= size:
            return None

        trailing = content[start:]
        stripped = trailing.strip(b"\x00\xff\r\n\t ")
        if not stripped:
            return None

        result.has_trailing_data = True
        result.trailing_size = len(trailing)

        try:
            preview = stripped[:50].decode("utf-8", errors="replace")
            result.warnings.append(f"trailing data preview: {preview}...")
        except:
            result.warnings.append("trailing binary data")

        return stripped

    #-------------------------------------------------------------
    def _check_markers(self, content, result):
        for start, end in self.HIDDEN_MARKERS.items():
            if start not in content:
                continue

            result.has_hidden_markers = True
            s = content.find(start) + len(start)
            e = content.find(end, s)
            if e > s > 0:
                block = content[s:e]
                try:
                    result.hidden_content = block[:100].decode("utf-8")
                except:
                    result.hidden_content = f"<binary {len(block)} bytes>"

                result.markers_found.append(start.decode(errors="ignore"))
                result.warnings.append(f"marker block: {result.hidden_content[:50]}...")

    #-------------------------------------------------------------
    @staticmethod
    def _entropy(data: bytes) -> float:
        if not data:
            return 0.0

        counts = [0]*256
        for b in data:
            counts[b]+=1

        length = len(data)
        entropy=0.0
        for c in counts:
            if c==0:
                continue
            p=c/length
            entropy-=p*math.log2(p)
        return entropy
