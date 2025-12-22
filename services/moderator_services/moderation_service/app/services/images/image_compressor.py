"""
Image Compressor
================

Compresses images to WebP format with target size ≤ 1MB.
Integrates with the security pipeline:

    Scanner → Sanitizer → Compressor → OCR

Features:
- Converts to WebP (best compression/quality ratio)
- Iteratively reduces quality until size ≤ 1MB
- Preserves aspect ratio
- Optional resizing for very large images
- Secure processing with size limits

Usage:
    from image_compressor import ImageCompressor, compress_image

    # Simple compression
    result = compress_image(image_data)

    # Full pipeline
    compressor = ImageCompressor()
    result = compressor.compress(image_data)

    if result.success:
        compressed_data = result.compressed_data  # WebP < 1MB
"""

import io
import os
import tempfile
import secrets
from pathlib import Path
from typing import Optional, Tuple, Callable, Any, Union
from dataclasses import dataclass, field


@dataclass
class CompressionResult:
    """Result of image compression"""
    success: bool = False

    # Compressed image data
    compressed_data: Optional[bytes] = None
    output_format: str = "webp"

    # Size information
    original_size: int = 0
    compressed_size: int = 0
    compression_ratio: float = 0.0

    # Quality used
    final_quality: int = 0

    # Dimensions
    original_dimensions: Tuple[int, int] = (0, 0)
    final_dimensions: Tuple[int, int] = (0, 0)
    was_resized: bool = False

    # Processing info
    iterations: int = 0
    processing_time_ms: float = 0.0

    # Errors
    error: str = ""
    warnings: list = field(default_factory=list)


