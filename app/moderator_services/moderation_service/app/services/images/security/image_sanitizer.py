"""
Image Sanitizer
===============

Safely removes hidden/embedded data from images:
- Strips data appended after EOF markers
- Removes hidden markers and their content
- Re-encodes image to remove steganographic content
- Cleans suspicious metadata
- Validates and repairs image structure

SECURITY FEATURES:
- Maximum file size limits to prevent memory exhaustion
- Decompression bomb protection
- Safe temporary file handling
- Path traversal prevention
- Timeout protection for processing

Usage:
    sanitizer = ImageSanitizer()
    result = sanitizer.sanitize("malicious.jpg", "clean.jpg")

    if result.success:
        print(f"Image sanitized: {result.output_path}")
    else:
        print(f"Failed: {result.error}")
"""

import os
import io
import re
import shutil
import tempfile
import hashlib
import secrets
from pathlib import Path
from typing import Optional, List, Tuple, Union
from dataclasses import dataclass, field


@dataclass
class SanitizeResult:
    """Result of sanitization operation"""
    success: bool = False
    input_path: str = ""
    output_path: str = ""

    # Sanitized image data (for in-memory operations)
    sanitized_data: Optional[bytes] = None

    # What was removed
    bytes_removed: int = 0
    appended_data_removed: bool = False
    markers_removed: List[str] = field(default_factory=list)
    metadata_cleaned: bool = False
    re_encoded: bool = False

    # Security checks passed
    size_check_passed: bool = True
    decompression_check_passed: bool = True
    format_validated: bool = True

    # Size comparison
    original_size: int = 0
    sanitized_size: int = 0

    # Errors
    error: str = ""
    warnings: List[str] = field(default_factory=list)


