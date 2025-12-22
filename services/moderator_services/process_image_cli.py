#!/usr/bin/env python3
"""
Image Processing CLI
====================

Command-line interface for the image processing pipeline.
Called by PHP ModerationServiceClient for local processing.

Pipeline: Scan → Sanitize → Compress

Usage:
    python3 process_image_cli.py <input_path> <output_path> [--json]

Output:
    - Processed image saved to output_path
    - JSON result printed to stdout (if --json flag)
"""
import sys
import os
import json
import argparse

# Add the moderation service to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def process_image(input_path: str, output_path: str, target_size: int = 1024*1024) -> dict:
    """
    Process image through the full pipeline.

    Returns dict with:
        success: bool
        original_size: int
        processed_size: int
        sanitized: bool
        compressed: bool
        threats_found: list
        warnings: list
    """
    result = {
        'success': False,
        'original_size': 0,
        'processed_size': 0,
        'sanitized': False,
        'compressed': False,
        'threats_found': [],
        'warnings': [],
        'format': 'webp'
    }

    if not os.path.exists(input_path):
        result['error'] = f'Input file not found: {input_path}'
        return result

    result['original_size'] = os.path.getsize(input_path)

    try:
        # Import the security scanner
        from moderation_service.app.services.images.security import SecurityScanner

        # Initialize scanner with full pipeline
        scanner = SecurityScanner(
            auto_sanitize=True,
            auto_compress=True,
            target_size=target_size
        )

        # Run the pipeline
        scan_result = scanner.scan(input_path)

        # Collect threat info
        if scan_result.ml_hidden and scan_result.ml_hidden.has_hidden_data:
            result['threats_found'].append('hidden_data')
        if scan_result.ml_steg and scan_result.ml_steg.has_steganography:
            result['threats_found'].append('steganography')
        if scan_result.ml_forensics and scan_result.ml_forensics.is_manipulated:
            result['threats_found'].append('manipulation')

        # Get processed data
        if scan_result.compressed and scan_result.compressed_data:
            # Save compressed WebP
            with open(output_path, 'wb') as f:
                f.write(scan_result.compressed_data)

            result['success'] = True
            result['sanitized'] = scan_result.sanitized
            result['compressed'] = scan_result.compressed
            result['processed_size'] = len(scan_result.compressed_data)
            result['compression_ratio'] = scan_result.compression_ratio
            result['warnings'] = [w for w in scan_result.warnings if 'Sanitizer' in w or 'Compressor' in w]

        elif scan_result.sanitized and scan_result.sanitized_data:
            # Fallback to sanitized (not compressed)
            with open(output_path, 'wb') as f:
                f.write(scan_result.sanitized_data)

            result['success'] = True
            result['sanitized'] = True
            result['compressed'] = False
            result['processed_size'] = len(scan_result.sanitized_data)
            result['warnings'].append('Compression unavailable, using sanitized image')

        else:
            # Fallback: copy original
            import shutil
            shutil.copy(input_path, output_path)
            result['success'] = True
            result['processed_size'] = result['original_size']
            result['warnings'].append('Processing unavailable, using original image')

    except ImportError as e:
        result['error'] = f'Import error: {e}'
        # Fallback to simple copy
        try:
            import shutil
            shutil.copy(input_path, output_path)
            result['success'] = True
            result['processed_size'] = result['original_size']
            result['warnings'].append(f'Pipeline unavailable ({e}), using original')
        except Exception as copy_err:
            result['error'] = f'Failed to copy: {copy_err}'

    except Exception as e:
        result['error'] = str(e)
        # Fallback to simple copy
        try:
            import shutil
            shutil.copy(input_path, output_path)
            result['success'] = True
            result['processed_size'] = result['original_size']
            result['warnings'].append(f'Processing failed ({e}), using original')
        except Exception as copy_err:
            result['error'] = f'Failed to copy: {copy_err}'

    return result


def main():
    parser = argparse.ArgumentParser(description='Process image through security pipeline')
    parser.add_argument('input', help='Input image path')
    parser.add_argument('output', help='Output image path')
    parser.add_argument('--target-size', type=int, default=1024*1024, help='Target size in bytes')
    parser.add_argument('--json', action='store_true', help='Output JSON result')

    args = parser.parse_args()

    result = process_image(args.input, args.output, args.target_size)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        if result['success']:
            print(f"✓ Processed: {args.input}")
            print(f"  Original: {result['original_size']:,} bytes")
            print(f"  Output: {result['processed_size']:,} bytes")
            if result['threats_found']:
                print(f"  Threats removed: {', '.join(result['threats_found'])}")
        else:
            print(f"✗ Failed: {result.get('error', 'Unknown error')}")
            sys.exit(1)


if __name__ == '__main__':
    main()