class ImageCompressor:
    """
    Compresses images to WebP format with size limit.

    Pipeline integration:
    - Receives sanitized image from ImageSanitizer
    - Compresses to WebP ≤ 1MB
    - Forwards to OCR processor

    Compression strategy:
    1. Start with high quality (95)
    2. Iteratively reduce quality until size ≤ target
    3. If still too large, resize image
    4. Minimum quality floor (10) to preserve usability
    """

    # Compression settings
    DEFAULT_TARGET_SIZE = 1 * 1024 * 1024  # 1 MB
    DEFAULT_START_QUALITY = 95
    DEFAULT_MIN_QUALITY = 10
    DEFAULT_QUALITY_STEP = 5

    # Size limits
    MAX_INPUT_SIZE = 50 * 1024 * 1024  # 50 MB
    MAX_DIMENSION = 10000  # pixels

    # Resize settings (if compression alone isn't enough)
    RESIZE_THRESHOLD_QUALITY = 30  # Start resizing if quality drops below this
    RESIZE_FACTOR = 0.8  # Reduce dimensions by 20% each resize iteration
    MIN_DIMENSION = 100  # Don't resize below this

    def __init__(
        self,
        target_size: int = None,
        start_quality: int = None,
        min_quality: int = None,
        quality_step: int = None,
        output_format: str = "webp"
    ):
        """
        Initialize compressor.

        Args:
            target_size: Target file size in bytes (default: 1MB)
            start_quality: Starting quality (1-100, default: 95)
            min_quality: Minimum quality floor (default: 10)
            quality_step: Quality reduction per iteration (default: 5)
            output_format: Output format (default: webp)
        """
        self.target_size = target_size or self.DEFAULT_TARGET_SIZE
        self.start_quality = start_quality or self.DEFAULT_START_QUALITY
        self.min_quality = min_quality or self.DEFAULT_MIN_QUALITY
        self.quality_step = quality_step or self.DEFAULT_QUALITY_STEP
        self.output_format = output_format.lower()

        # Check for PIL
        self.pillow_available = False
        try:
            from PIL import Image
            Image.MAX_IMAGE_PIXELS = self.MAX_DIMENSION * self.MAX_DIMENSION
            self.pillow_available = True
        except ImportError:
            pass

    def compress(
        self,
        image_data: bytes,
        target_size: int = None,
        preserve_format: bool = False
    ) -> CompressionResult:
        """
        Compress image data to target size.

        Args:
            image_data: Raw image bytes
            target_size: Override target size (bytes)
            preserve_format: Keep original format instead of converting to WebP

        Returns:
            CompressionResult with compressed data
        """
        import time
        start_time = time.time()

        result = CompressionResult()
        result.original_size = len(image_data)

        target = target_size or self.target_size

        # Check if compression is needed
        if result.original_size <= target:
            result.success = True
            result.compressed_data = image_data
            result.compressed_size = result.original_size
            result.compression_ratio = 1.0
            result.final_quality = 100
            result.warnings.append("Image already under target size, no compression needed")
            return result

        # Validate input size
        if result.original_size > self.MAX_INPUT_SIZE:
            result.error = f"Image too large: {result.original_size:,} bytes (max: {self.MAX_INPUT_SIZE:,})"
            return result

        if not self.pillow_available:
            result.error = "PIL/Pillow not available for compression"
            return result

        try:
            from PIL import Image

            # Load image
            img = Image.open(io.BytesIO(image_data))
            result.original_dimensions = img.size

            # Validate dimensions
            if img.width > self.MAX_DIMENSION or img.height > self.MAX_DIMENSION:
                result.error = f"Image dimensions too large: {img.width}x{img.height}"
                return result

            # Convert to RGB if needed (WebP doesn't support all modes)
            if img.mode in ('RGBA', 'LA', 'P'):
                # Preserve transparency for WebP
                if img.mode == 'P':
                    img = img.convert('RGBA')
            elif img.mode not in ('RGB', 'RGBA'):
                img = img.convert('RGB')

            # Determine output format
            out_format = self.output_format if not preserve_format else self._detect_format(image_data)
            result.output_format = out_format

            # Iteratively compress
            quality = self.start_quality
            iterations = 0
            current_img = img.copy()

            while True:
                iterations += 1

                # Compress at current quality
                output = io.BytesIO()

                if out_format == 'webp':
                    current_img.save(output, format='WEBP', quality=quality, method=4)
                elif out_format == 'jpeg':
                    # Convert to RGB for JPEG (no alpha)
                    if current_img.mode == 'RGBA':
                        rgb_img = Image.new('RGB', current_img.size, (255, 255, 255))
                        rgb_img.paste(current_img, mask=current_img.split()[3])
                        rgb_img.save(output, format='JPEG', quality=quality, optimize=True)
                    else:
                        current_img.save(output, format='JPEG', quality=quality, optimize=True)
                elif out_format == 'png':
                    current_img.save(output, format='PNG', optimize=True)
                else:
                    current_img.save(output, format='WEBP', quality=quality)

                compressed_size = output.tell()

                # Check if we're under target
                if compressed_size <= target:
                    result.success = True
                    result.compressed_data = output.getvalue()
                    result.compressed_size = compressed_size
                    result.final_quality = quality
                    result.iterations = iterations
                    result.final_dimensions = current_img.size
                    break

                # Reduce quality
                quality -= self.quality_step

                # If quality is too low, try resizing
                if quality < self.RESIZE_THRESHOLD_QUALITY:
                    new_width = int(current_img.width * self.RESIZE_FACTOR)
                    new_height = int(current_img.height * self.RESIZE_FACTOR)

                    # Check minimum dimensions
                    if new_width < self.MIN_DIMENSION or new_height < self.MIN_DIMENSION:
                        # Can't resize further, use best effort
                        result.success = True
                        result.compressed_data = output.getvalue()
                        result.compressed_size = compressed_size
                        result.final_quality = quality + self.quality_step
                        result.iterations = iterations
                        result.final_dimensions = current_img.size
                        result.warnings.append(
                            f"Could not reach target size. Final: {compressed_size:,} bytes"
                        )
                        break

                    # Resize image
                    current_img = current_img.resize(
                        (new_width, new_height),
                        Image.Resampling.LANCZOS
                    )
                    result.was_resized = True
                    quality = self.start_quality  # Reset quality after resize

                # Absolute minimum quality
                if quality < self.min_quality:
                    quality = self.min_quality

                    # Final attempt at minimum quality
                    output = io.BytesIO()
                    if out_format == 'webp':
                        current_img.save(output, format='WEBP', quality=quality, method=6)
                    else:
                        current_img.save(output, format='WEBP', quality=quality)

                    result.success = True
                    result.compressed_data = output.getvalue()
                    result.compressed_size = output.tell()
                    result.final_quality = quality
                    result.iterations = iterations
                    result.final_dimensions = current_img.size

                    if result.compressed_size > target:
                        result.warnings.append(
                            f"Minimum quality reached. Final: {result.compressed_size:,} bytes"
                        )
                    break

                # Safety limit on iterations
                if iterations > 50:
                    result.error = "Max iterations exceeded"
                    break

            # Calculate compression ratio
            if result.compressed_size > 0:
                result.compression_ratio = result.original_size / result.compressed_size

            result.processing_time_ms = (time.time() - start_time) * 1000

        except Exception as e:
            result.error = str(e)

        return result

    def compress_file(
        self,
        input_path: str,
        output_path: Optional[str] = None,
        target_size: int = None
    ) -> CompressionResult:
        """
        Compress an image file.

        Args:
            input_path: Path to input image
            output_path: Path for output (default: input_compressed.webp)
            target_size: Override target size

        Returns:
            CompressionResult
        """
        result = CompressionResult()

        if not os.path.exists(input_path):
            result.error = "Input file not found"
            return result

        try:
            with open(input_path, 'rb') as f:
                image_data = f.read()

            result = self.compress(image_data, target_size)

            if result.success and result.compressed_data:
                # Determine output path
                if output_path is None:
                    path = Path(input_path)
                    output_path = str(path.parent / f"{path.stem}_compressed.{self.output_format}")

                with open(output_path, 'wb') as f:
                    f.write(result.compressed_data)

        except Exception as e:
            result.error = str(e)

        return result

    def compress_and_process(
        self,
        image_data: bytes,
        processor_callback: Optional[Callable[[bytes], Any]] = None,
        target_size: int = None
    ) -> Tuple[CompressionResult, Any]:
        """
        Compress image and pass to processor (e.g., OCR).

        Args:
            image_data: Raw image bytes (should be sanitized first!)
            processor_callback: Function to process compressed image
            target_size: Override target size

        Returns:
            Tuple of (CompressionResult, processor result)
        """
        # Compress
        result = self.compress(image_data, target_size)

        processor_result = None

        if result.success and result.compressed_data and processor_callback:
            try:
                processor_result = processor_callback(result.compressed_data)
            except Exception as e:
                result.warnings.append(f"Processor failed: {e}")

        return result, processor_result

    def _detect_format(self, data: bytes) -> str:
        """Detect image format from magic bytes"""
        if data.startswith(b'\xff\xd8\xff'):
            return 'jpeg'
        elif data.startswith(b'\x89PNG'):
            return 'png'
        elif data.startswith(b'GIF'):
            return 'gif'
        elif data.startswith(b'RIFF') and b'WEBP' in data[:12]:
            return 'webp'
        return 'webp'  # Default to webp