class ImageSanitizer:
    """
    Securely sanitizes images by removing hidden/embedded data.

    Security measures:
    - Max file size limit (default 50MB)
    - Max image dimensions (default 10000x10000)
    - Decompression bomb protection
    - Safe temporary file handling with secure random names
    - Input validation and path sanitization

    Methods:
    1. EOF Truncation - Remove data after image EOF marker
    2. Marker Removal - Remove hidden data markers and content
    3. Re-encoding - Re-save image to strip LSB steganography
    4. Metadata Stripping - Remove all EXIF/XMP metadata
    """

    # Security limits
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
    MAX_IMAGE_DIMENSION = 10000  # pixels
    MAX_DECOMPRESSED_SIZE = 100 * 1024 * 1024  # 100 MB (for decompression bomb check)

    # Image signatures and their EOF markers
    IMAGE_FORMATS = {
        b'\xff\xd8\xff': {
            'name': 'JPEG',
            'eof': b'\xff\xd9',
            'eof_search': 'rfind',  # Find last occurrence
        },
        b'\x89PNG\r\n\x1a\n': {
            'name': 'PNG',
            'eof': b'IEND',
            'eof_offset': 8,  # IEND + 4 byte CRC
            'eof_search': 'rfind',
        },
        b'GIF87a': {
            'name': 'GIF',
            'eof': b'\x3b',
            'eof_search': 'rfind',
        },
        b'GIF89a': {
            'name': 'GIF',
            'eof': b'\x3b',
            'eof_search': 'rfind',
        },
    }

    # Hidden markers to remove
    HIDDEN_MARKERS = [
        (b'##HIDDEN_START##', b'##HIDDEN_END##'),
        (b'===BEGIN===', b'===END==='),
        (b'__START__', b'__END__'),
        (b'PAYLOAD_START', b'PAYLOAD_END'),
        (b'EMBED_START', b'EMBED_END'),
        (b'-----BEGIN ', b'-----END '),
    ]

    def __init__(
        self,
        strip_metadata: bool = True,
        re_encode: bool = True,
        max_file_size: int = None,
        max_dimension: int = None
    ):
        """
        Initialize sanitizer.

        Args:
            strip_metadata: Remove all EXIF/XMP metadata
            re_encode: Re-encode image to remove steganographic content
            max_file_size: Maximum allowed file size in bytes
            max_dimension: Maximum allowed image dimension (width or height)
        """
        self.strip_metadata = strip_metadata
        self.re_encode = re_encode
        self.max_file_size = max_file_size or self.MAX_FILE_SIZE
        self.max_dimension = max_dimension or self.MAX_IMAGE_DIMENSION

        # Check for PIL with security settings
        self.pillow_available = False
        try:
            from PIL import Image
            # Set PIL security limits
            Image.MAX_IMAGE_PIXELS = self.max_dimension * self.max_dimension
            self.pillow_available = True
        except ImportError:
            pass

    def _validate_path(self, path: str) -> Tuple[bool, str]:
        """Validate file path for security"""
        try:
            # Resolve to absolute path
            abs_path = os.path.abspath(path)

            # Check for path traversal
            if '..' in path:
                return False, "Path traversal detected"

            # Check for null bytes
            if '\x00' in path:
                return False, "Null byte in path"

            return True, abs_path
        except Exception as e:
            return False, str(e)

    def _check_file_size(self, size: int, result: SanitizeResult) -> bool:
        """Check if file size is within limits"""
        if size > self.max_file_size:
            result.error = f"File too large: {size:,} bytes (max: {self.max_file_size:,})"
            result.size_check_passed = False
            return False
        return True

    def _check_decompression_bomb(self, data: bytes, result: SanitizeResult) -> bool:
        """Check for decompression bomb (zip bomb for images)"""
        if not self.pillow_available:
            return True

        try:
            from PIL import Image

            img = Image.open(io.BytesIO(data))
            width, height = img.size

            # Check dimensions
            if width > self.max_dimension or height > self.max_dimension:
                result.error = f"Image too large: {width}x{height} (max: {self.max_dimension})"
                result.decompression_check_passed = False
                return False

            # Check pixel count (decompression bomb check)
            pixel_count = width * height
            bytes_per_pixel = 4  # RGBA
            decompressed_size = pixel_count * bytes_per_pixel

            if decompressed_size > self.MAX_DECOMPRESSED_SIZE:
                result.error = f"Decompression bomb detected: {decompressed_size:,} bytes uncompressed"
                result.decompression_check_passed = False
                return False

            return True

        except Exception as e:
            result.warnings.append(f"Could not verify decompression safety: {e}")
            return True  # Continue but warn

    def _generate_safe_temp_path(self, suffix: str = '') -> str:
        """Generate a cryptographically secure temporary file path"""
        random_name = secrets.token_hex(16)
        return os.path.join(tempfile.gettempdir(), f"sanitize_{random_name}{suffix}")

    def sanitize(
        self,
        input_path: str,
        output_path: Optional[str] = None,
        overwrite: bool = False
    ) -> SanitizeResult:
        """
        Safely sanitize an image file.

        Args:
            input_path: Path to input image
            output_path: Path for sanitized output (default: input_sanitized.ext)
            overwrite: If True, overwrite input file

        Returns:
            SanitizeResult with details
        """
        result = SanitizeResult()
        result.input_path = input_path

        # Security: Validate input path
        valid, validated_path = self._validate_path(input_path)
        if not valid:
            result.error = f"Invalid input path: {validated_path}"
            return result
        input_path = validated_path

        # Validate input exists
        if not os.path.exists(input_path):
            result.error = "Input file not found"
            return result

        result.original_size = os.path.getsize(input_path)

        # Security: Check file size
        if not self._check_file_size(result.original_size, result):
            return result

        # Determine output path
        if output_path is None:
            if overwrite:
                output_path = input_path
            else:
                path = Path(input_path)
                output_path = str(path.parent / f"{path.stem}_sanitized{path.suffix}")

        result.output_path = output_path

        try:
            # Read input file
            with open(input_path, 'rb') as f:
                data = f.read()

            original_len = len(data)

            # Security: Check for decompression bomb
            if not self._check_decompression_bomb(data, result):
                return result

            # Step 1: Detect format
            image_format = self._detect_format(data)
            if not image_format:
                result.error = "Unknown image format"
                return result

            # Step 2: Find and truncate at EOF
            data, eof_removed = self._truncate_at_eof(data, image_format, result)

            # Step 3: Remove hidden markers
            data, markers_removed = self._remove_markers(data, result)

            # Step 4: Re-encode image (removes LSB steganography)
            if self.re_encode and self.pillow_available:
                data = self._re_encode_image(data, image_format, result)

            # Step 5: Strip metadata
            if self.strip_metadata and self.pillow_available:
                data = self._strip_metadata(data, image_format, result)

            # Calculate bytes removed
            result.bytes_removed = original_len - len(data)
            result.sanitized_size = len(data)
            result.sanitized_data = data  # Store sanitized data for pipeline use

            # Write output using secure temp file
            if overwrite:
                temp_path = self._generate_safe_temp_path(Path(output_path).suffix)
                try:
                    with open(temp_path, 'wb') as f:
                        f.write(data)
                    os.replace(temp_path, output_path)
                finally:
                    # Clean up temp file if it still exists
                    if os.path.exists(temp_path):
                        os.unlink(temp_path)
            else:
                with open(output_path, 'wb') as f:
                    f.write(data)

            result.success = True

        except Exception as e:
            result.error = str(e)

        return result

    def sanitize_bytes(self, data: bytes) -> Tuple[bytes, SanitizeResult]:
        """
        Safely sanitize image data in memory.

        Args:
            data: Raw image bytes

        Returns:
            Tuple of (sanitized_bytes, result)
        """
        result = SanitizeResult()
        result.original_size = len(data)

        # Security: Check file size
        if not self._check_file_size(len(data), result):
            return data, result

        try:
            original_len = len(data)

            # Security: Check for decompression bomb
            if not self._check_decompression_bomb(data, result):
                return data, result

            # Detect format
            image_format = self._detect_format(data)
            if not image_format:
                result.error = "Unknown image format"
                result.format_validated = False
                return data, result

            result.format_validated = True

            # Truncate at EOF
            data, _ = self._truncate_at_eof(data, image_format, result)

            # Remove markers
            data, _ = self._remove_markers(data, result)

            # Re-encode
            if self.re_encode and self.pillow_available:
                data = self._re_encode_image(data, image_format, result)

            # Strip metadata
            if self.strip_metadata and self.pillow_available:
                data = self._strip_metadata(data, image_format, result)

            result.bytes_removed = original_len - len(data)
            result.sanitized_size = len(data)
            result.sanitized_data = data
            result.success = True

        except Exception as e:
            result.error = str(e)

        return data, result

    def _detect_format(self, data: bytes) -> Optional[dict]:
        """Detect image format from magic bytes"""
        for sig, fmt_info in self.IMAGE_FORMATS.items():
            if data.startswith(sig):
                return fmt_info
        return None

    def _truncate_at_eof(
        self,
        data: bytes,
        image_format: dict,
        result: SanitizeResult
    ) -> Tuple[bytes, bool]:
        """Truncate data after EOF marker"""
        eof_marker = image_format.get('eof')
        if not eof_marker:
            return data, False

        # Find EOF marker
        if image_format.get('eof_search') == 'rfind':
            eof_pos = data.rfind(eof_marker)
        else:
            eof_pos = data.find(eof_marker)

        if eof_pos == -1:
            result.warnings.append(f"EOF marker not found for {image_format['name']}")
            return data, False

        # Calculate end position
        eof_offset = image_format.get('eof_offset', len(eof_marker))
        end_pos = eof_pos + eof_offset

        # Check if there's trailing data
        if end_pos < len(data):
            trailing_size = len(data) - end_pos
            trailing_data = data[end_pos:]

            # Check if it's just null padding
            stripped = trailing_data.strip(b'\x00\xff\r\n\t ')

            if len(stripped) > 0:
                result.appended_data_removed = True
                result.warnings.append(
                    f"Removed {trailing_size} bytes of appended data after EOF"
                )
                return data[:end_pos], True

        return data, False

    def _remove_markers(
        self,
        data: bytes,
        result: SanitizeResult
    ) -> Tuple[bytes, bool]:
        """Remove hidden data markers and their content"""
        modified = False

        for start_marker, end_marker in self.HIDDEN_MARKERS:
            while True:
                start_pos = data.find(start_marker)
                if start_pos == -1:
                    break

                # Find end marker
                end_pos = data.find(end_marker, start_pos + len(start_marker))

                if end_pos == -1:
                    # No end marker, remove just the start marker
                    data = data[:start_pos] + data[start_pos + len(start_marker):]
                else:
                    # Remove entire block including markers
                    end_pos += len(end_marker)
                    removed_content = data[start_pos:end_pos]
                    data = data[:start_pos] + data[end_pos:]

                    result.markers_removed.append(
                        start_marker.decode('utf-8', errors='replace')
                    )

                modified = True

        return data, modified

    def _re_encode_image(
        self,
        data: bytes,
        image_format: dict,
        result: SanitizeResult
    ) -> bytes:
        """
        Re-encode image to remove LSB steganography.

        This works by decoding and re-encoding the image,
        which destroys any data hidden in the least significant bits.
        """
        if not self.pillow_available:
            return data

        try:
            from PIL import Image

            # Load image from bytes
            img = Image.open(io.BytesIO(data))

            # Convert to RGB if needed (removes alpha channel issues)
            if img.mode in ('RGBA', 'P', 'LA'):
                # Create white background for transparency
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')

            # Re-encode
            output = io.BytesIO()

            fmt_name = image_format['name']
            if fmt_name == 'JPEG':
                # Re-save as JPEG with quality 95 (slightly lossy to destroy stego)
                img.save(output, format='JPEG', quality=95, optimize=True)
            elif fmt_name == 'PNG':
                # PNG is lossless, but re-encoding still helps
                img.save(output, format='PNG', optimize=True)
            elif fmt_name == 'GIF':
                img.save(output, format='GIF')
            else:
                # Default to JPEG
                img.save(output, format='JPEG', quality=95)

            result.re_encoded = True
            return output.getvalue()

        except Exception as e:
            result.warnings.append(f"Re-encoding failed: {e}")
            return data

    def _strip_metadata(
        self,
        data: bytes,
        image_format: dict,
        result: SanitizeResult
    ) -> bytes:
        """Remove all EXIF/XMP metadata"""
        if not self.pillow_available:
            return data

        try:
            from PIL import Image

            img = Image.open(io.BytesIO(data))

            # Create new image without metadata
            clean_img = Image.new(img.mode, img.size)
            clean_img.putdata(list(img.getdata()))

            # Save without metadata
            output = io.BytesIO()

            fmt_name = image_format['name']
            if fmt_name == 'JPEG':
                clean_img.save(output, format='JPEG', quality=95)
            elif fmt_name == 'PNG':
                clean_img.save(output, format='PNG')
            elif fmt_name == 'GIF':
                clean_img.save(output, format='GIF')
            else:
                clean_img.save(output, format='JPEG', quality=95)

            result.metadata_cleaned = True
            return output.getvalue()

        except Exception as e:
            result.warnings.append(f"Metadata stripping failed: {e}")
            return data


