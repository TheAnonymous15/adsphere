#!/usr/bin/env python3
"""
Test AI-Assisted Category Search
Tests the multilingual sentence transformer model for category matching
WITH CACHE SUPPORT
"""

import sys
import time
from pathlib import Path

# Add paths for imports
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "moderation_service" / "app" / "services" / "search_assisatnt"))

print("=" * 70)
print("  AI-ASSISTED SEARCH TEST (WITH CACHE)")
print("  Using: paraphrase-multilingual-MiniLM-L12-v2")
print("=" * 70)
print()

# Test 0: Cache System
print("💾 TEST 0: Cache System")
print("-" * 40)

try:
    from cache import SearchCache, get_cache

    cache = get_cache()
    print(f"✅ Cache initialized")

    # Test set/get
    test_data = [{"slug": "test", "name": "Test", "score": 0.99}]
    cache.set("test_query", test_data)
    result = cache.get("test_query")

    if result == test_data:
        print("✅ Cache set/get working")
    else:
        print("❌ Cache set/get failed")

    # Show cache tiers
    stats = cache.stats()
    print(f"   Cache tiers:")
    print(f"   - Memory: {stats['tiers']['memory']['size']} entries")
    print(f"   - Redis: {'✅ Available' if stats['tiers']['redis'].get('available') else '❌ Not available'}")
    print(f"   - SQLite: {stats['tiers']['sqlite'].get('total_entries', 0)} entries")
    print(f"   - JSON: {stats['tiers']['json'].get('total_entries', 0)} entries")

    # Clear test entry
    cache.delete("test_query")

except Exception as e:
    print(f"❌ Cache test failed: {e}")
    import traceback
    traceback.print_exc()

print()

# Test 1: Model Registry
print("📦 TEST 1: Model Registry")
print("-" * 40)

try:
    from model_registry import ModelStore

    store = ModelStore(auto_download=True, verbose=True)

    print("\n🔄 Ensuring multilingual model is available...")
    if store.ensure_models(['sentence_transformers_multilingual']):
        print("✅ Model available via registry")

        model = store.get_sentence_transformer_multilingual()
        if model:
            print(f"✅ Model loaded: {type(model).__name__}")
        else:
            print("❌ Failed to get model instance")
    else:
        print("❌ Failed to ensure model")

except Exception as e:
    print(f"❌ Model registry test failed: {e}")

print()

# Test 2: Category Matcher
print("🔍 TEST 2: Category Matcher")
print("-" * 40)

try:
    from category_matcher import CategoryMatcher, get_matcher

    print("\n🔄 Initializing CategoryMatcher...")
    matcher = CategoryMatcher()
    matcher.load_model()
    matcher.load_default_categories()

    if matcher.is_loaded:
        print(f"✅ Matcher loaded with {len(matcher.categories)} categories")
        print(f"   Model type: {'Semantic (sentence-transformers)' if matcher.model else 'Keyword fallback'}")
    else:
        print("❌ Matcher failed to load")

except Exception as e:
    print(f"❌ Category matcher test failed: {e}")
    import traceback
    traceback.print_exc()

print()

# Test 3: Search Queries (English)
print("🇬🇧 TEST 3: English Search Queries")
print("-" * 40)

test_queries_english = [
    ("hungry", ["food"]),
    ("TV", ["electronics", "entertainment"]),
    ("rent apartment", ["housing"]),
    ("car for sale", ["vehicles"]),
    ("job vacancy", ["jobs"]),
    ("gym workout", ["health", "sports"]),
    ("flight ticket", ["travel"]),
    ("laptop computer", ["electronics"]),
    ("sofa furniture", ["furniture"]),
    ("dog cat pet", ["pets"]),
]

try:
    matcher = get_matcher()

    passed = 0
    failed = 0

    for query, expected_categories in test_queries_english:
        start = time.time()
        results = matcher.match(query, top_k=3, threshold=0.2)
        elapsed = (time.time() - start) * 1000

        matched_slugs = [r['slug'] for r in results]

        # Check if any expected category is in results
        found = any(exp in matched_slugs for exp in expected_categories)

        status = "✅" if found else "❌"
        if found:
            passed += 1
        else:
            failed += 1

        print(f"  {status} \"{query}\" → {matched_slugs[:3]} ({elapsed:.1f}ms)")
        if not found:
            print(f"      Expected one of: {expected_categories}")

    print(f"\n  Results: {passed}/{passed+failed} passed")

except Exception as e:
    print(f"❌ English search test failed: {e}")
    import traceback
    traceback.print_exc()

print()

# Test 4: Multilingual Search Queries
print("🌍 TEST 4: Multilingual Search Queries")
print("-" * 40)

