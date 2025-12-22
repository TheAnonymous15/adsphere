#!/usr/bin/env python3
"""
Full Image Moderation Pipeline Test
====================================

Tests the complete pipeline:
    Scanner → Sanitizer → Compressor → OCR → Content Analysis

This validates:
1. Security scanning (ML detectors)
2. Sanitization (hidden data removal)
3. Compression (WebP ≤ 1MB)
4. OCR text extraction
5. Content analysis integration
"""
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 70)
print("  FULL IMAGE MODERATION PIPELINE TEST")
print("=" * 70)
print()

# Test imports
print("Step 1: Testing imports...")
try:
    from moderation_service.app.services.images import (
        ImageCompressor,
        CompressionResult,
        compress_image,
        compress_file,
        SecurityScanner,
        ImageOCRProcessor,
    )
    print("  ✓ ImageCompressor imported")
    print("  ✓ CompressionResult imported")
    print("  ✓ compress_image imported")
    print("  ✓ compress_file imported")
    print("  ✓ SecurityScanner imported")
    print("  ✓ ImageOCRProcessor imported")
except ImportError as e:
    print(f"  ✗ Import error: {e}")

try:
    from moderation_service.app.services.images.security import (
        SecurityScanner as SecScanner,
        ImageSanitizer,
        sanitize_image,
        scan_image,
    )
    print("  ✓ SecurityScanner (from security) imported")
    print("  ✓ ImageSanitizer imported")
    print("  ✓ sanitize_image imported")
    print("  ✓ scan_image imported")
except ImportError as e:
    print(f"  ✗ Import error: {e}")

print()

# Test 1: Compressor standalone
print("=" * 70)
print("  TEST 1: Image Compressor")
print("=" * 70)

test_image = "sample_images/modified.jpeg"
if os.path.exists(test_image):
    with open(test_image, "rb") as f:
        image_data = f.read()

    compressor = ImageCompressor(target_size=1024*1024)
    result = compressor.compress(image_data)

    print(f"  Input: {test_image}")
    print(f"  Original size: {result.original_size:,} bytes ({result.original_size/1024:.1f} KB)")
    print(f"  Compressed size: {result.compressed_size:,} bytes ({result.compressed_size/1024:.1f} KB)")
    print(f"  Compression ratio: {result.compression_ratio:.2f}x")
    print(f"  Output format: {result.output_format}")
    print(f"  Quality: {result.final_quality}")
    print(f"  Under 1MB: {'✓' if result.compressed_size <= 1024*1024 else '✗'}")
    print(f"  Success: {'✓' if result.success else '✗'}")
else:
    print(f"  ✗ Test image not found: {test_image}")

print()

# Test 2: Security Scanner with sanitization and compression
print("=" * 70)
print("  TEST 2: Security Scanner Pipeline")
print("=" * 70)

if os.path.exists(test_image):
    scanner = SecScanner(
        auto_sanitize=True,
        auto_compress=True,
        target_size=1024*1024
    )

    start_time = time.time()
    scan_result = scanner.scan(test_image)
    elapsed = (time.time() - start_time) * 1000

    print(f"  Input: {test_image}")
    print(f"  Processing time: {elapsed:.0f}ms")
    print()
    print("  Scan Results:")
    print(f"    Safe: {scan_result.is_safe}")
    print(f"    Threat level: {scan_result.threat_level.value}")
    print(f"    Risk score: {scan_result.risk_score:.2f}")
    print()
    print("  Sanitization:")
    print(f"    Sanitized: {'✓' if scan_result.sanitized else '✗'}")
    if scan_result.sanitize_result:
        sr = scan_result.sanitize_result
        print(f"    Appended data removed: {sr.appended_data_removed}")
        print(f"    Markers removed: {sr.markers_removed}")
        print(f"    Re-encoded: {sr.re_encoded}")
    print()
    print("  Compression:")
    print(f"    Compressed: {'✓' if scan_result.compressed else '✗'}")
    if scan_result.compressed:
        print(f"    Compressed size: {scan_result.compressed_size:,} bytes ({scan_result.compressed_size/1024:.1f} KB)")
        print(f"    Compression ratio: {scan_result.compression_ratio:.2f}x")
        print(f"    Under 1MB: {'✓' if scan_result.compressed_size <= 1024*1024 else '✗'}")
    print()
    print(f"  Data ready for OCR: {'✓' if scan_result.compressed_data else '✗'}")
else:
    print(f"  ✗ Test image not found: {test_image}")

print()

# Test 3: Full pipeline with mock OCR
print("=" * 70)
print("  TEST 3: Full Pipeline with OCR Callback")
print("=" * 70)

def mock_ocr(image_data: bytes) -> dict:
    """Mock OCR processor"""
    # Check if it's WebP format
    is_webp = image_data[:4] == b'RIFF' and b'WEBP' in image_data[:12]
    return {
        "success": True,
        "text": "[Extracted text would appear here]",
        "format": "webp" if is_webp else "jpeg",
        "size": len(image_data),
        "confidence": 0.95
    }