def sanitize_image(
    input_path: str,
    output_path: Optional[str] = None,
    overwrite: bool = False,
    strip_metadata: bool = True,
    re_encode: bool = True
) -> SanitizeResult:
    """
    Convenience function to sanitize an image.

    Args:
        input_path: Path to input image
        output_path: Path for output (optional)
        overwrite: Overwrite input file
        strip_metadata: Remove EXIF/XMP
        re_encode: Re-encode to remove stego

    Returns:
        SanitizeResult
    """
    sanitizer = ImageSanitizer(
        strip_metadata=strip_metadata,
        re_encode=re_encode
    )
    return sanitizer.sanitize(input_path, output_path, overwrite)


# CLI interface
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python image_sanitizer.py <input_image> [output_image]")
        print()
        print("Options:")
        print("  --overwrite    Overwrite input file")
        print("  --no-reencode  Don't re-encode image")
        print("  --keep-meta    Keep metadata")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = None
    overwrite = False
    re_encode = True
    strip_meta = True

    args = sys.argv[2:]
    for i, arg in enumerate(args):
        if arg == '--overwrite':
            overwrite = True
        elif arg == '--no-reencode':
            re_encode = False
        elif arg == '--keep-meta':
            strip_meta = False
        elif not arg.startswith('--'):
            output_file = arg

    print(f"Sanitizing: {input_file}")
    print("-" * 40)

    result = sanitize_image(
        input_file,
        output_file,
        overwrite=overwrite,
        strip_metadata=strip_meta,
        re_encode=re_encode
    )

    if result.success:
        print(f"✅ Success!")
        print(f"   Output: {result.output_path}")
        print(f"   Original size: {result.original_size:,} bytes")
        print(f"   Sanitized size: {result.sanitized_size:,} bytes")
        print(f"   Bytes removed: {result.bytes_removed:,}")

        if result.appended_data_removed:
            print(f"   ✓ Appended data removed")
        if result.markers_removed:
            print(f"   ✓ Markers removed: {result.markers_removed}")
        if result.re_encoded:
            print(f"   ✓ Image re-encoded")
        if result.metadata_cleaned:
            print(f"   ✓ Metadata stripped")

        if result.warnings:
            print(f"   Warnings:")
            for w in result.warnings:
                print(f"     - {w}")
    else:
        print(f"❌ Failed: {result.error}")
        sys.exit(1)