test_queries_multilingual = [
    # Swahili
    ("chakula", ["food"], "Swahili - food"),
    ("nyumba", ["housing"], "Swahili - house"),
    ("gari", ["vehicles"], "Swahili - car"),
    ("kazi", ["jobs"], "Swahili - work/job"),

    # Spanish
    ("comida", ["food"], "Spanish - food"),
    ("coche", ["vehicles"], "Spanish - car"),
    ("trabajo", ["jobs"], "Spanish - work"),
    ("casa", ["housing"], "Spanish - house"),

    # French
    ("nourriture", ["food"], "French - food"),
    ("voiture", ["vehicles"], "French - car"),
    ("maison", ["housing"], "French - house"),

    # German
    ("essen", ["food"], "German - food"),
    ("auto", ["vehicles"], "German - car"),
    ("haus", ["housing"], "German - house"),

    # Arabic
    ("طعام", ["food"], "Arabic - food"),
    ("سيارة", ["vehicles"], "Arabic - car"),

    # Chinese
    ("食物", ["food"], "Chinese - food"),
    ("汽车", ["vehicles"], "Chinese - car"),
    ("房子", ["housing"], "Chinese - house"),

    # Portuguese
    ("comida", ["food"], "Portuguese - food"),
    ("carro", ["vehicles"], "Portuguese - car"),
]

try:
    matcher = get_matcher()

    passed = 0
    failed = 0

    for query, expected_categories, description in test_queries_multilingual:
        start = time.time()
        results = matcher.match(query, top_k=3, threshold=0.15)  # Lower threshold for multilingual
        elapsed = (time.time() - start) * 1000

        matched_slugs = [r['slug'] for r in results]
        scores = [f"{r['slug']}:{r['score']:.2f}" for r in results[:2]]

        # Check if any expected category is in results
        found = any(exp in matched_slugs for exp in expected_categories)

        status = "✅" if found else "⚠️"
        if found:
            passed += 1
        else:
            failed += 1

        print(f"  {status} [{description}] \"{query}\" → {scores} ({elapsed:.1f}ms)")

    print(f"\n  Results: {passed}/{passed+failed} passed")
    print(f"  Note: Some languages may have lower accuracy depending on model training data")

except Exception as e:
    print(f"❌ Multilingual search test failed: {e}")
    import traceback
    traceback.print_exc()

print()

# Test 5: Performance Test
print("⚡ TEST 5: Performance Test (100 queries)")
print("-" * 40)

try:
    matcher = get_matcher()

    queries = ["food", "car", "house", "job", "phone", "clothes", "doctor", "school", "travel", "movie"] * 10

    start = time.time()
    for q in queries:
        matcher.match(q, top_k=3)
    elapsed = time.time() - start

    qps = len(queries) / elapsed
    avg_ms = (elapsed / len(queries)) * 1000

    print(f"  Total time: {elapsed:.2f}s")
    print(f"  Queries per second: {qps:.1f}")
    print(f"  Average per query: {avg_ms:.2f}ms")

    if qps > 50:
        print("  ✅ Performance: Excellent")
    elif qps > 20:
        print("  ✅ Performance: Good")
    elif qps > 5:
        print("  ⚠️ Performance: Acceptable")
    else:
        print("  ❌ Performance: Needs optimization")

except Exception as e:
    print(f"❌ Performance test failed: {e}")

print()

# Test 6: Cache Performance (with warmed cache)
print("🚀 TEST 6: Cache Performance Test")
print("-" * 40)

try:
    from category_matcher import get_matcher, reset_matcher

    # Get matcher with cache
    matcher = get_matcher(use_cache=True)

    # First run - populate cache
    queries = ["food", "car", "house", "job", "phone", "clothes", "doctor", "school", "travel", "movie"]

    print("  Phase 1: Cold cache (populating)...")
    start = time.time()
    for q in queries:
        matcher.match(q, top_k=3)
    cold_time = time.time() - start

    # Second run - should hit cache
    print("  Phase 2: Warm cache (should be faster)...")
    start = time.time()
    for _ in range(10):  # 10 iterations = 100 queries
        for q in queries:
            matcher.match(q, top_k=3)
    warm_time = time.time() - start

    cold_qps = len(queries) / cold_time
    warm_qps = (len(queries) * 10) / warm_time
    speedup = warm_qps / cold_qps if cold_qps > 0 else 0

    print(f"  Cold cache: {cold_qps:.1f} qps ({cold_time*1000/len(queries):.2f}ms/query)")
    print(f"  Warm cache: {warm_qps:.1f} qps ({warm_time*1000/(len(queries)*10):.2f}ms/query)")
    print(f"  Speedup: {speedup:.1f}x faster with cache")

    # Show cache stats
    cache_stats = matcher.get_cache_stats()
    print(f"\n  Cache Statistics:")
    print(f"    Hits: {cache_stats['matcher_cache_hits']}")
    print(f"    Misses: {cache_stats['matcher_cache_misses']}")
    print(f"    Hit rate: {cache_stats['matcher_hit_rate']:.1%}")

    if speedup > 2:
        print("\n  ✅ Cache is providing significant speedup!")
    elif speedup > 1.2:
        print("\n  ✅ Cache is providing good speedup")
    else:
        print("\n  ⚠️ Cache speedup is minimal (may need more iterations)")

except Exception as e:
    print(f"❌ Cache performance test failed: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 70)
print("  TEST COMPLETE")
print("=" * 70)

