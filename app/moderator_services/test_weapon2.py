#!/usr/bin/env python3
"""
Bulk test: send every image found in sample_images/ to weapon moderation service
"""
import sys
import requests
from pathlib import Path

# Add path for model_registry
sys.path.insert(0, str(Path(__file__).parent))
from model_registry import ensure_models

# Ensure models are available
REQUIRED_MODELS = ['yolov8n', 'transformers', 'torch']
ensure_models(REQUIRED_MODELS, verbose=False)

print("=" * 90)
print("   WEAPON MODERATION TEST - BULK IMAGE SCAN")
print("=" * 90)
print()

ML_URL = "http://localhost:8002/moderate/image"
SAMPLE_DIR = Path(__file__).parent / "sample_images"

# extensions you want to test
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}

results = []

# walk through directory
for img in sorted(SAMPLE_DIR.iterdir()):

    if not img.suffix.lower() in IMAGE_EXTS:
        continue

    print("=" * 90)
    print(f"  {img.name}")
    print("=" * 90)

    size_kb = img.stat().st_size / 1024
    print(f"  Size: {size_kb:.1f} KB\n")

    try:
        with img.open("rb") as f:
            resp = requests.post(
                ML_URL,
                files={'file': (img.name, f, 'image/jpeg')},
                timeout=60
            )

        if resp.status_code != 200:
            print(f"  ❌ HTTP {resp.status_code}\n")
            results.append((img.name, "ERROR", "-"))
            continue

        data = resp.json()

        decision = data.get("decision", "unknown")
        risk = data.get("risk_level", "unknown")
        scores = data.get("category_scores", {})

        weapon = scores.get("weapons", 0)
        blood = scores.get("blood", 0)
        violence = scores.get("violence", 0)

        print(f"  ✔ Decision: {decision.upper()}   (risk: {risk})")
        print(f"  Weapon:   {weapon*100:6.2f}%")
        print(f"  Blood:    {blood*100:6.2f}%")
        print(f"  Violence: {violence*100:6.2f}%")
        print()

        results.append(
            (img.name, decision, f"{weapon:.2f}/{blood:.2f}/{violence:.2f}")
        )

    except Exception as exc:
        print(f"  ❌ Exception: {exc}\n")
        results.append((img.name, "ERROR", "-"))


print("\n")
print("=" * 90)
print("   SUMMARY")
print("=" * 90)

print(f"{'Image':<30} {'Decision':<12} Scores")
print("-" * 90)

for filename, decision, score in results:
    print(f"{filename:<30} {decision:<12} {score}")

print("\nDone.\n")
