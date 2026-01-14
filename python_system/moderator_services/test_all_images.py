#!/usr/bin/env python3
"""
Test all images in sample_images folder with ML Security Scanner
"""
import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from moderation_service.app.services.images.security import SecurityScanner

# Supported image extensions
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.avif'}

def main():
    print("=" * 80)
    print("  ML SECURITY SCANNER - TESTING ALL SAMPLE IMAGES")
    print("=" * 80)
    print()

    # Initialize scanner with all ML detectors
    scanner = SecurityScanner(
        enable_ml_steg=True,
        enable_ml_forensics=True,
        enable_ml_hidden=True,
        use_gpu=False
    )

    print("ML Detectors Enabled:")
    print(f"  ✓ ML Steg: {scanner.ml_steg_detector is not None}")
    print(f"  ✓ ML Forensics: {scanner.ml_forensics_detector is not None}")
    print(f"  ✓ ML Hidden: {scanner.ml_hidden_detector is not None}")
    print()
    print("-" * 80)

    # Get all images
    sample_dir = Path("sample_images")
    images = sorted([
        f for f in sample_dir.iterdir()
        if f.suffix.lower() in IMAGE_EXTENSIONS
    ])

    print(f"Found {len(images)} images to scan\n")

    # Results summary
    results_summary = {
        'safe': [],
        'low': [],
        'medium': [],
        'high': [],
        'critical': []
    }

    # Scan each image
    for i, img_path in enumerate(images, 1):
        print(f"[{i}/{len(images)}] {img_path.name}")
        print("-" * 40)

        try:
            result = scanner.scan(str(img_path))

            # Determine status icon
            if result.is_safe:
                status = "✅ SAFE"
            elif result.threat_level.value == "critical":
                status = "🚫 CRITICAL"
            elif result.threat_level.value == "high":
                status = "⛔ HIGH"
            elif result.threat_level.value == "medium":
                status = "⚠️  MEDIUM"
            else:
                status = "ℹ️  LOW"

            print(f"  Status: {status}")
            print(f"  Threat Level: {result.threat_level.value.upper()}")
            print(f"  Risk Score: {result.risk_score:.2f}")

            # ML Results
            if result.ml_steg:
                steg_icon = "🔴" if result.ml_steg.has_steganography else "🟢"
                print(f"  ML Steg: {steg_icon} conf={result.ml_steg.confidence:.2f}")

            if result.ml_forensics:
                manip_icon = "🔴" if result.ml_forensics.is_manipulated else "🟢"
                print(f"  ML Forensics: {manip_icon} conf={result.ml_forensics.manipulation_confidence:.2f}")

            if result.ml_hidden:
                hidden_icon = "🔴" if result.ml_hidden.has_hidden_data else "🟢"
                print(f"  ML Hidden: {hidden_icon} conf={result.ml_hidden.confidence:.2f}")

                if result.ml_hidden.has_appended_data:
                    print(f"    └─ Appended: {result.ml_hidden.appended_size} bytes")
                if result.ml_hidden.has_hidden_markers:
                    print(f"    └─ Markers: {result.ml_hidden.markers_found[:2]}")
                if result.ml_hidden.has_embedded_file:
                    print(f"    └─ Embedded: {result.ml_hidden.embedded_file_type}")

            # Key warnings
            if result.warnings:
                print(f"  Warnings ({len(result.warnings)}):")
                for w in result.warnings[:3]:
                    print(f"    • {w[:60]}...")

            # Add to summary
            results_summary[result.threat_level.value].append(img_path.name)

        except Exception as e:
            print(f"  ❌ ERROR: {e}")
            results_summary['critical'].append(f"{img_path.name} (ERROR)")

        print()

    # Print summary
    print("=" * 80)
    print("  SCAN SUMMARY")
    print("=" * 80)
    print()

    total = len(images)
    safe_count = len(results_summary['safe'])
    unsafe_count = total - safe_count

    print(f"Total Images Scanned: {total}")
    print(f"Safe: {safe_count} ({safe_count/total*100:.1f}%)")
    print(f"Unsafe: {unsafe_count} ({unsafe_count/total*100:.1f}%)")
    print()

    for level in ['critical', 'high', 'medium', 'low', 'safe']:
        files = results_summary[level]
        if files:
            icon = {
                'critical': '🚫',
                'high': '⛔',
                'medium': '⚠️',
                'low': 'ℹ️',
                'safe': '✅'
            }[level]
            print(f"{icon} {level.upper()} ({len(files)}):")
            for f in files:
                print(f"   - {f}")
            print()

    print("=" * 80)
    print("  SCAN COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()