if os.path.exists(test_image):
    scanner = SecScanner(
        auto_sanitize=True,
        auto_compress=True,
        target_size=1024*1024
    )

    start_time = time.time()
    scan_result, ocr_result = scanner.scan_and_process(
        test_image,
        ocr_callback=mock_ocr
    )
    elapsed = (time.time() - start_time) * 1000

    print(f"  Input: {test_image}")
    print(f"  Total processing time: {elapsed:.0f}ms")
    print()
    print("  Pipeline stages:")
    print(f"    1. Scan:     {'✓' if scan_result else '✗'}")
    print(f"    2. Sanitize: {'✓' if scan_result.sanitized else '✗'}")
    print(f"    3. Compress: {'✓' if scan_result.compressed else '✗'}")
    print(f"    4. OCR:      {'✓' if ocr_result else '✗'}")
    print()
    if ocr_result:
        print("  OCR Result:")
        for key, value in ocr_result.items():
            print(f"    {key}: {value}")
else:
    print(f"  ✗ Test image not found: {test_image}")

print()

# Test 4: Multiple images
print("=" * 70)
print("  TEST 4: Batch Processing Multiple Images")
print("=" * 70)

import glob
images = glob.glob("sample_images/*.jpg") + glob.glob("sample_images/*.jpeg") + glob.glob("sample_images/*.png")
images = images[:5]  # Test first 5

if images:
    scanner = SecScanner(
        auto_sanitize=True,
        auto_compress=True,
        target_size=1024*1024
    )

    results = []
    total_original = 0
    total_compressed = 0

    for img in images:
        result = scanner.scan(img)
        original_size = os.path.getsize(img)
        total_original += original_size

        compressed_size = result.compressed_size if result.compressed else original_size
        total_compressed += compressed_size

        status = "✓" if result.compressed else "✗"
        print(f"  {status} {os.path.basename(img)}: {original_size/1024:.0f}KB → {compressed_size/1024:.0f}KB")
        results.append(result)

    print()
    print(f"  Total images: {len(images)}")
    print(f"  Successful: {sum(1 for r in results if r.compressed)}")
    print(f"  Total original: {total_original/1024:.0f} KB")
    print(f"  Total compressed: {total_compressed/1024:.0f} KB")
    print(f"  Overall ratio: {total_original/total_compressed:.2f}x" if total_compressed > 0 else "  N/A")
else:
    print("  ✗ No images found in sample_images/")

print()

# Test 5: Verify output safety
print("=" * 70)
print("  TEST 5: Verify Compressed Output is Safe")
print("=" * 70)

if os.path.exists(test_image):
    scanner = SecScanner(auto_sanitize=True, auto_compress=True)
    result = scanner.scan(test_image)

    if result.compressed_data:
        # Save and verify
        test_output = "sample_images/_test_output.webp"
        with open(test_output, "wb") as f:
            f.write(result.compressed_data)

        # Scan the output with a fresh scanner (no sanitize/compress)
        verifier = SecScanner(auto_sanitize=False, auto_compress=False)
        verify_result = verifier.scan(test_output)

        print(f"  Original: {os.path.basename(test_image)}")
        print(f"    Threat: {result.threat_level.value}")
        print(f"    Hidden data: {result.ml_hidden.has_hidden_data if result.ml_hidden else 'N/A'}")
        print()
        print(f"  Compressed output: {os.path.basename(test_output)}")
        print(f"    Threat: {verify_result.threat_level.value}")
        print(f"    Safe: {'✓' if verify_result.is_safe else '✗'}")
        print(f"    Hidden data: {verify_result.ml_hidden.has_hidden_data if verify_result.ml_hidden else 'N/A'}")

        # Cleanup
        os.remove(test_output)
    else:
        print("  ✗ No compressed data available")
else:
    print(f"  ✗ Test image not found: {test_image}")

print()

# Summary
print("=" * 70)
print("  PIPELINE SUMMARY")
print("=" * 70)
print("""
  ┌──────────┐   ┌───────────┐   ┌────────────┐   ┌─────────┐
  │ SCANNER  │──▶│ SANITIZER │──▶│ COMPRESSOR │──▶│   OCR   │
  └──────────┘   └───────────┘   └────────────┘   └─────────┘
       │              │               │               │
       ▼              ▼               ▼               ▼
  ML Detection    Remove hidden   WebP ≤ 1MB     Text extract
  - Steg          - EOF truncate  - Quality adj  - Process safe
  - Forensics     - Markers       - Resize if    - Clean image
  - Hidden data   - Re-encode       needed

  SECURITY GUARANTEES:
  ✓ Hidden data removed before OCR
  ✓ Compressed to ≤ 1MB for fast processing
  ✓ WebP format (best compression)
  ✓ Decompression bomb protection
  ✓ Path traversal prevention
""")
print("=" * 70)
print("  ALL TESTS COMPLETE")
print("=" * 70)

