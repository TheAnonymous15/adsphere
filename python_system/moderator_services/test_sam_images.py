#!/usr/bin/env python3
"""
Test sam images with text content
"""
import sys
import requests
import json
from pathlib import Path

# Add path for model_registry
sys.path.insert(0, str(Path(__file__).parent))
from model_registry import ensure_models

# Ensure models are available
REQUIRED_MODELS = ['yolov8n', 'paddleocr', 'detoxify', 'torch']
ensure_models(REQUIRED_MODELS, verbose=False)

ML_SERVICE_URL = "http://localhost:8002"
SAMPLE_DIR = Path(__file__).parent / "sample_images"

def test_image_detailed(image_name):
    """Test image and show detailed results"""
    image_path = SAMPLE_DIR / image_name

    if not image_path.exists():
        print(f"❌ Image not found: {image_name}")
        return None

    print(f"\n{'='*80}")
    print(f"📸 TESTING: {image_name}")
    print(f"   Size: {image_path.stat().st_size / 1024:.1f} KB")
    print(f"{'='*80}\n")

    try:
        with open(image_path, 'rb') as f:
            files = {'file': (image_name, f, 'image/jpeg')}
            response = requests.post(
                f"{ML_SERVICE_URL}/moderate/image",
                files=files,
                timeout=30
            )

        if response.status_code != 200:
            print(f"❌ Error: HTTP {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return None

        result = response.json()

        # Extract key information
        decision = result.get('decision', 'unknown')
        risk_level = result.get('risk_level', 'unknown')
        category_scores = result.get('category_scores', {})
        ai_sources = result.get('ai_sources', {})
        reasons = result.get('reasons', [])

        # Decision
        emoji = {'approve': '✅', 'review': '⚠️', 'block': '🚫'}.get(decision, '❓')
        print(f"🎯 DECISION: {emoji} {decision.upper()}")
        print(f"⚠️  RISK LEVEL: {risk_level.upper()}\n")

        # Extracted text from OCR
        ocr_data = ai_sources.get('ocr', {})
        if ocr_data and isinstance(ocr_data, dict):
            ocr_details = ocr_data.get('details', {})
            extracted_text = ocr_details.get('text', '')

            if extracted_text and extracted_text.strip():
                print(f"📝 EXTRACTED TEXT:")
                print(f"{'-'*80}")
                print(f"{extracted_text.strip()}")
                print(f"{'-'*80}\n")

                # Analyze text
                print(f"📊 TEXT ANALYSIS:")
                words = extracted_text.split()
                print(f"   • Character count: {len(extracted_text)}")
                print(f"   • Word count: {len(words)}")
                print(f"   • Text length: {len(extracted_text.strip())} chars\n")

                # Check for problematic keywords
                text_lower = extracted_text.lower()

                # Define keyword categories
                keyword_checks = {
                    '🚫 Violence': ['assault', 'attack', 'violence', 'kill', 'murder', 'fight', 'beat', 'hurt', 'harm'],
                    '🔞 Adult': ['sex', 'porn', 'nude', 'xxx', 'adult', 'nsfw', 'sensual', 'erotic'],
                    '💊 Drugs': ['drug', 'cocaine', 'heroin', 'meth', 'weed', 'marijuana', 'pills'],
                    '😡 Hate': ['hate', 'racist', 'nazi', 'kill all', 'death to', 'destroy'],
                    '💰 Scam': ['get rich', 'guarantee', 'free money', 'miracle', 'limited time', 'act now'],
                    '⚖️ Legal': ['lawyer', 'attorney', 'legal', 'criminal', 'court', 'law', 'defense'],
                    '🏢 Professional': ['professional', 'certified', 'licensed', 'expert', 'service']
                }

                found_keywords = {}
                for category, keywords in keyword_checks.items():
                    matches = []
                    for kw in keywords:
                        if kw in text_lower:
                            matches.append(kw)
                    if matches:
                        found_keywords[category] = matches

                if found_keywords:
                    print(f"🔍 KEYWORDS DETECTED:")
                    for category, keywords in found_keywords.items():
                        print(f"   {category}: {', '.join(keywords)}")
                    print()
                else:
                    print(f"   ℹ️  No problematic keywords detected\n")
            else:
                print(f"📝 EXTRACTED TEXT: ⚠️  No text detected in image\n")
        else:
            print(f"📝 EXTRACTED TEXT: ❌ OCR service not available\n")

        # Category scores
        print(f"📊 VISUAL CATEGORY SCORES:")
        flagged = {k: v for k, v in category_scores.items() if v > 0.05}

        if flagged:
            for category, score in sorted(flagged.items(), key=lambda x: x[1], reverse=True):
                bar = '█' * int(score * 20)
                emoji_map = {
                    'blood': '🩸',
                    'violence': '👊',
                    'weapons': '🔫',
                    'nudity': '🔞',
                    'sexual_content': '🔞',
                    'hate': '😡',
                    'drugs': '💊'
                }
                cat_emoji = emoji_map.get(category, '•')
                print(f"   {cat_emoji} {category:20s}: {score:6.1%} {bar}")
        else:
            print(f"   ✅ All visual categories < 5% (safe)")
        print()

        # Reasons for decision
        if reasons:
            print(f"💭 DECISION REASONS:")
            for i, reason in enumerate(reasons[:5], 1):
                print(f"   {i}. {reason}")
            print()

        # Final explanation
        print(f"🎯 WHY THIS DECISION:")

        if decision == 'approve':
            print(f"   ✅ Content passed all safety checks")
            if extracted_text and extracted_text.strip():
                print(f"   ✅ Text analyzed and deemed safe")
                if '⚖️ Legal' in found_keywords or '🏢 Professional' in found_keywords:
                    print(f"   ℹ️  Professional/legitimate content identified")
            print(f"   ✅ No policy violations detected")

        elif decision == 'review':
            print(f"   ⚠️  Borderline content requires human verification")
            if flagged:
                top = max(flagged.items(), key=lambda x: x[1])
                print(f"   ⚠️  Primary concern: {top[0]} at {top[1]:.1%}")
            if extracted_text and found_keywords:
                concerning = [k for k in found_keywords.keys() if k.startswith(('🚫', '🔞', '💊', '😡', '💰'))]
                if concerning:
                    print(f"   ⚠️  Potentially concerning text detected")

        elif decision == 'block':
            print(f"   🚫 Content violates platform safety policies")
            if flagged:
                violations = sorted(flagged.items(), key=lambda x: x[1], reverse=True)[:3]
                print(f"   🚫 Violations detected:")
                for cat, score in violations:
                    print(f"      • {cat}: {score:.1%}")
            if extracted_text and found_keywords:
                harmful = [k for k in found_keywords.keys() if k.startswith(('🚫', '🔞', '💊', '😡'))]
                if harmful:
                    print(f"   🚫 Harmful text content: {', '.join(harmful)}")

        print(f"\n{'='*80}\n")

        return result

    except Exception as e:
        print(f"❌ Error: {str(e)}\n")
        return None

def main():
    print("\n" + "="*80)
    print("  TEXT IMAGE MODERATION TEST - SAM IMAGES")
    print("  Testing images with text content")
    print("="*80)

    # Test the sam images
    test_images = ['sam2.jpeg', 'sam3.jpeg']

    # Check for sam.jpeg
    if (SAMPLE_DIR / 'sam.jpeg').exists():
        test_images.insert(0, 'sam.jpeg')

    results = {}
    for image_name in test_images:
        result = test_image_detailed(image_name)
        if result:
            results[image_name] = result

    # Summary
    if results:
        print("\n" + "="*80)
        print("  SUMMARY")
        print("="*80 + "\n")

        decisions = {'approve': [], 'review': [], 'block': []}
        for img_name, result in results.items():
            decision = result.get('decision', 'unknown')
            if decision in decisions:
                decisions[decision].append(img_name)

        print(f"Total Tested: {len(results)}")
        print(f"✅ Approved: {len(decisions['approve'])}")
        print(f"⚠️  Flagged for Review: {len(decisions['review'])}")
        print(f"🚫 Blocked: {len(decisions['block'])}")
        print()

        if decisions['approve']:
            print(f"✅ APPROVED IMAGES:")
            for img in decisions['approve']:
                print(f"   • {img}")
            print()

        if decisions['review']:
            print(f"⚠️  REVIEW NEEDED:")
            for img in decisions['review']:
                print(f"   • {img}")
            print()

        if decisions['block']:
            print(f"🚫 BLOCKED IMAGES:")
            for img in decisions['block']:
                print(f"   • {img}")
            print()

    print("="*80 + "\n")

if __name__ == "__main__":
    main()

