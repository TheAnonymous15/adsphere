#!/usr/bin/env python3
"""
Text Moderation Test Script
===========================

Quick test script to verify text moderation pipeline functionality.

Usage:
    python test_text_moderation.py                    # Run default tests
    python test_text_moderation.py "Custom text"     # Test custom text
    python test_text_moderation.py --interactive     # Interactive mode
"""

import sys
from pathlib import Path

# Add paths
BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / 'moderation_service'))

from model_registry import ensure_models

# Ensure required models
print("Checking required models...")
REQUIRED_MODELS = ['detoxify', 'transformers', 'torch']
if not ensure_models(REQUIRED_MODELS, verbose=False):
    print("⚠ Some models not available")

from moderation_service.app.services.text.text_moderation_pipeline import (
    TextModerationPipeline,
    TextModerationInput,
    moderate_text
)


def print_result(title: str, description: str, result: dict):
    """Print formatted result"""
    decision = result['decision'].upper()
    confidence = result['confidence'] * 100

    # Color coding
    if decision == 'APPROVE':
        icon = '✅'
    elif decision == 'REVIEW':
        icon = '⚠️'
    else:
        icon = '🚫'

    print(f"\n{'='*70}")
    print(f"📝 Title: {title[:50]}")
    print(f"📄 Description: {description[:100]}...")
    print(f"{'='*70}")
    print(f"\n{icon} Decision: {decision}")
    print(f"🎯 Confidence: {confidence:.1f}%")
    print(f"🌐 Language: {result.get('detected_language', 'unknown')}")

    if result.get('violations'):
        print(f"⚠️ Violations: {', '.join(result['violations'])}")

    if result.get('toxicity_scores'):
        high_tox = {k: f"{v:.2f}" for k, v in result['toxicity_scores'].items() if v > 0.3}
        if high_tox:
            print(f"☢️ Toxicity: {high_tox}")

    print(f"\n💬 {result['explanation']}")
    print(f"⏱️ Processing time: {result['processing_time_ms']:.1f}ms")


def run_default_tests():
    """Run default test cases"""
    print("\n" + "="*70)
    print("  TEXT MODERATION PIPELINE - TEST SUITE")
    print("="*70)

    test_cases = [
        {
            "title": "iPhone 14 Pro Max for Sale",
            "description": "Excellent condition, 256GB, comes with original box and charger. Screen protector included.",
            "expected": "approve"
        },
        {
            "title": "URGENT: Get Rich Quick!!!",
            "description": "Make $10,000 per day working from home! Wire transfer required. Limited time offer! Act now!",
            "expected": "review"
        },
        {
            "title": "Weapons for sale",
            "description": "AR-15 rifles and ammunition. Contact for prices. Cash only. No questions asked.",
            "expected": "block"
        },
        {
            "title": "Professional Tutoring Services",
            "description": "Math and science tutoring for high school students. Experienced teacher, $30/hour.",
            "expected": "approve"
        },
        {
            "title": "I hate you all",
            "description": "You are stupid worthless garbage. Die you pathetic losers. I will find you.",
            "expected": "block"
        },
        {
            "title": "Bienes raíces en venta",
            "description": "Casa hermosa de 3 habitaciones en zona residencial. Precio negociable.",
            "expected": "approve"
        },
        {
            "title": "Buy drugs online",
            "description": "Cocaine, meth, pills available. Discrete shipping. Bitcoin accepted.",
            "expected": "block"
        },
        {
            "title": "Vintage Car Parts",
            "description": "Original parts for 1965 Mustang. Carburetor, distributor, chrome trim.",
            "expected": "approve"
        }
    ]

    results = {"pass": 0, "fail": 0}

    for i, test in enumerate(test_cases, 1):
        print(f"\n{'─'*70}")
        print(f"TEST {i}/{len(test_cases)}: {test['title'][:40]}")
        print(f"Expected: {test['expected'].upper()}")
        print(f"{'─'*70}")

        result = moderate_text(test['title'], test['description'])

        decision = result['decision']
        expected = test['expected']
        passed = decision == expected

        if passed:
            results["pass"] += 1
            status = "✅ PASS"
        else:
            results["fail"] += 1
            status = "❌ FAIL"

        print(f"\nResult: {decision.upper()} | {status}")
        print(f"Confidence: {result['confidence']*100:.1f}%")

        if result.get('violations'):
            print(f"Violations: {', '.join(result['violations'])}")

        print(f"Explanation: {result['explanation'][:100]}...")

    # Summary
    print(f"\n{'='*70}")
    print(f"  TEST SUMMARY")
    print(f"{'='*70}")
    print(f"  Passed: {results['pass']}/{len(test_cases)}")
    print(f"  Failed: {results['fail']}/{len(test_cases)}")
    print(f"  Accuracy: {results['pass']/len(test_cases)*100:.1f}%")
    print(f"{'='*70}\n")

    return results['fail'] == 0


def test_single(text: str):
    """Test single text input"""
    print("\n" + "="*70)
    print("  SINGLE TEXT TEST")
    print("="*70)

    # Assume text is both title and description
    if len(text) < 50:
        title = text
        description = text
    else:
        title = text[:50]
        description = text

    result = moderate_text(title, description)
    print_result(title, description, result)


def interactive_mode():
    """Interactive testing mode"""
    print("\n" + "="*70)
    print("  INTERACTIVE TEXT MODERATION")
    print("  Type 'quit' to exit")
    print("="*70)

    while True:
        print("\n")
        title = input("📝 Enter title (or 'quit'): ").strip()

        if title.lower() == 'quit':
            print("Goodbye!")
            break

        description = input("📄 Enter description: ").strip()

        if not title and not description:
            print("⚠ Please enter some text")
            continue

        result = moderate_text(title or "Untitled", description or title)
        print_result(title, description, result)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Text Moderation Test Script")
    parser.add_argument("text", nargs="?", help="Text to moderate")
    parser.add_argument("--interactive", "-i", action="store_true", help="Interactive mode")

    args = parser.parse_args()

    if args.interactive:
        interactive_mode()
    elif args.text:
        test_single(args.text)
    else:
        success = run_default_tests()
        sys.exit(0 if success else 1)

