#!/usr/bin/env python3
"""
Integration test for moderation service
Tests all endpoints and core functionality
"""

import requests
import json
import time

# Configuration
BASE_URL = "http://localhost:8002"
TIMEOUT = 10

def test_health():
    """Test health endpoints"""
    print("\n=== Testing Health Endpoints ===")

    # Root endpoint
    r = requests.get(f"{BASE_URL}/", timeout=TIMEOUT)
    assert r.status_code == 200
    data = r.json()
    print(f"✓ Root: {data['service']} v{data['version']}")

    # Health check
    r = requests.get(f"{BASE_URL}/health", timeout=TIMEOUT)
    assert r.status_code == 200
    print(f"✓ Health: {r.json()['status']}")

    # Readiness check
    r = requests.get(f"{BASE_URL}/ready", timeout=TIMEOUT)
    print(f"✓ Ready: {r.status_code}")

    # Metrics
    r = requests.get(f"{BASE_URL}/metrics", timeout=TIMEOUT)
    assert r.status_code == 200
    metrics = r.json()
    print(f"✓ Metrics: {metrics['uptime_seconds']}s uptime, {metrics['cpu_percent']:.1f}% CPU")


def test_text_moderation_clean():
    """Test text moderation with clean content"""
    print("\n=== Testing Clean Content ===")

    payload = {
        "title": "Beautiful apartment for rent",
        "description": "Spacious 2-bedroom apartment in downtown area. Close to shops and transport.",
        "category": "housing",
        "language": "en"
    }

    r = requests.post(
        f"{BASE_URL}/moderate/realtime",
        json=payload,
        timeout=TIMEOUT
    )

    assert r.status_code == 200
    result = r.json()

    print(f"  Decision: {result['decision']}")
    print(f"  Risk Level: {result['risk_level']}")
    print(f"  Global Score: {result['global_score']:.3f}")
    print(f"  Processing Time: {result['processing_time']:.1f}ms")
    print(f"  Audit ID: {result['audit_id']}")

    assert result['decision'] == 'approve', "Clean content should be approved"
    print("✓ Clean content passed")


def test_text_moderation_suspicious():
    """Test text moderation with suspicious content"""
    print("\n=== Testing Suspicious Content ===")

    payload = {
        "title": "URGENT!!! Make money FAST!!!",
        "description": "Click here NOW for amazing opportunity! Limited time only! Act fast!!!",
        "category": "general",
        "language": "en"
    }

    r = requests.post(
        f"{BASE_URL}/moderate/realtime",
        json=payload,
        timeout=TIMEOUT
    )

    assert r.status_code == 200
    result = r.json()

    print(f"  Decision: {result['decision']}")
    print(f"  Risk Level: {result['risk_level']}")
    print(f"  Flags: {result['flags']}")
    print(f"  Reasons: {result['reasons'][:2]}")  # First 2 reasons

    assert result['decision'] in ['review', 'block'], "Suspicious content should be flagged"
    print("✓ Suspicious content flagged")


def test_text_moderation_violent():
    """Test text moderation with violent content"""
    print("\n=== Testing Violent Content ===")

    payload = {
        "title": "Weapons for sale",
        "description": "Selling firearms and ammunition. AR-15 available.",
        "category": "general",
        "language": "en"
    }

    r = requests.post(
        f"{BASE_URL}/moderate/realtime",
        json=payload,
        timeout=TIMEOUT
    )

    assert r.status_code == 200
    result = r.json()

    print(f"  Decision: {result['decision']}")
    print(f"  Risk Level: {result['risk_level']}")
    print(f"  Flags: {result['flags']}")
    print(f"  Category Scores:")
    for category, score in result['category_scores'].items():
        if score > 0:
            print(f"    - {category}: {score:.3f}")

    assert result['decision'] == 'block', "Violent content should be blocked"
    assert 'weapons' in result['flags'], "Should flag weapons"
    print("✓ Violent content blocked")


def test_text_moderation_toxic():
    """Test text moderation with toxic language"""
    print("\n=== Testing Toxic Language ===")

    payload = {
        "title": "Hate speech test",
        "description": "This content contains toxic language and hate speech that should be detected.",
        "category": "general",
        "language": "en"
    }

    r = requests.post(
        f"{BASE_URL}/moderate/realtime",
        json=payload,
        timeout=TIMEOUT
    )

    assert r.status_code == 200
    result = r.json()

    print(f"  Decision: {result['decision']}")
    print(f"  Risk Level: {result['risk_level']}")
    print(f"  AI Sources: {list(result.get('ai_sources', {}).keys())}")

    print("✓ Toxic language processed")


def test_simple_text_endpoint():
    """Test simple text-only endpoint"""
    print("\n=== Testing Simple Text Endpoint ===")

    r = requests.post(
        f"{BASE_URL}/moderate/text",
        params={
            "title": "Test ad",
            "description": "This is a test advertisement",
            "category": "general"
        },
        timeout=TIMEOUT
    )

    assert r.status_code == 200
    result = r.json()

    print(f"  Decision: {result['decision']}")
    print(f"  Processing Time: {result['processing_time']:.1f}ms")
    print("✓ Simple text endpoint works")


def test_api_docs():
    """Test that API documentation is accessible"""
    print("\n=== Testing API Documentation ===")

    r = requests.get(f"{BASE_URL}/docs", timeout=TIMEOUT)
    assert r.status_code == 200
    print("✓ API docs accessible at /docs")

    r = requests.get(f"{BASE_URL}/openapi.json", timeout=TIMEOUT)
    assert r.status_code == 200
    print("✓ OpenAPI schema available")


def main():
    """Run all tests"""
    print("=" * 60)
    print("AdSphere Moderation Service - Integration Tests")
    print("=" * 60)

    try:
        print(f"\nTesting service at: {BASE_URL}")

        # Wait for service to be ready
        print("Waiting for service...")
        for i in range(10):
            try:
                r = requests.get(f"{BASE_URL}/health", timeout=2)
                if r.status_code == 200:
                    break
            except:
                pass
            time.sleep(1)
        else:
            print("✗ Service not responding. Make sure it's running on port 8002")
            return False

        # Run tests
        test_health()
        test_text_moderation_clean()
        test_text_moderation_suspicious()
        test_text_moderation_violent()
        test_text_moderation_toxic()
        test_simple_text_endpoint()
        test_api_docs()

        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED")
        print("=" * 60)
        print("\nService is ready to receive data from PHP!")
        print(f"  - API Endpoint: {BASE_URL}/moderate/realtime")
        print(f"  - Documentation: {BASE_URL}/docs")

        return True

    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        return False
    except requests.exceptions.ConnectionError:
        print(f"\n✗ Cannot connect to {BASE_URL}")
        print("  Make sure the service is running:")
        print("    ./start.sh")
        return False
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)

