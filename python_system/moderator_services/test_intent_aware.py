#!/usr/bin/env python3
"""
Intent-Aware Comprehensive Edge Case Tests
===========================================

50 test cases that require understanding context, not just keywords.
Tests the ML models' ability to understand intent and context.

Categories:
- Legitimate content with trigger words
- Actual violations disguised with innocent language
- Edge cases requiring semantic understanding
- Multi-language and cultural context
- Professional/business contexts
- News/educational content
- Scam/spam patterns
- Violence/hate speech nuances
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from moderation_service.app.services.text import moderate_text

# 50 Edge cases that test INTENT not just keywords
test_cases = [
    # ==========================================================================
    # LEGITIMATE CONTENT WITH TRIGGER WORDS (Should APPROVE)
    # ==========================================================================

    # 1. News/Educational - Weapons
    ("News article about gun control",
     "The debate over gun regulations continues as lawmakers discuss assault rifle bans.",
     "approve"),

    # 2. News/Educational - Violence
    ("Documentary about World War II",
     "The film explores the violence and tragedy of war, interviewing survivors of the conflict.",
     "approve"),

    # 3. Medical context - Drugs
    ("Pain management clinic",
     "We provide prescription medication management for chronic pain patients under doctor supervision.",
     "approve"),

    # 4. Medical context - Controlled substances
    ("Pharmacy services",
     "Licensed pharmacy offering prescription medications. All controlled substances require valid prescription.",
     "approve"),

    # 5. Fitness - Weight loss
    ("Personal trainer services",
     "I help clients lose weight through exercise and nutrition. Realistic goals over 6 months.",
     "approve"),

    # 6. Collectibles - Weapons
    ("Antique sword collection",
     "Beautiful 18th century decorative swords for display. Museum quality replicas.",
     "approve"),

    # 7. Gaming - Violence context
    ("Video game for sale",
     "Call of Duty Modern Warfare - includes all DLC. Great for shooting game fans.",
     "approve"),

    # 8. Books - Controversial topics
    ("True crime book collection",
     "Collection of books about famous murders and criminal investigations. Great for crime enthusiasts.",
     "approve"),

    # 9. Security services
    ("Home security consultation",
     "Professional assessment of your home's vulnerabilities. We identify weak points and threats.",
     "approve"),

    # 10. Pest control
    ("Pest extermination services",
     "We kill rats, mice, and insects. Fast poison-free methods available. Call for free estimate.",
     "approve"),

    # 11. Hunting supplies (legal)
    ("Hunting gear and accessories",
     "Camouflage clothing, binoculars, and hunting blinds. Licensed hunters only.",
     "approve"),

    # 12. Martial arts
    ("Karate classes for kids",
     "Learn self-defense and discipline. We teach kicks, punches, and fighting techniques safely.",
     "approve"),

    # 13. Movie props
    ("Film prop replicas",
     "Realistic replica guns and swords from famous movies. Made of plastic, for display only.",
     "approve"),

    # 14. Kitchen supplies
    ("Professional chef knives",
     "High-quality Japanese steel knives for cooking. Sharp blades for precise cutting.",
     "approve"),

    # 15. Chemistry education
    ("Chemistry tutoring",
     "Learn about chemical reactions, acids, and explosive compounds in a safe lab environment.",
     "approve"),

    # ==========================================================================
    # ACTUAL VIOLATIONS DISGUISED WITH INNOCENT LANGUAGE (Should BLOCK/REVIEW)
    # ==========================================================================

    # 16. Drug sale with medical disguise
    ("Medical supplies available",
     "Selling oxycodone and fentanyl pills. No prescription needed. Discrete shipping.",
     "block"),

    # 17. Weapons sale disguised
    ("Metal tools for sale",
     "Untraceable firearms, no serial numbers. Cash only, meet in private location.",
     "block"),

    # 18. Violence for hire
    ("Problem solving services",
     "Need someone permanently removed from your life? We handle difficult situations discreetly.",
     "block"),

    # 19. Escort services
    ("Companionship services",
     "Beautiful ladies available for private encounters. Full service, no limits. Hourly rates.",
     "block"),

    # 20. Stolen goods
    ("Electronics clearance sale",
     "Brand new iPhones, no box, no receipt. Don't ask where they came from. Cash only.",
     "block"),

    # 21. Hate group recruitment
    ("Community gathering",
     "Join our movement to take back our country from foreigners. White pride worldwide.",
     "block"),

    # 22. Drug delivery service
    ("Late night delivery",
     "We deliver party supplies to your door. Coke, molly, weed available 24/7.",
     "block"),

    # 23. Counterfeit goods
    ("Designer items wholesale",
     "Fake Gucci, Louis Vuitton, Rolex. Identical to originals, fraction of the price.",
     "block"),

    # 24. Identity fraud
    ("Document services",
     "Fake IDs, passports, driver's licenses. Scan-proof holograms. Any name you want.",
     "block"),

    # 25. Revenge services
    ("Justice delivery",
     "Your enemy hurt you? We hurt them back. Beatings, property damage, intimidation.",
     "block"),

    # ==========================================================================
    # SCAM/SPAM PATTERNS (Should REVIEW)
    # ==========================================================================

    # 26. Weight loss scam
    ("Revolutionary diet pills",
     "Lose 50 pounds in 2 weeks! No diet, no exercise! Miracle formula guaranteed!",
     "review"),

    # 27. Get rich quick
    ("Financial freedom opportunity",
     "Make $10,000 per week from home! No experience needed! Limited spots available!",
     "review"),

    # 28. Lottery scam
    ("Congratulations winner!",
     "You've won $1,000,000! Send $500 processing fee to claim your prize immediately!",
     "review"),

    # 29. Crypto scam
    ("Investment opportunity",
     "Double your Bitcoin in 24 hours! Guaranteed returns! Act now before it's too late!",
     "review"),

    # 30. Fake job offer
    ("Work from home job",
     "Earn $5000/week stuffing envelopes! No interview needed! Start today! Send $99 to begin.",
     "review"),

    # 31. Romance scam setup
    ("Looking for love",
     "Rich businessman seeking wife. Will pay for everything. Just send bank details for gifts.",
     "review"),

    # 32. Tech support scam
    ("Computer virus warning",
     "Your computer is infected! Call now to fix! We need remote access immediately!",
     "review"),

    # 33. Inheritance scam
    ("Legal notice - inheritance",
     "You are heir to $5M fortune. Contact attorney immediately. Processing fee required.",
     "review"),

    # ==========================================================================
    # EDGE CASES - PROFESSIONAL/BUSINESS CONTEXT (Should APPROVE)
    # ==========================================================================

    # 34. Legal cannabis business
    ("Licensed dispensary",
     "Legal cannabis products in authorized state. Must be 21+ with valid ID.",
     "approve"),

    # 35. Alcohol sales
    ("Wine shop grand opening",
     "Premium wines and spirits. Must be of legal drinking age. Free tasting event.",
     "approve"),

    # 36. Tobacco products
    ("Cigar lounge membership",
     "Premium cigars and tobacco products for adult enthusiasts. Members only club.",
     "approve"),

    # 37. Adult entertainment venue
    ("Nightclub hiring",
     "Upscale nightclub seeking bartenders and servers. Must be 21+. Great tips.",
     "approve"),

    # 38. Security guard services
    ("Armed security guards",
     "Licensed and bonded security personnel. Armed guards available for high-risk events.",
     "approve"),

    # 39. Demolition services
    ("Building demolition",
     "Professional demolition and explosive demolition services. Licensed and insured.",
     "approve"),

    # ==========================================================================
    # CULTURAL/RELIGIOUS CONTEXT (Should APPROVE)
    # ==========================================================================

    # 40. Religious text
    ("Bible study group",
     "Discussing passages about smiting enemies and divine wrath. All welcome.",
     "approve"),

    # 41. Historical reenactment
    ("Civil War reenactment",
     "Join our Confederate regiment for authentic battle recreations. Uniforms provided.",
     "approve"),

    # 42. Cultural festival
    ("Día de los Muertos celebration",
     "Celebrate the Day of the Dead with traditional skull decorations and death imagery.",
     "approve"),

    # ==========================================================================
    # MULTI-LANGUAGE TESTS (Should detect properly)
    # ==========================================================================

    # 43. Spanish legitimate ad
    ("Apartamento en alquiler",
     "Hermoso apartamento de 2 habitaciones en zona céntrica. Precio negociable.",
     "approve"),

    # 44. French legitimate ad
    ("Cours de cuisine",
     "Apprenez à cuisiner des plats français traditionnels. Chef professionnel.",
     "approve"),

    # 45. Swahili legitimate ad
    ("Nyumba ya kupangisha",
     "Nyumba nzuri yenye vyumba vitatu. Karibu na shule na hospitali.",
     "approve"),

    # ==========================================================================
    # ADDITIONAL EDGE CASES
    # ==========================================================================

    # 46. Legitimate massage
    ("Therapeutic massage",
     "Licensed massage therapist offering Swedish and deep tissue massage. Relaxation focus.",
     "approve"),

    # 47. Suspicious massage
    ("Special massage services",
     "Private rooms, happy endings guaranteed. Young Asian girls. Cash only.",
     "block"),

    # 48. Legitimate dating
    ("Dating profile",
     "Single professional seeking meaningful relationship. Love hiking and cooking.",
     "approve"),

    # 49. Explicit dating
    ("Looking for hookups",
     "No strings attached encounters. Send pics. Must host. Married but discreet.",
     "review"),

    # 50. Borderline clickbait
    ("You won't believe this!",
     "Amazing product that everyone is talking about! Celebrities love it! Order now!",
     "review"),
]

def run_tests(verbose=True):
    """Run all tests and return results"""
    print("="*70)
    print("  INTENT-AWARE COMPREHENSIVE EDGE CASE TESTS")
    print(f"  Total tests: {len(test_cases)}")
    print("="*70)

    results = {
        "pass": 0,
        "fail": 0,
        "details": [],
        "by_category": {
            "approve": {"expected": 0, "correct": 0},
            "block": {"expected": 0, "correct": 0},
            "review": {"expected": 0, "correct": 0},
        }
    }

    for i, (title, desc, expected) in enumerate(test_cases, 1):
        r = moderate_text(title, desc)
        decision = r['decision']
        correct = decision == expected

        results["by_category"][expected]["expected"] += 1

        if correct:
            results["pass"] += 1
            results["by_category"][expected]["correct"] += 1
            icon = "✅"
        else:
            results["fail"] += 1
            icon = "❌"

        results["details"].append({
            "test_num": i,
            "title": title,
            "expected": expected,
            "actual": decision,
            "correct": correct,
            "violations": r.get('violations', []),
            "confidence": r.get('confidence', 0)
        })

        if verbose:
            status = "PASS" if correct else "FAIL"
            print(f"\n{icon} [{i:02d}] {status}: {decision.upper():8} (expected {expected.upper()})")
            print(f"       {title[:55]}")
            if r.get('violations'):
                print(f"       Violations: {r['violations']}")
            if not correct:
                print(f"       ⚠️  MISMATCH - needs review")

    # Summary
    print("\n" + "="*70)
    print("  TEST SUMMARY")
    print("="*70)

    total = len(test_cases)
    accuracy = (results['pass'] / total) * 100

    print(f"\n  Total: {results['pass']}/{total} passed ({accuracy:.1f}%)")
    print(f"\n  By Decision Type:")
    for decision_type, stats in results["by_category"].items():
        if stats["expected"] > 0:
            type_acc = (stats["correct"] / stats["expected"]) * 100
            print(f"    {decision_type.upper():8}: {stats['correct']}/{stats['expected']} ({type_acc:.1f}%)")

    print("\n" + "="*70)

    if accuracy >= 90:
        print("  🏆 EXCELLENT! Intent-aware moderation is working very well!")
    elif accuracy >= 80:
        print("  ✅ GOOD! Intent-aware moderation is working properly.")
    elif accuracy >= 70:
        print("  ⚠️  FAIR. Some edge cases need tuning.")
    else:
        print("  ❌ NEEDS IMPROVEMENT. Review failed cases.")

    print("="*70)

    # Show failed cases
    failed = [d for d in results["details"] if not d["correct"]]
    if failed:
        print("\n  FAILED CASES:")
        for f in failed:
            print(f"    [{f['test_num']:02d}] {f['title'][:40]}")
            print(f"        Expected: {f['expected'].upper()}, Got: {f['actual'].upper()}")

    return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Intent-Aware Edge Case Tests")
    parser.add_argument("-q", "--quiet", action="store_true", help="Quiet mode - summary only")
    parser.add_argument("-f", "--failed-only", action="store_true", help="Show only failed tests")

    args = parser.parse_args()

    results = run_tests(verbose=not args.quiet)

    # Exit with error code if tests failed
    sys.exit(0 if results["fail"] == 0 else 1)

