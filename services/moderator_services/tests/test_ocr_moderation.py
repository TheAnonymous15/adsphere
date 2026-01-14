#!/usr/bin/env python3
"""
OCR-Based Image Moderation Test
Tests images with text content and provides detailed analysis
"""
import sys
import requests
import json
import os
from pathlib import Path

# Add path for model_registry
sys.path.insert(0, str(Path(__file__).parent))
from model_registry import ensure_models

# Ensure models are available
REQUIRED_MODELS = ['paddleocr', 'detoxify', 'torch']
ensure_models(REQUIRED_MODELS, verbose=False)

ML_SERVICE_URL = "http://localhost:8002"
SAMPLE_DIR = Path(__file__).parent / "sample_images"

# Images likely to contain text based on filenames
TEXT_IMAGES = [
    "assault-criminal-lawyer.jpg",  # Legal/text image
    "gettyimages-sb10061957u-003-612x612.jpg",  # Getty watermark
    "file-20181030-76384-6nsrgw.avif",  # Might have text
    "file-20181031-122147-2o7afn.avif",  # Might have text
]

def test_image_with_ocr(image_path: Path):
    """Test single image with detailed OCR analysis"""

    print(f"\n{'='*80}")
    print(f"Image: {image_path.name}")
    print(f"Size: {image_path.stat().st_size / 1024:.1f} KB")
    print(f"{'='*80}\n")

    try:
        with open(image_path, 'rb') as f:
            files = {'file': (image_path.name, f, 'image/jpeg')}
            response = requests.post(
                f"{ML_SERVICE_URL}/moderate/image",
                files=files,
                timeout=30
            )

        if response.status_code == 200:
            result = response.json()
            analyze_result(result, image_path.name)
            return result
        else:
            print(f"❌ Error: HTTP {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return None

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None

def analyze_result(result: dict, filename: str):
    """Analyze and print detailed moderation results"""

    decision = result.get('decision', 'unknown')
    risk_level = result.get('risk_level', 'unknown')

    # Decision emoji
    emoji = {'approve': '✅', 'review': '⚠️', 'block': '🚫'}.get(decision, '❓')

    print(f"📋 DECISION: {emoji} {decision.upper()}")
    print(f"⚠️  RISK LEVEL: {risk_level.upper()}")
    print(f"\n{'-'*80}")

    # Extract OCR text if available
    ai_sources = result.get('ai_sources', {})
    ocr_data = ai_sources.get('ocr', {})

    if ocr_data and isinstance(ocr_data, dict):
        ocr_details = ocr_data.get('details', {})
        extracted_text = ocr_details.get('text', '')

        if extracted_text and extracted_text.strip():
            print(f"\n📝 EXTRACTED TEXT:")
            print(f"{'-'*80}")
            print(f"{extracted_text.strip()}")
            print(f"{'-'*80}")

            # Analyze text
            print(f"\n📊 TEXT ANALYSIS:")
            print(f"  - Character count: {len(extracted_text)}")
            print(f"  - Word count: {len(extracted_text.split())}")

            # Check for keywords
            text_lower = extracted_text.lower()

            # Check for problematic keywords
            problematic_keywords = {
                'violence': ['assault', 'attack', 'violence', 'kill', 'murder', 'fight'],
                'adult': ['sex', 'porn', 'nude', 'xxx', 'adult'],
                'drugs': ['drug', 'cocaine', 'heroin', 'meth'],
                'hate': ['hate', 'racist', 'nazi', 'kill'],
                'legal': ['lawyer', 'attorney', 'legal', 'criminal', 'court', 'law']
            }

            found_keywords = {}
            for category, keywords in problematic_keywords.items():
                matches = [k for k in keywords if k in text_lower]
                if matches:
                    found_keywords[category] = matches

            if found_keywords:
                print(f"\n  Keywords detected:")
                for category, keywords in found_keywords.items():
                    print(f"    - {category.capitalize()}: {', '.join(keywords)}")
        else:
            print(f"\n📝 EXTRACTED TEXT: None (no text detected in image)")
    else:
        print(f"\n📝 EXTRACTED TEXT: OCR not available or failed")

    # Category scores
    print(f"\n📊 CATEGORY SCORES:")
    category_scores = result.get('category_scores', {})
    flagged = {k: v for k, v in category_scores.items() if v > 0.05}

    if flagged:
        for category, score in sorted(flagged.items(), key=lambda x: x[1], reverse=True):
            bar = '█' * int(score * 20)
            print(f"  {category:20s}: {score:6.1%} {bar}")
    else:
        print(f"  All categories < 5% (safe)")

    # Reasons
    reasons = result.get('reasons', [])
    if reasons:
        print(f"\n💭 DECISION REASONS:")
        for i, reason in enumerate(reasons[:5], 1):
            print(f"  {i}. {reason}")

    # Why this decision?
    print(f"\n🎯 WHY THIS DECISION:")
    if decision == 'approve':
        print(f"  ✅ Image passed all safety checks")
        print(f"  ✅ No harmful content detected")
        if extracted_text and extracted_text.strip():
            print(f"  ℹ️  Text content analyzed and deemed safe")
            if 'legal' in found_keywords:
                print(f"  ℹ️  Legal/professional content identified (legitimate)")
    elif decision == 'review':
        print(f"  ⚠️  Borderline content detected")
        print(f"  ⚠️  Human review recommended for verification")
        if flagged:
            top_category = max(flagged.items(), key=lambda x: x[1])
            print(f"  ⚠️  Primary concern: {top_category[0]} ({top_category[1]:.1%})")
    elif decision == 'block':
        print(f"  🚫 Harmful content detected")
        print(f"  🚫 Violates platform safety policies")
        if flagged:
            top_categories = sorted(flagged.items(), key=lambda x: x[1], reverse=True)[:3]
            print(f"  🚫 Violations:")
            for cat, score in top_categories:
                print(f"     - {cat}: {score:.1%}")

    print(f"\n{'='*80}\n")

def main():
    print("\n" + "="*80)
    print("  OCR-BASED IMAGE MODERATION TEST")
    print("  Testing images with text content")
    print("="*80)

    # Test all images (OCR will only extract text if present)
    images = sorted(SAMPLE_DIR.glob("*.jpg")) + \
             sorted(SAMPLE_DIR.glob("*.jpeg")) + \
             sorted(SAMPLE_DIR.glob("*.png")) + \
             sorted(SAMPLE_DIR.glob("*.webp")) + \
             sorted(SAMPLE_DIR.glob("*.avif"))

    print(f"\nTesting {len(images)} images for text content...")
    print(f"OCR will extract and analyze any text found\n")

    results = {}
    for image_path in images:
        result = test_image_with_ocr(image_path)
        if result:
            results[image_path.name] = result

    # Summary
    print("\n" + "="*80)
    print("  SUMMARY - TEXT ANALYSIS")
    print("="*80 + "\n")

    images_with_text = []
    for filename, result in results.items():
        ai_sources = result.get('ai_sources', {})
        ocr_data = ai_sources.get('ocr', {})
        if ocr_data and isinstance(ocr_data, dict):
            ocr_details = ocr_data.get('details', {})
            text = ocr_details.get('text', '')
            if text and text.strip():
                images_with_text.append({
                    'filename': filename,
                    'text': text.strip(),
                    'decision': result.get('decision'),
                    'risk': result.get('risk_level')
                })

    if images_with_text:
        print(f"Images with extracted text: {len(images_with_text)}\n")
        for i, img in enumerate(images_with_text, 1):
            emoji = {'approve': '✅', 'review': '⚠️', 'block': '🚫'}.get(img['decision'], '❓')
            print(f"{i}. {img['filename']}")
            print(f"   Decision: {emoji} {img['decision'].upper()}")
            print(f"   Text preview: {img['text'][:80]}...")
            print()
    else:
        print("⚠️  No text detected in any images (OCR found no readable text)")

    print("="*80 + "\n")

if __name__ == "__main__":
    main()

