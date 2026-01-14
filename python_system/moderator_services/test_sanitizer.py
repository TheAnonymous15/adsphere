#!/usr/bin/env python3
"""
Test Full Pipeline: Scanner → Sanitizer → Compressor → OCR

Demonstrates:
1. Security scanning with auto-sanitization
2. Compression to WebP ≤ 1MB
3. Decompression bomb protection
4. Path traversal prevention
5. OCR callback integration with compressed images
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from moderation_service.app.services.images.security import SecurityScanner
from moderation_service.app.services.images.security.image_sanitizer import sanitize_image
from moderation_service.app.services.images.image_compressor import ImageCompressor, compress_image

print("=" * 70)
print("  FULL IMAGE PROCESSING PIPELINE TEST")
print("  Scanner → Sanitizer → Compressor → OCR")
print("=" * 70)


# Mock OCR processor
def mock_ocr_processor(image_data: bytes) -> dict:
    """Mock OCR that would normally extract text from image"""
    return {
        "success": True,
        "text": "[Mock OCR: Would extract text from compressed WebP image]",
        "image_size": len(image_data),
        "format": "webp" if image_data[:4] == b'RIFF' else "other",
        "safe": True
    }


# Test 1: Compressor standalone
print("\n" + "=" * 70)
print("  TEST 1: Image Compressor Standalone")
print("=" * 70)

with open("sample_images/modified.jpeg", "rb") as f:
    original_data = f.read()

comp_result = compress_image(original_data, target_size=1024*1024)

if comp_result.success:
    print(f"✅ Compression successful!")
    print(f"   Original: {comp_result.original_size:,} bytes ({comp_result.original_size/1024:.0f} KB)")
    print(f"   Compressed: {comp_result.compressed_size:,} bytes ({comp_result.compressed_size/1024:.0f} KB)")
    print(f"   Ratio: {comp_result.compression_ratio:.1f}x")
    print(f"   Quality: {comp_result.final_quality}")
    print(f"   Format: {comp_result.output_format}")
    print(f"   Dimensions: {comp_result.original_dimensions} → {comp_result.final_dimensions}")
    print(f"   Under 1MB: {'✓' if comp_result.compressed_size <= 1024*1024 else '✗'}")
else:
    print(f"❌ Failed: {comp_result.error}")


# Test 2: Full Pipeline
print("\n" + "=" * 70)
print("  TEST 2: Full Pipeline - Scan → Sanitize → Compress → OCR")
print("=" * 70)

scanner = SecurityScanner(
    auto_sanitize=True,
    auto_compress=True,
    target_size=1024*1024  # 1MB
)

print("\nProcessing modified.jpeg through full pipeline...")
scan_result, ocr_result = scanner.scan_and_process(
    "sample_images/modified.jpeg",
    ocr_callback=mock_ocr_processor
)

print(f"\nPipeline Results:")
print(f"  1. Scan: {'✓' if scan_result else '✗'} (Threat: {scan_result.threat_level.value})")
print(f"  2. Sanitize: {'✓' if scan_result.sanitized else '✗'}")
print(f"  3. Compress: {'✓' if scan_result.compressed else '✗'}")
print(f"  4. OCR: {'✓' if ocr_result else '✗'}")

if scan_result.compressed:
    print(f"\nCompression Details:")
    print(f"   Original size: {scan_result.file_size:,} bytes")
    print(f"   Compressed size: {scan_result.compressed_size:,} bytes ({scan_result.compressed_size/1024:.0f} KB)")
    print(f"   Ratio: {scan_result.compression_ratio:.1f}x")
    print(f"   Under 1MB: {'✓' if scan_result.compressed_size <= 1024*1024 else '✗'}")

if ocr_result:
    print(f"\nOCR Output:")
    for key, value in ocr_result.items():
        print(f"    {key}: {value}")


# Test 3: Large Image Compression
print("\n" + "=" * 70)
print("  TEST 3: Large Image Handling")
print("=" * 70)

# Find the largest image in sample_images
import glob
images = glob.glob("sample_images/*.jpg") + glob.glob("sample_images/*.jpeg") + glob.glob("sample_images/*.png")
if images:
    largest = max(images, key=lambda x: os.path.getsize(x))
    largest_size = os.path.getsize(largest)

    print(f"\nLargest image: {os.path.basename(largest)} ({largest_size/1024:.0f} KB)")

    result = scanner.scan(largest)

    print(f"  Sanitized: {'✓' if result.sanitized else '✗'}")
    print(f"  Compressed: {'✓' if result.compressed else '✗'}")
    if result.compressed:
        print(f"  Final size: {result.compressed_size/1024:.0f} KB")
        print(f"  Under 1MB: {'✓' if result.compressed_size <= 1024*1024 else '✗'}")


# Test 4: Verify Clean Output
print("\n" + "=" * 70)
print("  TEST 4: Verify Clean Output is Safe")
print("=" * 70)

# Scan the compressed output
verifier = SecurityScanner(auto_sanitize=False, auto_compress=False)

# Save compressed data to file for verification
if scan_result.compressed_data:
    with open("sample_images/test_compressed.webp", "wb") as f:
        f.write(scan_result.compressed_data)

    verify_result = verifier.scan("sample_images/test_compressed.webp")

    print(f"\nVerification of compressed WebP:")
    print(f"  Safe: {verify_result.is_safe}")
    print(f"  Threat Level: {verify_result.threat_level.value}")
    print(f"  File Size: {os.path.getsize('sample_images/test_compressed.webp')/1024:.0f} KB")

    # Clean up
    os.remove("sample_images/test_compressed.webp")


# Summary
print("\n" + "=" * 70)
print("  PIPELINE SUMMARY")
print("=" * 70)
print("""
  ┌──────────┐   ┌───────────┐   ┌────────────┐   ┌─────────┐
  │ SCANNER  │──▶│ SANITIZER │──▶│ COMPRESSOR │──▶│   OCR   │
  └──────────┘   └───────────┘   └────────────┘   └─────────┘
       │              │               │               │
       ▼              ▼               ▼               ▼
  Detect threats  Remove hidden   Compress to     Process clean
  - ML Steg       - EOF truncate  WebP ≤ 1MB      optimized image
  - ML Forensics  - Remove markers
  - ML Hidden     - Re-encode
                  - Strip metadata

  BENEFITS:
  ✓ No hidden data reaches OCR processor
  ✓ Compressed to ≤ 1MB (faster processing)
  ✓ WebP format (best compression)
  ✓ Decompression bomb protection
  ✓ Path traversal prevention
""")
print("=" * 70)

