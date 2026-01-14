#!/usr/bin/env python3
"""
Test sam images with image moderation pipeline
"""
import sys
import os

# Add path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from moderation_service.app.services.images import moderate_image

def main():
    sam_images = ['sam.jpeg', 'sam2.jpeg', 'sam3.jpeg']

    print("=" * 70)
    print("  SAM IMAGES TEST - Image Moderation Pipeline")
    print("=" * 70)

    for img in sam_images:
        image_path = f'sample_images/{img}'

        if not os.path.exists(image_path):
            print(f"\n❌ {img}: File not found")
            continue

        print(f"\n{'─' * 50}")
        print(f"📸 {img}")
        print(f"{'─' * 50}")

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

        # Violations
        if result['violations']:
            print(f"⚠️  Violations: {', '.join(result['violations'])}")

        # Detection scores
        print(f"\n📊 Detection Scores:")
        print(f"   • Weapon: {'Yes' if result['weapon_detected'] else 'No'} ({result['weapon_score']:.2f})")
        print(f"   • Violence: {'Yes' if result['violence_detected'] else 'No'} ({result['violence_score']:.2f})")
        print(f"   • NSFW: {result['nsfw_scores'].get('nudity', 0):.2f}")

        # OCR
        print(f"\n📝 Text Detection:")
        if result['has_text']:
            text = result['extracted_text']
            print(f"   Found text ({len(text)} chars):")
            # Show first 150 chars
            preview = text[:150].replace('\n', ' ')
            print(f"   \"{preview}{'...' if len(text) > 150 else ''}\"")

            # Text moderation result
            if result['text_moderation']:
                tm = result['text_moderation']
                print(f"   Text moderation: {tm.get('decision', 'N/A')}")
                if tm.get('violations'):
                    print(f"   Text violations: {tm.get('violations')}")
        else:
            print("   No text detected")

        # Explanation
        print(f"\n💬 {result['explanation']}")
        print(f"⏱️  Time: {result['processing_time_ms']:.0f}ms")

    print(f"\n{'=' * 70}")
    print("  TEST COMPLETE")
    print(f"{'=' * 70}")

if __name__ == "__main__":
    main()

