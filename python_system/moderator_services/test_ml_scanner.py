#!/usr/bin/env python3
"""Test security scanner with ML detectors only"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from moderation_service.app.services.images.security import SecurityScanner

print("=== ML-ONLY SCANNER TEST ===")
print()

# Default scanner - ML only
scanner = SecurityScanner()

print("Detectors enabled:")
print(f"  ML Steg: {scanner.ml_steg_detector is not None}")
print(f"  ML Forensics: {scanner.ml_forensics_detector is not None}")
print(f"  ML Hidden: {scanner.ml_hidden_detector is not None}")
print(f"  Traditional (File Structure): {scanner.file_structure_detector is not None}")
print(f"  Traditional (Entropy): {scanner.entropy_detector is not None}")
print()

for img in ['legit.jpg', 'modified.jpeg']:
    path = f'sample_images/{img}'
    print(f'{img}:')
    result = scanner.scan(path)
    print(f'  Safe: {result.is_safe}')
    print(f'  Threat: {result.threat_level.value}')
    print(f'  Risk Score: {result.risk_score:.2f}')
    print(f'  Embedded Data: {result.has_embedded_data}')
    print(f'  Malware: {result.malware_detected}')

    if result.ml_steg:
        print(f'  ML Steg: confidence={result.ml_steg.confidence:.2f}, detected={result.ml_steg.has_steganography}')

    if result.ml_forensics:
        print(f'  ML Forensics: confidence={result.ml_forensics.manipulation_confidence:.2f}')

    if result.ml_hidden:
        print(f'  ML Hidden: confidence={result.ml_hidden.confidence:.2f}, detected={result.ml_hidden.has_hidden_data}')
        if result.ml_hidden.has_appended_data:
            print(f'    - Appended data: {result.ml_hidden.appended_size} bytes')
        if result.ml_hidden.has_hidden_markers:
            print(f'    - Markers: {result.ml_hidden.markers_found}')
        if result.ml_hidden.has_embedded_file:
            print(f'    - Embedded: {result.ml_hidden.embedded_file_type}')

    print(f'  Warnings ({len(result.warnings)}):')
    for w in result.warnings[:5]:
        print(f'    - {w[:70]}')
    print()

print("=== TEST COMPLETE ===")

