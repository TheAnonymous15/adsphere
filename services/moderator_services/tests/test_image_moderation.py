#!/usr/bin/env python3
"""
Image Moderation Test Script
Tests all sample images through the ML moderation service
"""
import requests
import json
import os
import sys
from pathlib import Path

# Add path for model_registry
sys.path.insert(0, str(Path(__file__).parent))
from model_registry import ensure_models

# Ensure models are available
REQUIRED_MODELS = ['yolov8n', 'transformers', 'torch', 'PIL']
ensure_models(REQUIRED_MODELS, verbose=False)

# ML Service URL
ML_SERVICE_URL = "http://localhost:8002"

# Sample images directory
SAMPLE_DIR = Path(__file__).parent / "sample_images"

def test_image_moderation(image_path: Path):
    """Test image moderation via ML service"""

    print(f"\n{'='*80}")
    print(f"Testing: {image_path.name}")
    print(f"Size: {image_path.stat().st_size / 1024:.1f} KB")
    print(f"{'='*80}\n")

    # For now, test with a simple endpoint
    # The ML service should have an image moderation endpoint

    try:
        # First check if service is up
        health = requests.get(f"{ML_SERVICE_URL}/health", timeout=5)
        if health.status_code != 200:
            print(f"❌ ML Service not healthy")
            return None

        # Test image moderation
        # Note: The actual endpoint might be different based on implementation
        with open(image_path, 'rb') as f:
            files = {'file': (image_path.name, f, 'image/jpeg')}

            response = requests.post(
                f"{ML_SERVICE_URL}/moderate/image",
                files=files,
                timeout=30
            )

        if response.status_code == 200:
            result = response.json()
            print_result(result, image_path.name)
            return result
        elif response.status_code == 404:
            print(f"⚠️  Image moderation endpoint not found (404)")
            print(f"   The ML service may not have image moderation enabled yet")
            return None
        else:
            print(f"❌ Error: HTTP {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return None

    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to ML service at {ML_SERVICE_URL}")
        print(f"   Make sure the service is running: uvicorn app.main:app --host 0.0.0.0 --port 8002")
        return None
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None

def print_result(result: dict, filename: str):
    """Print moderation results in a readable format"""

    if not result.get('success'):
        print(f"❌ Moderation failed")
        return

    decision = result.get('decision', 'unknown')
    risk_level = result.get('risk_level', 'unknown')

    # Decision emoji
    decision_emoji = {
        'approve': '✅',
        'review': '⚠️',
        'block': '🚫'
    }.get(decision, '❓')

    print(f"Decision: {decision_emoji} {decision.upper()}")
    print(f"Risk Level: {risk_level.upper()}")

    # Category scores
    if 'category_scores' in result:
        scores = result['category_scores']
        flagged = {k: v for k, v in scores.items() if v > 0.1}

        if flagged:
            print(f"\n📊 Category Scores (>10%):")
            for category, score in sorted(flagged.items(), key=lambda x: x[1], reverse=True):
                bar = '█' * int(score * 20)
                print(f"  {category:20s}: {score:5.1%} {bar}")
        else:
            print(f"\n✅ All categories below 10%")

    # Flags
    if result.get('flags'):
        print(f"\n🚩 Flags: {', '.join(result['flags'])}")

    # Reasons
    if result.get('reasons'):
        print(f"\n📝 Reasons:")
        for reason in result['reasons'][:3]:
            print(f"  - {reason}")

    # AI Sources
    if 'ai_sources' in result:
        print(f"\n🤖 AI Models Used:")
        for model_name, model_data in result['ai_sources'].items():
            if isinstance(model_data, dict) and 'model_name' in model_data:
                score = model_data.get('score', 0)
                print(f"  - {model_name}: {score:.1%}")

def main():
    """Run image moderation tests"""

    print("\n" + "="*80)
    print("  IMAGE MODERATION TEST - AdSphere ML Service")
    print("="*80)

    # Check if sample directory exists
    if not SAMPLE_DIR.exists():
        print(f"\n❌ Sample directory not found: {SAMPLE_DIR}")
        sys.exit(1)

    # Get all images
    images = list(SAMPLE_DIR.glob("*.jpg")) + \
             list(SAMPLE_DIR.glob("*.jpeg")) + \
             list(SAMPLE_DIR.glob("*.png")) + \
             list(SAMPLE_DIR.glob("*.webp")) + \
             list(SAMPLE_DIR.glob("*.avif"))

    if not images:
        print(f"\n❌ No images found in {SAMPLE_DIR}")
        sys.exit(1)

    print(f"\nFound {len(images)} images to test")
    print(f"Directory: {SAMPLE_DIR}\n")

    # Test each image
    results = {}
    for image_path in sorted(images):
        result = test_image_moderation(image_path)
        if result:
            results[image_path.name] = result

    # Summary
    print("\n" + "="*80)
    print("  SUMMARY")
    print("="*80 + "\n")

    if results:
        decisions = {'approve': 0, 'review': 0, 'block': 0}
        for filename, result in results.items():
            decision = result.get('decision', 'unknown')
            decisions[decision] = decisions.get(decision, 0) + 1

        total = len(results)
        print(f"Total Tested: {total}")
        print(f"✅ Approved: {decisions.get('approve', 0)}")
        print(f"⚠️  Flagged for Review: {decisions.get('review', 0)}")
        print(f"🚫 Blocked: {decisions.get('block', 0)}")

        # Most concerning images
        blocked = [(f, r) for f, r in results.items() if r.get('decision') == 'block']
        if blocked:
            print(f"\n🚫 Blocked Images:")
            for filename, result in blocked[:5]:
                flags = ', '.join(result.get('flags', [])[:3])
                print(f"  - {filename}: {flags}")
    else:
        print("⚠️  No images were successfully moderated")
        print("   Check if ML service has image moderation endpoint enabled")

    print("\n" + "="*80)
    print("  Test Complete!")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()