# Convenience functions

def compress_image(
    image_data: bytes,
    target_size: int = 1024 * 1024,
    output_format: str = "webp"
) -> CompressionResult:
    """
    Quick function to compress an image.

    Args:
        image_data: Raw image bytes
        target_size: Target size in bytes (default: 1MB)
        output_format: Output format (default: webp)

    Returns:
        CompressionResult
    """
    compressor = ImageCompressor(
        target_size=target_size,
        output_format=output_format
    )
    return compressor.compress(image_data)


def compress_file(
    input_path: str,
    output_path: Optional[str] = None,
    target_size: int = 1024 * 1024
) -> CompressionResult:
    """
    Quick function to compress an image file.

    Args:
        input_path: Path to input image
        output_path: Path for output
        target_size: Target size in bytes (default: 1MB)

    Returns:
        CompressionResult
    """
    compressor = ImageCompressor(target_size=target_size)
    return compressor.compress_file(input_path, output_path)


# CLI interface
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python image_compressor.py <input_image> [output_image]")
        print()
        print("Options:")
        print("  --target-size=BYTES   Target size (default: 1048576 = 1MB)")
        print("  --quality=N           Starting quality (default: 95)")
        print()
        print("Example:")
        print("  python image_compressor.py photo.jpg photo_small.webp")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = None
    target_size = 1024 * 1024

    for arg in sys.argv[2:]:
        if arg.startswith('--target-size='):
            target_size = int(arg.split('=')[1])
        elif arg.startswith('--quality='):
            pass  # Could add quality override
        elif not arg.startswith('--'):
            output_file = arg

    print(f"Compressing: {input_file}")
    print(f"Target size: {target_size:,} bytes ({target_size / 1024:.0f} KB)")
    print("-" * 40)

    result = compress_file(input_file, output_file, target_size)

    if result.success:
        print(f"✅ Success!")
        print(f"   Original: {result.original_size:,} bytes ({result.original_size / 1024:.0f} KB)")
        print(f"   Compressed: {result.compressed_size:,} bytes ({result.compressed_size / 1024:.0f} KB)")
        print(f"   Ratio: {result.compression_ratio:.1f}x")
        print(f"   Quality: {result.final_quality}")
        print(f"   Format: {result.output_format}")
        print(f"   Dimensions: {result.original_dimensions} → {result.final_dimensions}")
        if result.was_resized:
            print(f"   ⚠️  Image was resized to meet target")
        print(f"   Time: {result.processing_time_ms:.1f}ms")

        if result.warnings:
            print(f"   Warnings:")
            for w in result.warnings:
                print(f"     - {w}")
    else:
        print(f"❌ Failed: {result.error}")
        sys.exit(1)

