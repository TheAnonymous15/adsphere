#!/usr/bin/env python3
"""
False Positive Analysis Tool
============================
Investigates detected embedded files to determine if they're real or false positives.
"""
import os
import struct
from pathlib import Path

# Signatures we're checking
SIGNATURES = {
    b'\x1f\x8b': ('GZIP', 'GZIP Archive'),
    b'\x00\x00\x01\x00': ('ICO', 'ICO/CUR File'),
}

def analyze_gzip_signature(data: bytes, pos: int) -> dict:
    """Analyze if GZIP signature at position is a real GZIP file"""
    result = {
        'is_real': False,
        'reason': '',
        'details': {}
    }

    if pos + 10 > len(data):
        result['reason'] = 'Not enough data after signature'
        return result

    # GZIP header structure:
    # Bytes 0-1: Magic (1f 8b)
    # Byte 2: Compression method (08 = deflate)
    # Byte 3: Flags
    # Bytes 4-7: Modification time
    # Byte 8: Extra flags
    # Byte 9: OS

    header = data[pos:pos+10]

    compression_method = header[2]
    flags = header[3]
    mtime = struct.unpack('<I', header[4:8])[0]
    xfl = header[8]
    os_type = header[9]

    result['details'] = {
        'compression_method': compression_method,
        'flags': flags,
        'mtime': mtime,
        'xfl': xfl,
        'os': os_type,
        'hex': header.hex()
    }

    # Valid GZIP checks:
    # 1. Compression method should be 8 (deflate)
    if compression_method != 8:
        result['reason'] = f'Invalid compression method: {compression_method} (expected 8)'
        return result

    # 2. Flags should be 0-31 (only bits 0-4 are defined)
    if flags > 31:
        result['reason'] = f'Invalid flags: {flags}'
        return result

    # 3. OS should be 0-13 or 255
    valid_os = list(range(14)) + [255]
    if os_type not in valid_os:
        result['reason'] = f'Invalid OS type: {os_type}'
        return result

    # 4. Check if there's valid deflate data following
    # This is a simplified check - real validation would decompress

    # If all basic checks pass, it might be real
    result['is_real'] = True
    result['reason'] = 'Passes basic GZIP header validation'

    return result


def analyze_ico_signature(data: bytes, pos: int) -> dict:
    """Analyze if ICO signature at position is a real ICO file"""
    result = {
        'is_real': False,
        'reason': '',
        'details': {}
    }

    if pos + 6 > len(data):
        result['reason'] = 'Not enough data after signature'
        return result

    # ICO header structure:
    # Bytes 0-1: Reserved (must be 0)
    # Bytes 2-3: Type (1 = ICO, 2 = CUR)
    # Bytes 4-5: Number of images

    header = data[pos:pos+6]

    reserved = struct.unpack('<H', header[0:2])[0]
    img_type = struct.unpack('<H', header[2:4])[0]
    num_images = struct.unpack('<H', header[4:6])[0]

    result['details'] = {
        'reserved': reserved,
        'type': img_type,
        'num_images': num_images,
        'hex': header.hex()
    }

    # Valid ICO checks:
    # 1. Reserved must be 0
    if reserved != 0:
        result['reason'] = f'Reserved field not 0: {reserved}'
        return result

    # 2. Type must be 1 (ICO) or 2 (CUR)
    if img_type not in [1, 2]:
        result['reason'] = f'Invalid type: {img_type} (expected 1 or 2)'
        return result

    # 3. Number of images should be reasonable (1-256)
    if num_images == 0 or num_images > 256:
        result['reason'] = f'Invalid image count: {num_images}'
        return result

    # If checks pass, might be real
    result['is_real'] = True
    result['reason'] = 'Passes basic ICO header validation'

    return result


def check_context(data: bytes, pos: int, window: int = 50) -> str:
    """Get context around the signature"""
    start = max(0, pos - window)
    end = min(len(data), pos + window)

    context = data[start:end]

    # Check if it looks like image data or text
    printable = sum(1 for b in context if 32 <= b <= 126)
    ratio = printable / len(context)

    if ratio > 0.7:
        return f"Mostly printable text ({ratio:.1%})"
    else:
        return f"Binary data ({ratio:.1%} printable)"


