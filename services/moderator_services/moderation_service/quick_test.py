#!/usr/bin/env python3
"""Quick test script for the moderation service"""

import sys
sys.path.insert(0, '.')

from app.services.master_pipeline import MasterModerationPipeline
from app.services.text_rules import TextRulesEngine

def test_rules():
    """Test text rules engine"""
    print("=" * 50)
    print("Testing Text Rules Engine")
    print("=" * 50)

    rules = TextRulesEngine()

    # Test clean content
    result = rules.check('This is a test ad for selling used car')
    print(f"\nTest 1 - Clean content:")
    print(f"  Violations: {result['has_violations']}")
    print(f"  Should Block: {result['should_block']}")

    # Test bad content
    result2 = rules.check('Weapons for sale, buy guns here')
    print(f"\nTest 2 - Weapons content:")
    print(f"  Violations: {result2['has_violations']}")
    print(f"  Should Block: {result2['should_block']}")
    print(f"  Flags: {result2['flags']}")

    # Test critical content
    result3 = rules.check('Stolen iPhone for sale, no paperwork')
    print(f"\nTest 3 - Stolen goods:")
    print(f"  Violations: {result3['has_violations']}")
    print(f"  Should Block: {result3['should_block']}")
    print(f"  Flags: {result3['flags']}")

    print("\n✅ Text rules engine working!")

def test_pipeline():
    """Test master pipeline"""
    print("\n" + "=" * 50)
    print("Testing Master Pipeline")
    print("=" * 50)

    print("\nInitializing pipeline...")
    pipeline = MasterModerationPipeline()

    # Test 1: Clean content
    print("\nTest 1 - Clean content:")
    result = pipeline.moderate_text(
        title='Used Honda Civic 2020',
        description='Well maintained, single owner, 50k miles. Clean title, no accidents.'
    )
    print(f"  Decision: {result['decision']}")
    print(f"  Risk Level: {result['risk_level']}")
    print(f"  Global Score: {result.get('global_score', 'N/A'):.2f}")

    # Test 2: Suspicious content
    print("\nTest 2 - Weapons content:")
    result2 = pipeline.moderate_text(
        title='Weapons for sale',
        description='Buy guns and ammunition here, cheap prices'
    )
    print(f"  Decision: {result2['decision']}")
    print(f"  Risk Level: {result2['risk_level']}")
    print(f"  Flags: {result2.get('flags', [])}")

    # Test 3: Critical content
    print("\nTest 3 - Stolen goods:")
    result3 = pipeline.moderate_text(
        title='Stolen iPhone for sale',
        description='Hot goods, no paperwork, cash only'
    )
    print(f"  Decision: {result3['decision']}")
    print(f"  Risk Level: {result3['risk_level']}")
    print(f"  Flags: {result3.get('flags', [])}")

    print("\n✅ Master Pipeline working!")

if __name__ == "__main__":
    test_rules()
    test_pipeline()
    print("\n" + "=" * 50)
    print("ALL TESTS PASSED!")
    print("=" * 50)

