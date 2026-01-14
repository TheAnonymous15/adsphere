#!/usr/bin/env python3
"""Test legit.jpg and modified.jpeg"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from moderation_service.app.services.images import moderate_image

def test_image(img_name):
    image_path = f'sample_images/{img_name}'

    if not os.path.exists(image_path):
        print(f"\n❌ {img_name}: File not found")
        return None

    file_size = os.path.getsize(image_path) / 1024

    print(f"\n{'─' * 60}")
    print(f"📸 {img_name} ({file_size:.1f} KB)")
    print(f"{'─' * 60}")

    result = moderate_image(image_path)

    # Decision
    decision = result['decision'].upper()
    if decision == 'BLOCK':
        print(f"🚫 Decision: {decision}")
    elif decision == 'REVIEW':
        print(f"⚠️  Decision: {decision}")
    else:
        print(f"✅ Decision: {decision}")

    print(f"🎯 Confidence: {result['confidence']:.1%}")

    if result['violations']:
        print(f"⚠️  Violations: {', '.join(result['violations'])}")

    print(f"\n📊 Scores:")
    print(f"   Weapon: {result['weapon_score']:.2f}, Violence: {result['violence_score']:.2f}")

    if result['has_text']:
        text = result['extracted_text']
        print(f"\n📝 Text ({len(text)} chars): \"{text[:100]}...\"")
        if result['text_moderation']:
            print(f"   Text decision: {result['text_moderation'].get('decision')}")

    print(f"\n💬 {result['explanation']}")
    print(f"⏱️  {result['processing_time_ms']:.0f}ms")

    return result

if __name__ == "__main__":
    print("=" * 70)
    print("  TESTING: legit.jpg vs modified.jpeg")
    print("=" * 70)

    test_image('legit.jpg')
    test_image('modified.jpeg')

    print(f"\n{'=' * 70}")
    print("  COMPLETE")
    print(f"{'=' * 70}")