def analyze_image(filepath: str) -> dict:
    """Analyze a single image for false positives"""
    result = {
        'file': os.path.basename(filepath),
        'size': os.path.getsize(filepath),
        'detections': []
    }

    with open(filepath, 'rb') as f:
        data = f.read()

    # Find all signature occurrences
    for sig, (sig_type, sig_name) in SIGNATURES.items():
        pos = 0
        while True:
            pos = data.find(sig, pos)
            if pos == -1:
                break

            # Skip if in first 1KB (image header area)
            if pos < 1024:
                pos += 1
                continue

            detection = {
                'type': sig_type,
                'name': sig_name,
                'offset': pos,
                'context': check_context(data, pos)
            }

            # Validate based on type
            if sig_type == 'GZIP':
                analysis = analyze_gzip_signature(data, pos)
            elif sig_type == 'ICO':
                analysis = analyze_ico_signature(data, pos)
            else:
                analysis = {'is_real': False, 'reason': 'Unknown type'}

            detection['is_real'] = analysis['is_real']
            detection['reason'] = analysis['reason']
            detection['details'] = analysis.get('details', {})

            result['detections'].append(detection)
            pos += 1

    return result


def main():
    print("=" * 80)
    print("  FALSE POSITIVE ANALYSIS")
    print("=" * 80)
    print()

    # Images that were flagged as having embedded files
    flagged_images = [
        'sample_images/assault-criminal-lawyer.jpg',
        'sample_images/gettyimages-sb10061957u-003-612x612.jpg',
        'sample_images/images (11).jpeg',
        'sample_images/legit.jpg',
        'sample_images/man-noose-around-neck-on-260nw-1297019821.webp',
        'sample_images/modified.jpeg',
        'sample_images/sam3.jpeg',
        'sample_images/ss.avif',
        'sample_images/ss2.avif',
    ]

    real_positives = []
    false_positives = []

    for img_path in flagged_images:
        if not os.path.exists(img_path):
            print(f"⚠️  File not found: {img_path}")
            continue

        print(f"📄 {os.path.basename(img_path)}")
        print("-" * 40)

        analysis = analyze_image(img_path)

        if not analysis['detections']:
            print("  No embedded file signatures found")
        else:
            for det in analysis['detections']:
                status = "✅ REAL" if det['is_real'] else "❌ FALSE POSITIVE"
                print(f"  {det['name']} at offset {det['offset']}")
                print(f"    Status: {status}")
                print(f"    Reason: {det['reason']}")
                print(f"    Context: {det['context']}")
                if det['details']:
                    print(f"    Header: {det['details'].get('hex', 'N/A')}")

                if det['is_real']:
                    real_positives.append((img_path, det))
                else:
                    false_positives.append((img_path, det))

        print()

    # Summary
    print("=" * 80)
    print("  ANALYSIS SUMMARY")
    print("=" * 80)
    print()
    print(f"Total Detections: {len(real_positives) + len(false_positives)}")
    print(f"Real Positives: {len(real_positives)}")
    print(f"False Positives: {len(false_positives)}")
    print()

    if false_positives:
        print("❌ FALSE POSITIVES:")
        for img, det in false_positives:
            print(f"   - {os.path.basename(img)}: {det['name']} ({det['reason']})")
        print()

    if real_positives:
        print("✅ REAL EMBEDDED FILES:")
        for img, det in real_positives:
            print(f"   - {os.path.basename(img)}: {det['name']} at offset {det['offset']}")
        print()

    # Calculate false positive rate
    total = len(real_positives) + len(false_positives)
    if total > 0:
        fp_rate = len(false_positives) / total * 100
        print(f"False Positive Rate: {fp_rate:.1f}%")

    print()
    print("=" * 80)


if __name__ == "__main__":
    main()

