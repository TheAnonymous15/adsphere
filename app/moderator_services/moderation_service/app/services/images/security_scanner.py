"""
Security Scanner
================

Step 1: Scan images for embedded malicious data, steganography, and metadata issues.

Checks for:
- Embedded executables or scripts
- Steganographic hidden data
- Malicious EXIF/metadata
- Polyglot files (valid image + executable)
- Suspicious file structure
"""

import sys
import os
import struct
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Add parent paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent.parent))

try:
    from model_registry import ensure_models
except ImportError:
    def ensure_models(models, verbose=False):
        return True

from .models import SecurityScanResult


class SecurityScanner:
    """
    Scans images for security threats before processing.

    Detects:
    1. Embedded executables (polyglot files)
    2. Steganographic data
    3. Malicious metadata/EXIF
    4. Script injection in metadata
    5. Oversized or malformed headers
    """

    # Known magic bytes for dangerous file types
    DANGEROUS_SIGNATURES = {
        b'MZ': 'Windows Executable (PE)',
        b'\x7fELF': 'Linux Executable (ELF)',
        b'PK\x03\x04': 'ZIP Archive (possible JAR/APK)',
        b'%PDF': 'PDF (can contain scripts)',
        b'<script': 'JavaScript injection',
        b'<?php': 'PHP code injection',
        b'#!/': 'Shell script',
        b'\xca\xfe\xba\xbe': 'Java Class file',
        b'\xfe\xed\xfa\xce': 'Mach-O (macOS executable)',
        b'\xfe\xed\xfa\xcf': 'Mach-O 64-bit',
    }

    # Valid image signatures
    IMAGE_SIGNATURES = {
        b'\xff\xd8\xff': 'JPEG',
        b'\x89PNG\r\n\x1a\n': 'PNG',
        b'GIF87a': 'GIF87',
        b'GIF89a': 'GIF89',
        b'RIFF': 'WEBP',
        b'BM': 'BMP',
        b'\x00\x00\x01\x00': 'ICO',
        b'II*\x00': 'TIFF (little-endian)',
        b'MM\x00*': 'TIFF (big-endian)',
    }

    # Suspicious EXIF tags that could contain scripts
    SUSPICIOUS_EXIF_TAGS = [
        'XPComment', 'UserComment', 'ImageDescription',
        'Copyright', 'Artist', 'Software', 'ProcessingSoftware'
    ]

    # Hidden data markers that attackers might use
    HIDDEN_DATA_MARKERS = [
        b'##HIDDEN_START##',
        b'##HIDDEN_END##',
        b'<!--HIDDEN-->',
        b'[HIDDEN]',
        b'__START__',
        b'__END__',
        b'===BEGIN===',
        b'===END===',
        b'PAYLOAD_START',
        b'PAYLOAD_END',
        b'DATA_INJECT',
        b'SECRET_DATA',
    ]

    # JPEG EOF marker
    JPEG_EOF_MARKER = b'\xff\xd9'

    # PNG EOF marker (IEND chunk)
    PNG_EOF_MARKER = b'IEND'

    # Max sizes for sanity checks
    MAX_METADATA_SIZE = 1024 * 1024  # 1MB
    MAX_COMMENT_LENGTH = 10000

    def __init__(self):
        self.pillow_available = False
        self.exifread_available = False
        self._load_dependencies()

    def _load_dependencies(self):
        """Load optional dependencies"""
        try:
            from PIL import Image
            self.pillow_available = True
        except ImportError:
            pass

        try:
            import exifread
            self.exifread_available = True
        except ImportError:
            pass

    def scan(self, image_path: str) -> SecurityScanResult:
        """
        Perform comprehensive security scan on image.

        Args:
            image_path: Path to image file

        Returns:
            SecurityScanResult with findings
        """
        result = SecurityScanResult()

        if not os.path.exists(image_path):
            result.is_safe = False
            result.warnings.append("File not found")
            return result

        # Get file size
        file_size = os.path.getsize(image_path)

        # Step 1: Check file signature
        signature_result = self._check_file_signature(image_path)
        if not signature_result['is_valid_image']:
            result.is_safe = False
            result.warnings.append(f"Invalid image signature: {signature_result.get('detected_type', 'unknown')}")

        if signature_result.get('has_embedded'):
            result.has_embedded_data = True
            result.embedded_type = signature_result.get('embedded_type')
            result.warnings.append(f"Embedded data detected: {result.embedded_type}")

        # Step 2: Scan for dangerous byte sequences
        dangerous_found = self._scan_for_dangerous_bytes(image_path)
        if dangerous_found:
            result.is_safe = False
            result.malware_detected = True
            result.warnings.extend(dangerous_found)

        # Step 3: Check metadata/EXIF
        exif_result = self._scan_metadata(image_path)
        result.exif_data = exif_result.get('exif', {})
        if exif_result.get('suspicious'):
            result.suspicious_metadata = True
            result.warnings.extend(exif_result.get('warnings', []))

        # Step 4: Check for steganography indicators
        stego_result = self._check_steganography(image_path, file_size)
        if stego_result.get('suspicious'):
            result.has_embedded_data = True
            result.embedded_type = "steganography"
            result.warnings.extend(stego_result.get('warnings', []))

        # Step 5: Check for trailing data after EOF markers
        trailing_result = self._check_trailing_data(image_path)
        if trailing_result.get('has_trailing_data'):
            result.has_embedded_data = True
            result.embedded_type = trailing_result.get('type', 'trailing_data')
            result.is_safe = False
            result.warnings.extend(trailing_result.get('warnings', []))

        # Step 6: Check for hidden data markers
        hidden_result = self._check_hidden_markers(image_path)
        if hidden_result.get('has_hidden_markers'):
            result.has_embedded_data = True
            result.embedded_type = "hidden_markers"
            result.is_safe = False
            result.malware_detected = True
            result.warnings.extend(hidden_result.get('warnings', []))

        # Step 7: Validate image structure
        structure_result = self._validate_image_structure(image_path)
        if not structure_result.get('valid'):
            result.is_safe = False
            result.warnings.extend(structure_result.get('warnings', []))

        # Determine final safety
        if result.malware_detected:
            result.is_safe = False
        elif result.has_embedded_data and result.embedded_type != "steganography":
            result.is_safe = False
        elif len(result.warnings) > 3:
            result.is_safe = False

        return result

    def _check_file_signature(self, image_path: str) -> Dict[str, Any]:
        """Check file magic bytes"""
        result = {
            'is_valid_image': False,
            'detected_type': None,
            'has_embedded': False,
            'embedded_type': None
        }

        try:
            with open(image_path, 'rb') as f:
                header = f.read(32)

                # Check for valid image signature
                for sig, img_type in self.IMAGE_SIGNATURES.items():
                    if header.startswith(sig):
                        result['is_valid_image'] = True
                        result['detected_type'] = img_type
                        break

                # Scan for dangerous signatures (skip first 1KB as image header area)
                f.seek(0)
                content = f.read()
                file_size = len(content)

                # Only check for embedded executables in specific contexts
                # A true polyglot usually has the executable at a specific offset
                for sig, danger_type in self.DANGEROUS_SIGNATURES.items():
                    # Skip very short signatures that could match randomly
                    if len(sig) < 3:
                        continue

                    # Look for signature after the image header area (1KB+)
                    # but only if it's at a position that could be a real embedded file
                    search_start = 1024  # Skip first 1KB
                    pos = content.find(sig, search_start)

                    if pos != -1:
                        # Additional checks to reduce false positives
                        # PE files have specific structure after MZ
                        if sig == b'MZ':
                            # MZ should be at a sector boundary (512 bytes) for real polyglots
                            # and must have valid PE header
                            if pos % 512 == 0 and pos + 0x40 < file_size:
                                try:
                                    pe_offset_bytes = content[pos + 0x3C:pos + 0x40]
                                    if len(pe_offset_bytes) == 4:
                                        pe_offset = struct.unpack('<I', pe_offset_bytes)[0]
                                        # Valid PE offset should be reasonable (not too large)
                                        if pe_offset < 0x1000 and pos + pe_offset + 4 < file_size:
                                            pe_sig = content[pos + pe_offset:pos + pe_offset + 4]
                                            if pe_sig == b'PE\x00\x00':
                                                result['has_embedded'] = True
                                                result['embedded_type'] = danger_type
                                                break
                                except:
                                    pass
                        else:
                            # For other signatures, require them to appear in a suspicious context
                            # (e.g., not just random bytes that match)
                            if sig in [b'<script', b'<?php', b'<%']:
                                result['has_embedded'] = True
                                result['embedded_type'] = danger_type
                                break

        except Exception as e:
            result['error'] = str(e)

        return result

    def _scan_for_dangerous_bytes(self, image_path: str) -> List[str]:
        """Scan for dangerous byte patterns"""
        warnings = []

        try:
            with open(image_path, 'rb') as f:
                content = f.read()

                # Check for script injections - these need more context
                # Short patterns like '<% ' could appear in compressed image data
                dangerous_patterns = {
                    b'<script': 'JavaScript',
                    b'javascript:': 'JavaScript URL',
                    b'vbscript:': 'VBScript URL',
                    b'<?php': 'PHP code',
                    b'eval(': 'JavaScript eval',
                    b'exec(': 'exec call',
                    b'system(': 'system call',
                    b'shell_exec(': 'shell_exec',
                    b'passthru(': 'passthru',
                    b'base64_decode(': 'base64_decode (obfuscation)',
                }

                # Patterns that are too short and could appear randomly in binary data
                # Only flag these if they appear with more context
                short_patterns = {
                    b'<%': 'ASP/JSP',  # Requires closing %> nearby
                }

                for pattern, desc in dangerous_patterns.items():
                    if pattern.lower() in content.lower():
                        warnings.append(f"Dangerous pattern detected: {desc}")

                # For short patterns, check for complete tags
                for pattern, desc in short_patterns.items():
                    pos = content.find(pattern)
                    if pos != -1:
                        # Check if there's a closing tag within 500 bytes
                        end_pos = content.find(b'%>', pos)
                        if end_pos != -1 and end_pos - pos < 500:
                            warnings.append(f"Dangerous pattern detected: {desc}")

                # Check for excessive null bytes (potential padding attack)
                null_count_end = content[-500:].count(b'\x00')
                if null_count_end > 50:
                    warnings.append("Excessive null bytes near end of file")

        except Exception as e:
            warnings.append(f"Error scanning file: {e}")

        return warnings

    def _scan_metadata(self, image_path: str) -> Dict[str, Any]:
        """Scan EXIF and metadata for suspicious content"""
        result = {
            'exif': {},
            'suspicious': False,
            'warnings': []
        }

        # Try exifread first
        if self.exifread_available:
            try:
                import exifread
                with open(image_path, 'rb') as f:
                    tags = exifread.process_file(f, details=False)

                for tag, value in tags.items():
                    tag_str = str(tag)
                    value_str = str(value)

                    # Store clean EXIF
                    result['exif'][tag_str] = value_str[:500]

                    # Check for suspicious content
                    for suspicious_tag in self.SUSPICIOUS_EXIF_TAGS:
                        if suspicious_tag.lower() in tag_str.lower():
                            # Check value for scripts
                            if any(s in value_str.lower() for s in ['<script', 'javascript:', '<?php']):
                                result['suspicious'] = True
                                result['warnings'].append(f"Script in EXIF tag {tag_str}")

                            # Check for excessively long values
                            if len(value_str) > self.MAX_COMMENT_LENGTH:
                                result['suspicious'] = True
                                result['warnings'].append(f"Oversized EXIF tag: {tag_str}")

            except Exception as e:
                result['warnings'].append(f"EXIF read error: {e}")

        # Try Pillow as fallback
        elif self.pillow_available:
            try:
                from PIL import Image
                from PIL.ExifTags import TAGS

                with Image.open(image_path) as img:
                    exif = img._getexif()
                    if exif:
                        for tag_id, value in exif.items():
                            tag = TAGS.get(tag_id, tag_id)
                            result['exif'][str(tag)] = str(value)[:500]

            except Exception as e:
                result['warnings'].append(f"Pillow EXIF error: {e}")

        return result

    def _check_steganography(self, image_path: str, file_size: int) -> Dict[str, Any]:
        """Check for steganography indicators"""
        result = {
            'suspicious': False,
            'warnings': []
        }

        if not self.pillow_available:
            return result

        try:
            from PIL import Image

            with Image.open(image_path) as img:
                width, height = img.size
                expected_size = width * height * 3  # Rough estimate for RGB

                # If file is significantly larger than expected, might have hidden data
                if file_size > expected_size * 1.5:
                    result['suspicious'] = True
                    result['warnings'].append("File size larger than expected for image dimensions")

                # Check for unusual bit patterns in LSB (simplified check)
                if img.mode in ['RGB', 'RGBA']:
                    # Sample a few pixels
                    pixels = list(img.getdata())[:1000]
                    lsb_ones = sum(1 for p in pixels for c in p[:3] if c & 1)
                    lsb_ratio = lsb_ones / (len(pixels) * 3)

                    # Natural images have roughly 50% LSB ones
                    # Steganography often has different patterns
                    if lsb_ratio < 0.3 or lsb_ratio > 0.7:
                        result['warnings'].append("Unusual LSB distribution (possible steganography)")

        except Exception as e:
            result['warnings'].append(f"Steganography check error: {e}")

        return result

    def _validate_image_structure(self, image_path: str) -> Dict[str, Any]:
        """Validate image can be properly parsed"""
        result = {
            'valid': True,
            'warnings': []
        }

        if not self.pillow_available:
            return result

        try:
            from PIL import Image

            with Image.open(image_path) as img:
                # Try to load the image data
                img.load()

                # Check for reasonable dimensions
                width, height = img.size
                if width > 10000 or height > 10000:
                    result['warnings'].append(f"Extremely large dimensions: {width}x{height}")

                if width < 10 or height < 10:
                    result['warnings'].append(f"Suspiciously small dimensions: {width}x{height}")

                # Verify format
                if img.format not in ['JPEG', 'PNG', 'GIF', 'WEBP', 'BMP', 'TIFF']:
                    result['warnings'].append(f"Unusual image format: {img.format}")

        except Exception as e:
            result['valid'] = False
            result['warnings'].append(f"Image validation failed: {e}")

        return result

    def _check_trailing_data(self, image_path: str) -> Dict[str, Any]:
        """
        Check for data appended after the image EOF marker.

        Attackers often append malicious data after JPEG's FF D9 or PNG's IEND chunk.
        """
        result = {
            'has_trailing_data': False,
            'type': None,
            'trailing_size': 0,
            'warnings': []
        }

        try:
            with open(image_path, 'rb') as f:
                content = f.read()
                file_size = len(content)

                # Check if it's a JPEG (starts with FF D8 FF)
                if content[:3] == b'\xff\xd8\xff':
                    # Find the last occurrence of JPEG EOF marker (FF D9)
                    eof_pos = content.rfind(self.JPEG_EOF_MARKER)

                    if eof_pos != -1:
                        # Check if there's data after EOF
                        trailing_start = eof_pos + 2  # After FF D9
                        if trailing_start < file_size:
                            trailing_data = content[trailing_start:]
                            trailing_size = len(trailing_data)

                            # Ignore small padding (< 10 bytes of nulls or whitespace)
                            stripped = trailing_data.strip(b'\x00\xff\r\n\t ')
                            if len(stripped) > 0:
                                result['has_trailing_data'] = True
                                result['type'] = 'jpeg_trailing_data'
                                result['trailing_size'] = trailing_size

                                # Try to decode as text for preview
                                try:
                                    preview = stripped[:100].decode('utf-8', errors='replace')
                                    result['warnings'].append(
                                        f"Data found after JPEG EOF marker ({trailing_size} bytes): \"{preview[:50]}...\""
                                    )
                                except:
                                    result['warnings'].append(
                                        f"Binary data found after JPEG EOF marker ({trailing_size} bytes)"
                                    )

                # Check if it's a PNG (starts with 89 50 4E 47)
                elif content[:4] == b'\x89PNG':
                    # Find IEND chunk (49 45 4E 44 AE 42 60 82)
                    iend_marker = b'IEND\xae\x42\x60\x82'
                    eof_pos = content.rfind(iend_marker)

                    if eof_pos != -1:
                        trailing_start = eof_pos + len(iend_marker)
                        if trailing_start < file_size:
                            trailing_data = content[trailing_start:]
                            trailing_size = len(trailing_data)

                            stripped = trailing_data.strip(b'\x00\xff\r\n\t ')
                            if len(stripped) > 0:
                                result['has_trailing_data'] = True
                                result['type'] = 'png_trailing_data'
                                result['trailing_size'] = trailing_size
                                result['warnings'].append(
                                    f"Data found after PNG IEND chunk ({trailing_size} bytes)"
                                )

        except Exception as e:
            result['warnings'].append(f"Trailing data check error: {e}")

        return result

    def _check_hidden_markers(self, image_path: str) -> Dict[str, Any]:
        """
        Check for known hidden data markers that attackers use.

        Detects custom markers like ##HIDDEN_START##, __START__, etc.
        """
        result = {
            'has_hidden_markers': False,
            'markers_found': [],
            'warnings': []
        }

        try:
            with open(image_path, 'rb') as f:
                content = f.read()

                # Check for each hidden marker pattern
                for marker in self.HIDDEN_DATA_MARKERS:
                    if marker in content:
                        result['has_hidden_markers'] = True
                        try:
                            marker_str = marker.decode('utf-8', errors='replace')
                        except:
                            marker_str = str(marker)
                        result['markers_found'].append(marker_str)

                if result['has_hidden_markers']:
                    result['warnings'].append(
                        f"Hidden data markers detected: {', '.join(result['markers_found'])}"
                    )

                    # Try to extract the hidden content between markers
                    for start_marker in [b'##HIDDEN_START##', b'===BEGIN===', b'__START__']:
                        if start_marker in content:
                            start_pos = content.find(start_marker) + len(start_marker)
                            # Find corresponding end marker
                            end_markers = {
                                b'##HIDDEN_START##': b'##HIDDEN_END##',
                                b'===BEGIN===': b'===END===',
                                b'__START__': b'__END__'
                            }
                            end_marker = end_markers.get(start_marker)
                            if end_marker and end_marker in content:
                                end_pos = content.find(end_marker)
                                if end_pos > start_pos:
                                    hidden_content = content[start_pos:end_pos]
                                    try:
                                        preview = hidden_content[:100].decode('utf-8', errors='replace')
                                        result['warnings'].append(
                                            f"Hidden content extracted: \"{preview}...\""
                                        )
                                    except:
                                        result['warnings'].append(
                                            f"Hidden binary content found ({len(hidden_content)} bytes)"
                                        )
                                    break

        except Exception as e:
            result['warnings'].append(f"Hidden marker check error: {e}")

        return result

    def compute_hash(self, image_path: str) -> Dict[str, str]:
        """Compute file hashes for fingerprinting"""
        hashes = {}

        try:
            with open(image_path, 'rb') as f:
                content = f.read()
                hashes['md5'] = hashlib.md5(content).hexdigest()
                hashes['sha256'] = hashlib.sha256(content).hexdigest()

            # Perceptual hash if available
            if self.pillow_available:
                try:
                    import imagehash
                    from PIL import Image
                    with Image.open(image_path) as img:
                        hashes['phash'] = str(imagehash.phash(img))
                        hashes['dhash'] = str(imagehash.dhash(img))
                except ImportError:
                    pass
                except Exception:
                    pass

        except Exception as e:
            hashes['error'] = str(e)

        return hashes

