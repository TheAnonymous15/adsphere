#!/usr/bin/env python3
"""Quick edge case tests for text moderation"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from moderation_service.app.services.text.text_moderation_pipeline import moderate_text

tests = [
    ("Nairobi apartment for rent", "Spacious 2 bedroom apartment in Westlands. 50k per month."),
    ("Kazi ya muda mfupi", "Tunatafuta wafanyakazi wa kusaidia sokoni. Mshahara mzuri."),
    ("FREE MONEY!!!", "Send $100 to this account and receive $10000 back. Wire transfer only!"),
    ("Selling my old laptop", "MacBook Pro 2019, works great. $500"),
    ("Kill all enemies", "Destroy them and make them suffer"),
    ("Beautiful handmade jewelry", "Sterling silver necklaces and bracelets. Custom orders welcome."),
]

print("\nEDGE CASE TESTS")
print("=" * 70)

for title, desc in tests:
    r = moderate_text(title, desc)
    decision = r['decision'].upper()
    if decision == 'APPROVE':
        icon = '✅'
    elif decision == 'REVIEW':
        icon = '⚠️'
    else:
        icon = '🚫'

    print(f"\n{icon} {decision:8} | {title}")
    if r.get('violations'):
        print(f"   Violations: {r['violations']}")
    print(f"   Confidence: {r['confidence']*100:.0f}%")

print("\n" + "=" * 70)

