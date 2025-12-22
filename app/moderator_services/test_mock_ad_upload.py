#!/usr/bin/env python3
"""
Mock Ad Upload Test - Python Version
=====================================

Tests the full text moderation pipeline with sample ad data,
simulating what the PHP upload system would send.

This tests the same scenarios as test_mock_upload.php
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# Add paths
BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / 'moderation_service'))

print("=" * 70)
print("  MOCK AD UPLOAD TEST")
print("  Testing Text Moderation Pipeline")
print("=" * 70)
print()

# Import the text moderation pipeline
from model_registry import ensure_models

print("Checking required models...")
REQUIRED_MODELS = ['detoxify', 'transformers', 'torch']
if not ensure_models(REQUIRED_MODELS, verbose=False):
    print("⚠ Some models not available")

from moderation_service.app.services.text import (
    TextModerationPipeline,
    moderate_text,
    ModerationDecision
)

print("\nInitializing Text Moderation Pipeline...")
pipeline = TextModerationPipeline()

# Test cases matching test_mock_upload.php
test_ads = [
    {
        "name": "Clean Product Ad",
        "title": "Brand New iPhone 15 Pro",
        "description": "Excellent condition, 128GB Space Gray, comes with original box and charger. Never used, still sealed. Great deal!",
        "expected": "approve"
    },
    {
        "name": "Spam Ad",
        "title": "URGENT!!! AMAZING DEAL!!!",
        "description": "CLICK HERE NOW!!! Limited time only!!! Act fast!!! Don't miss out!!! BUY NOW!!!",
        "expected": "review"
    },
    {
        "name": "Weapons Ad",
        "title": "Firearms for sale",
        "description": "Selling AR-15 rifle with ammunition. Also have pistols and knives available. Contact for details.",
        "expected": "block"
    },
    {
        "name": "Drugs Ad",
        "title": "Party supplies available",
        "description": "Cocaine, heroin, and meth for sale. Fast delivery, no questions asked. Cash only.",
        "expected": "block"
    },
    {
        "name": "Hate Speech Ad",
        "title": "Special group gathering",
        "description": "We hate all foreigners and will destroy them. Join our racist movement today!",
        "expected": "block"
    },
    {
        "name": "Stolen Goods Ad",
        "title": "Cheap electronics",
        "description": "Selling stolen iPhones and laptops. No receipts, no questions asked. Very cheap prices.",
        "expected": "block"
    },
    {
        "name": "Borderline Ad",
        "title": "Amazing weight loss product",
        "description": "Lose 30 pounds in 7 days! Guaranteed results! Miracle formula! No exercise needed!",
        "expected": "review"
    },
    {
        "name": "Housing Ad",
        "title": "Beautiful 2-bedroom apartment",
        "description": "Spacious apartment in downtown area, near shops and public transport. Rent $1200/month.",
        "expected": "approve"
    },
    {
        "name": "Violence Ad",
        "title": "Seeking revenge",
        "description": "Looking to hire someone to hurt my enemy. Will pay good money for violence and assault.",
        "expected": "block"
    },
    {
        "name": "Adult Services Ad",
        "title": "Escort services available",
        "description": "Beautiful girls for hire, sexual services, no condom option available. Call now.",
        "expected": "block"
    }
]

print(f"\nRunning {len(test_ads)} moderation tests...\n")
print("=" * 70)

results = {
    "total": len(test_ads),
    "approved": 0,
    "blocked": 0,
    "reviewed": 0,
    "correct": 0
}

for i, test in enumerate(test_ads, 1):
    print(f"\nTEST {i}: {test['name']}")
    print("-" * 70)
    print(f"Title: {test['title']}")
    print(f"Description: {test['description'][:60]}...")
    print(f"Expected: {test['expected'].upper()}")
    print()

    # Run moderation
    result = moderate_text(test['title'], test['description'])

    decision = result['decision']
    confidence = result['confidence'] * 100

    # Track results
    if decision == 'approve':
        results['approved'] += 1
    elif decision == 'block':
        results['blocked'] += 1
    else:
        results['reviewed'] += 1

    # Check correctness
    correct = decision == test['expected']
    if correct:
        results['correct'] += 1

    # Display
    if decision == 'approve':
        icon = '✅'
    elif decision == 'review':
        icon = '⚠️'
    else:
        icon = '🚫'

    status = "✓ CORRECT" if correct else f"✗ WRONG (expected {test['expected'].upper()})"

    print(f"RESULT: {icon} {decision.upper()}")
    print(f"Status: {status}")
    print(f"Confidence: {confidence:.1f}%")
    print(f"Language: {result.get('detected_language', 'en')}")

    if result.get('violations'):
        print(f"Violations: {', '.join(result['violations'])}")

    if result.get('toxicity_scores'):
        high_tox = {k: f"{v:.2f}" for k, v in result['toxicity_scores'].items() if v > 0.3}
        if high_tox:
            print(f"Toxicity: {high_tox}")

    print(f"Explanation: {result['explanation'][:70]}...")
    print(f"Processing: {result['processing_time_ms']:.1f}ms")

print("\n" + "=" * 70)
print("  TEST SUMMARY")
print("=" * 70)

accuracy = (results['correct'] / results['total']) * 100

print(f"""
Total Tests: {results['total']}
Approved: {results['approved']}
Blocked: {results['blocked']}
Flagged for Review: {results['reviewed']}

Correct Predictions: {results['correct']}/{results['total']}
Accuracy: {accuracy:.1f}%
""")

if accuracy >= 90:
    print("🏆 EXCELLENT! Moderation system is working very well!")
elif accuracy >= 70:
    print("✅ GOOD! Moderation system is working properly.")
elif accuracy >= 50:
    print("⚠️  FAIR. Moderation system needs tuning.")
else:
    print("❌ POOR. Moderation system needs significant improvement.")

print("\n" + "=" * 70)
print("  PROTECTION LEVELS")
print("=" * 70)

# Analyze specific categories
weapons_blocked = any(
    't' in test['name'].lower() and 'weapon' in test['name'].lower()
    for test in test_ads
)

print(f"""
Safe Content:   {'✅ Approved correctly' if results['approved'] > 0 else '❌ Issues'}
Spam Content:   {'✅ Flagged for review' if results['reviewed'] > 0 else '⚠️ Check spam detection'}
Harmful Content: {'✅ Blocked' if results['blocked'] >= 5 else '⚠️ Check blocking'}
""")

# Export results as JSON for PHP consumption
export_data = {
    "timestamp": datetime.now().isoformat(),
    "results": results,
    "accuracy": accuracy,
    "tests": []
}

for i, test in enumerate(test_ads):
    r = moderate_text(test['title'], test['description'])
    export_data["tests"].append({
        "name": test["name"],
        "title": test["title"],
        "expected": test["expected"],
        "actual": r["decision"],
        "correct": r["decision"] == test["expected"],
        "confidence": r["confidence"],
        "violations": r.get("violations", []),
        "processing_time_ms": r["processing_time_ms"]
    })

# Save results
results_file = BASE_DIR / "mock_upload_results.json"
with open(results_file, "w") as f:
    json.dump(export_data, f, indent=2)

print(f"\n📄 Results saved to: {results_file}")
print("\n✅ Mock upload test complete!")

